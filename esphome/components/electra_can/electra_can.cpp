#ifdef USE_ESP32

#include "electra_can.h"

#include "esphome/core/log.h"

#include <driver/gpio.h>
#include <esp_err.h>

#include <algorithm>
#include <cstring>

// TWAI_GENERAL_CONFIG_DEFAULT() references CAN_IO_UNUSED, which some framework
// versions define as a bare (-1) that will not convert to gpio_num_t.
#undef CAN_IO_UNUSED
#define CAN_IO_UNUSED ((gpio_num_t) -1)

namespace esphome::electra_can {

static const char *const TAG = "electra_can";

// A dominant run longer than any legal frame field means the line is being held,
// which on the Electra bus is an analog audio session rather than data.
static const uint32_t AUDIO_SESSION_MIN_MS = 100;

void ElectraCan::set_timing(uint32_t brp, uint8_t tseg1, uint8_t tseg2, uint8_t sjw, bool triple_sampling) {
  // Zero-initialise so quanta_resolution_hz stays 0; a non-zero value there makes
  // the driver derive its own prescaler and ignore brp.
  this->timing_ = twai_timing_config_t{};
  this->timing_.brp = brp;
  this->timing_.tseg_1 = tseg1;
  this->timing_.tseg_2 = tseg2;
  this->timing_.sjw = sjw;
  this->timing_.triple_sampling = triple_sampling;
}

bool ElectraCan::setup_internal() {
  if (!this->install_(TWAI_MODE_LISTEN_ONLY))
    return false;
  ESP_LOGI(TAG, "listening at %" PRIu32 " bps, listen-only until a frame is queued", this->nominal_bit_rate_);
  return true;
}

bool ElectraCan::install_(twai_mode_t mode) {
  twai_general_config_t g_config = TWAI_GENERAL_CONFIG_DEFAULT((gpio_num_t) this->tx_, (gpio_num_t) this->rx_, mode);
  g_config.rx_queue_len = this->rx_queue_len_;
  g_config.tx_queue_len = MAX_TX_QUEUE;

  twai_filter_config_t f_config = TWAI_FILTER_CONFIG_ACCEPT_ALL();

  esp_err_t err = twai_driver_install(&g_config, &this->timing_, &f_config);
  if (err != ESP_OK) {
    ESP_LOGE(TAG, "twai_driver_install failed: %s", esp_err_to_name(err));
    return false;
  }
  err = twai_start();
  if (err != ESP_OK) {
    ESP_LOGE(TAG, "twai_start failed: %s", esp_err_to_name(err));
    twai_driver_uninstall();
    return false;
  }
  this->installed_ = true;
  this->mode_ = mode;
  return true;
}

void ElectraCan::uninstall_() {
  if (!this->installed_)
    return;
  // twai_stop() also aborts anything still pending in the transmit queue.
  twai_stop();
  twai_driver_uninstall();
  this->installed_ = false;
}

bool ElectraCan::restore_listen_only_() {
  this->uninstall_();
  if (this->install_(TWAI_MODE_LISTEN_ONLY))
    return true;
  ESP_LOGE(TAG, "could not return to listen-only mode, bus interface is down");
  this->mark_failed();
  return false;
}

bool ElectraCan::enter_normal_mode_() {
  this->uninstall_();
  if (this->install_(TWAI_MODE_NORMAL))
    return true;
  ESP_LOGW(TAG, "could not enter normal mode, dropping %u queued frame(s)",
           static_cast<unsigned>(this->tx_queue_.size()));
  this->tx_failure_count_ += this->tx_queue_.size();
  this->tx_queue_.clear();
  this->tx_state_ = TX_IDLE;
  this->restore_listen_only_();
  return false;
}

void ElectraCan::sample_line_() {
  // The GPIO input register still reflects the pad level while the pin is routed
  // to the TWAI peripheral, so this reads the raw bus state.
  const bool recessive = gpio_get_level((gpio_num_t) this->rx_) != 0;
  if (recessive) {
    if (!this->line_recessive_) {
      this->line_recessive_ = true;
      this->recessive_since_ = millis();
    }
  } else {
    if (this->line_recessive_) {
      this->line_recessive_ = false;
      this->dominant_since_ = millis();
    }
  }
}

bool ElectraCan::bus_is_idle() const {
  return this->line_recessive_ && (millis() - this->recessive_since_) >= this->idle_required_ms_;
}

bool ElectraCan::audio_session_active() const {
  return !this->line_recessive_ && (millis() - this->dominant_since_) >= AUDIO_SESSION_MIN_MS;
}

void ElectraCan::loop() {
  this->sample_line_();
  canbus::Canbus::loop();  // drains the receive queue and fires on_frame triggers
  this->service_tx_();
}

canbus::Error ElectraCan::send_message(canbus::CanFrame *frame) {
  if (this->is_failed())
    return canbus::ERROR_FAIL;
  if (frame->can_data_length_code > canbus::CAN_MAX_DATA_LENGTH)
    return canbus::ERROR_FAILTX;
  if (this->tx_queue_.size() >= MAX_TX_QUEUE) {
    ESP_LOGW(TAG, "transmit queue full, dropping frame 0x%03" PRIx32, frame->can_id);
    this->tx_failure_count_++;
    return canbus::ERROR_ALLTXBUSY;
  }
  // Queued rather than sent: transmitting needs a mode swap and a quiet line.
  this->tx_queue_.push_back(*frame);
  return canbus::ERROR_OK;
}

canbus::Error ElectraCan::read_message(canbus::CanFrame *frame) {
  if (!this->installed_)
    return canbus::ERROR_FAIL;

  twai_message_t message;
  if (twai_receive(&message, 0) != ESP_OK)
    return canbus::ERROR_NOMSG;

  // A frame just occupied the line, so the quiet window has to start over even if
  // the level happened to read recessive between polls.
  this->line_recessive_ = false;
  this->dominant_since_ = millis();
  this->rx_count_++;

  frame->can_id = message.identifier;
  frame->use_extended_id = (message.flags & TWAI_MSG_FLAG_EXTD) != 0;
  frame->remote_transmission_request = (message.flags & TWAI_MSG_FLAG_RTR) != 0;
  frame->can_data_length_code = message.data_length_code;

  if (!frame->remote_transmission_request) {
    const size_t dlc = std::min<size_t>(message.data_length_code, canbus::CAN_MAX_DATA_LENGTH);
    memcpy(frame->data, message.data, dlc);
  }
  return canbus::ERROR_OK;
}

void ElectraCan::service_tx_() {
  const uint32_t now = millis();

  switch (this->tx_state_) {
    case TX_IDLE:
      if (this->tx_queue_.empty() || this->is_failed())
        return;
      this->tx_state_ = TX_WAIT_QUIET;
      this->tx_state_since_ = now;
      return;

    case TX_WAIT_QUIET: {
      if (now - this->tx_state_since_ >= this->tx_window_timeout_ms_) {
        ESP_LOGW(TAG, "line never went quiet within %" PRIu32 " ms, dropping %u queued frame(s)",
                 this->tx_window_timeout_ms_, static_cast<unsigned>(this->tx_queue_.size()));
        this->tx_failure_count_ += this->tx_queue_.size();
        this->tx_queue_.clear();
        this->tx_state_ = TX_IDLE;
        return;
      }
      if (!this->bus_is_idle())
        return;

      if (!this->enter_normal_mode_())
        return;

      while (!this->tx_queue_.empty()) {
        const canbus::CanFrame &frame = this->tx_queue_.front();
        twai_message_t message{};
        message.identifier = frame.can_id;
        message.data_length_code = frame.can_data_length_code;
        if (frame.use_extended_id)
          message.flags |= TWAI_MSG_FLAG_EXTD;
        if (frame.remote_transmission_request) {
          message.flags |= TWAI_MSG_FLAG_RTR;
        } else {
          memcpy(message.data, frame.data, frame.can_data_length_code);
        }

        const esp_err_t err = twai_transmit(&message, 0);
        if (err == ESP_OK) {
          this->tx_count_++;
          ESP_LOGD(TAG, "queued 0x%03" PRIx32 " for transmission", frame.can_id);
        } else {
          this->tx_failure_count_++;
          ESP_LOGW(TAG, "twai_transmit failed: %s", esp_err_to_name(err));
        }
        this->tx_queue_.pop_front();
      }
      this->tx_state_ = TX_SENDING;
      this->tx_state_since_ = now;
      return;
    }

    case TX_SENDING: {
      twai_status_info_t status{};
      const bool drained = twai_get_status_info(&status) == ESP_OK && status.msgs_to_tx == 0;
      if (!drained && (now - this->tx_state_since_) < this->tx_window_timeout_ms_)
        return;
      if (!drained) {
        // Nothing acknowledged us, so the controller is still retrying. Dropping
        // back to listen-only aborts it, which is the safe outcome.
        ESP_LOGW(TAG, "transmission unacknowledged after %" PRIu32 " ms, aborting", this->tx_window_timeout_ms_);
        this->tx_failure_count_++;
      }
      this->restore_listen_only_();
      this->tx_state_ = TX_IDLE;
      return;
    }
  }
}

uint32_t ElectraCan::get_bus_error_count() const {
  twai_status_info_t status{};
  if (!this->installed_ || twai_get_status_info(&status) != ESP_OK)
    return 0;
  return status.bus_error_count;
}

void ElectraCan::dump_config() {
  ESP_LOGCONFIG(TAG, "Electra single-wire CAN:");
  ESP_LOGCONFIG(TAG, "  RX pin: GPIO%u", this->rx_);
  ESP_LOGCONFIG(TAG, "  TX pin: GPIO%u", this->tx_);
  ESP_LOGCONFIG(TAG, "  Bit rate: %" PRIu32 " bps", this->nominal_bit_rate_);
  ESP_LOGCONFIG(TAG, "  Timing: brp=%" PRIu32 " tseg1=%u tseg2=%u sjw=%u triple_sampling=%s", this->timing_.brp,
                this->timing_.tseg_1, this->timing_.tseg_2, this->timing_.sjw,
                YESNO(this->timing_.triple_sampling));
  ESP_LOGCONFIG(TAG, "  Quiet time required before transmitting: %" PRIu32 " ms", this->idle_required_ms_);
  ESP_LOGCONFIG(TAG, "  Transmit window timeout: %" PRIu32 " ms", this->tx_window_timeout_ms_);
  canbus::Canbus::dump_config();
  if (this->is_failed())
    ESP_LOGE(TAG, "  Setup failed");
}

}  // namespace esphome::electra_can

#endif  // USE_ESP32
