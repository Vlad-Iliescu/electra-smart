#ifdef USE_ESP32

#include "electra_can.h"

#include "esphome/core/log.h"

#include <driver/gpio.h>
#include <esp_err.h>
#include <esp_rom_sys.h>
#include <esp_timer.h>

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
  // Park the assist pin high-Z before anything else. It is wired to a shared bus
  // through a resistor low enough to disturb it, so the pin must never be an
  // output except during the few milliseconds a frame is going out.
  this->tx_pullup_(false);
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
  if (this->tx_no_ack_)
    ESP_LOGW(TAG, "transmitting in no-ack mode: the acknowledge slot is ignored (diagnostic)");
  if (this->install_(this->tx_no_ack_ ? TWAI_MODE_NO_ACK : TWAI_MODE_NORMAL))
    return true;
  ESP_LOGW(TAG, "could not enter normal mode, dropping %u queued frame(s)",
           static_cast<unsigned>(this->tx_queue_.size()));
  this->tx_failure_count_ += this->tx_queue_.size();
  this->tx_queue_.clear();
  this->tx_state_ = TX_IDLE;
  this->restore_listen_only_();
  return false;
}

void ElectraCan::tx_pullup_(bool on) {
  if (this->pullup_ < 0)
    return;
  const gpio_num_t pin = (gpio_num_t) this->pullup_;

  if (on) {
    // Set the level before the direction, so becoming an output cannot flick the
    // line dominant for a cycle.
    gpio_set_level(pin, 1);
    gpio_set_direction(pin, GPIO_MODE_OUTPUT);
    return;
  }

  gpio_config_t cfg{};
  cfg.pin_bit_mask = 1ULL << (uint32_t) this->pullup_;
  cfg.mode = GPIO_MODE_INPUT;
  // Not gpio_reset_pin(), which enables the internal pull-up: that would leave
  // ~45 k to 3V3 sitting on the bus for good, too weak to help and not nothing.
  cfg.pull_up_en = GPIO_PULLUP_DISABLE;
  cfg.pull_down_en = GPIO_PULLDOWN_DISABLE;
  cfg.intr_type = GPIO_INTR_DISABLE;
  gpio_config(&cfg);
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

      // The line has been recessive for the whole quiet window, so asserting the
      // assist here holds it where it already is - it only starts mattering once
      // the controller begins pulling bits dominant.
      this->tx_pullup_(true);

      if (!this->enter_normal_mode_()) {
        this->tx_pullup_(false);
        return;
      }

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
        // Self-test mode only waives the acknowledge for frames issued as a self
        // reception request, so the flag has to travel with the message rather
        // than being implied by the controller mode. The frame still goes out on
        // the wire; we just also receive a copy of it.
        if (this->tx_no_ack_)
          message.flags |= TWAI_MSG_FLAG_SELF;

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
      this->log_tx_status_("tx begin");
      this->probe_tx_errors_(300000);
      this->tx_state_ = TX_SENDING;
      this->tx_state_since_ = millis();
      this->tx_last_probe_ = this->tx_state_since_;
      return;
    }

    case TX_SENDING: {
      twai_status_info_t status{};
      const bool drained = twai_get_status_info(&status) == ESP_OK && status.msgs_to_tx == 0;
      if (!drained && (now - this->tx_state_since_) < this->tx_window_timeout_ms_) {
        if (now - this->tx_last_probe_ >= 500) {
          this->tx_last_probe_ = now;
          this->log_tx_status_("tx pending");
        }
        return;
      }
      if (!drained) {
        // The controller never emptied its queue. Why is in the counters, not
        // here. Dropping back to listen-only aborts the attempt, which is the
        // safe outcome either way.
        this->log_tx_status_("tx aborted");
        ESP_LOGW(TAG, "frame not sent within %" PRIu32 " ms, aborting", this->tx_window_timeout_ms_);
        this->tx_failure_count_++;
      } else {
        this->log_tx_status_("tx done");
      }
      // Listen-only first: that stops the controller driving, so the assist stays
      // up for as long as we could still be putting bits on the line.
      this->restore_listen_only_();
      this->tx_pullup_(false);
      this->tx_state_ = TX_IDLE;
      return;
    }
  }
}

void ElectraCan::probe_tx_errors_(uint32_t window_us) {
  static constexpr size_t MAX_MARKS = 12;
  // One bit at the bus rate, used to express the gaps in something meaningful.
  const uint32_t bit_us = this->nominal_bit_rate_ == 0 ? 88 : 1000000UL / this->nominal_bit_rate_;

  int64_t at[MAX_MARKS];
  uint32_t count[MAX_MARKS];
  size_t n = 0;

  twai_status_info_t s{};
  uint32_t last = 0;
  if (twai_get_status_info(&s) == ESP_OK)
    last = s.bus_error_count;

  const int64_t start = esp_timer_get_time();
  while (n < MAX_MARKS && (esp_timer_get_time() - start) < (int64_t) window_us) {
    if (twai_get_status_info(&s) != ESP_OK)
      break;
    if (s.bus_error_count != last) {
      at[n] = esp_timer_get_time() - start;
      count[n] = s.bus_error_count;
      last = s.bus_error_count;
      n++;
    }
    if (s.msgs_to_tx == 0)
      break;
  }

  if (n == 0) {
    ESP_LOGW(TAG, "tx probe: no errors in the first %" PRIu32 " us", window_us);
    return;
  }
  for (size_t i = 0; i < n; i++) {
    const int64_t gap = i == 0 ? at[0] : at[i] - at[i - 1];
    ESP_LOGW(TAG, "tx probe: bus_err=%" PRIu32 " at %lld us, %lld us since previous (%lld bit times)", count[i],
             (long long) at[i], (long long) gap, (long long) (gap / bit_us));
  }
}

void ElectraCan::log_tx_status_(const char *phase) {
  twai_status_info_t s{};
  if (twai_get_status_info(&s) != ESP_OK) {
    ESP_LOGW(TAG, "%s: controller status unavailable", phase);
    return;
  }
  const char *state = "?";
  switch (s.state) {
    case TWAI_STATE_STOPPED:
      state = "stopped";
      break;
    case TWAI_STATE_RUNNING:
      state = "running";
      break;
    case TWAI_STATE_BUS_OFF:
      state = "bus-off";
      break;
    case TWAI_STATE_RECOVERING:
      state = "recovering";
      break;
  }
  ESP_LOGW(TAG,
           "%s: state=%s tx_queued=%" PRIu32 " tec=%" PRIu32 " rec=%" PRIu32 " tx_failed=%" PRIu32
           " arb_lost=%" PRIu32 " bus_err=%" PRIu32,
           phase, state, s.msgs_to_tx, s.tx_error_counter, s.rx_error_counter, s.tx_failed_count, s.arb_lost_count,
           s.bus_error_count);
}

uint32_t ElectraCan::get_bus_error_count() const {
  twai_status_info_t status{};
  if (!this->installed_ || twai_get_status_info(&status) != ESP_OK)
    return 0;
  return status.bus_error_count;
}

void ElectraCan::tx_path_selftest(uint32_t assert_ms) {
  // A dominant line would make every reading below meaningless, and this must
  // not step on a call in progress.
  if (!this->bus_is_idle()) {
    ESP_LOGW(TAG, "TX self-test skipped: line is not idle");
    return;
  }

  this->uninstall_();

  // Take both pins back from the TWAI matrix. The transmit pin is parked high
  // before its driver is enabled, so handing it over cannot glitch the line
  // dominant. High is recessive: the 74LVC1G07 is a non-inverting open-drain
  // buffer, so a high input leaves its output floating.
  gpio_reset_pin((gpio_num_t) this->tx_);
  gpio_set_level((gpio_num_t) this->tx_, 1);
  gpio_set_direction((gpio_num_t) this->tx_, GPIO_MODE_OUTPUT);
  gpio_set_level((gpio_num_t) this->tx_, 1);

  gpio_reset_pin((gpio_num_t) this->rx_);
  gpio_set_direction((gpio_num_t) this->rx_, GPIO_MODE_INPUT);
  // No internal pull, so the reading is the bus and not our own pin.
  gpio_set_pull_mode((gpio_num_t) this->rx_, GPIO_FLOATING);

  esp_rom_delay_us(200);
  const int idle_level = gpio_get_level((gpio_num_t) this->rx_);

  // Pull the buffer input low, which should sink the line through the 47R.
  gpio_set_level((gpio_num_t) this->tx_, 0);
  uint32_t dominant_samples = 0;
  const uint32_t samples = assert_ms == 0 ? 1 : assert_ms;
  for (uint32_t i = 0; i < samples; i++) {
    esp_rom_delay_us(1000);
    if (gpio_get_level((gpio_num_t) this->rx_) == 0)
      dominant_samples++;
  }

  gpio_set_level((gpio_num_t) this->tx_, 1);
  esp_rom_delay_us(200);
  const int released_level = gpio_get_level((gpio_num_t) this->rx_);

  const bool asserted_ok = dominant_samples == samples;
  const bool released_ok = idle_level == 1 && released_level == 1;

  if (asserted_ok && released_ok) {
    ESP_LOGW(TAG, "TX self-test PASS: line went dominant on all %" PRIu32 " samples and returned recessive",
             samples);
  } else if (!released_ok) {
    ESP_LOGE(TAG, "TX self-test INVALID: line read %d idle and %d after release, expected recessive both times",
             idle_level, released_level);
  } else {
    ESP_LOGE(TAG,
             "TX self-test FAIL: line stayed recessive for %" PRIu32 " of %" PRIu32
             " samples while driven - the transmit path is not reaching the bus",
             samples - dominant_samples, samples);
  }

  this->restore_listen_only_();
}

void ElectraCan::assist_selftest(uint32_t rounds) {
  if (!this->bus_is_idle()) {
    ESP_LOGW(TAG, "assist self-test skipped: line is not idle");
    return;
  }
  if (rounds == 0)
    rounds = 1;

  // Anything longer than this is not a rise time, it is a stuck line.
  static constexpr int64_t GIVE_UP_US = 2000;

  this->uninstall_();

  gpio_reset_pin((gpio_num_t) this->tx_);
  gpio_set_level((gpio_num_t) this->tx_, 1);
  gpio_set_direction((gpio_num_t) this->tx_, GPIO_MODE_OUTPUT);

  gpio_reset_pin((gpio_num_t) this->rx_);
  gpio_set_direction((gpio_num_t) this->rx_, GPIO_MODE_INPUT);
  gpio_set_pull_mode((gpio_num_t) this->rx_, GPIO_FLOATING);

  for (int pass = 0; pass < 2; pass++) {
    const bool assist = pass == 1;
    if (assist && this->pullup_ < 0) {
      ESP_LOGW(TAG, "assist self-test: no assist pin configured, nothing to compare against");
      break;
    }
    this->tx_pullup_(assist);
    esp_rom_delay_us(500);

    int64_t total = 0;
    int64_t worst = 0;
    uint32_t timeouts = 0;
    for (uint32_t i = 0; i < rounds; i++) {
      gpio_set_level((gpio_num_t) this->tx_, 0);  // sink the line dominant
      esp_rom_delay_us(500);
      if (gpio_get_level((gpio_num_t) this->rx_) != 0) {
        ESP_LOGE(TAG, "assist self-test INVALID: line would not go dominant");
        gpio_set_level((gpio_num_t) this->tx_, 1);
        this->tx_pullup_(false);
        this->restore_listen_only_();
        return;
      }

      const int64_t t0 = esp_timer_get_time();
      gpio_set_level((gpio_num_t) this->tx_, 1);  // release, and time the climb
      int64_t rise;
      for (;;) {
        rise = esp_timer_get_time() - t0;
        if (gpio_get_level((gpio_num_t) this->rx_) != 0)
          break;
        if (rise >= GIVE_UP_US) {
          timeouts++;
          break;
        }
      }
      total += rise;
      worst = std::max(worst, rise);
      esp_rom_delay_us(2000);
    }

    ESP_LOGW(TAG, "assist %s: recessive recovery mean %lld us, worst %lld us over %" PRIu32 " rounds%s",
             assist ? "ON " : "OFF", total / rounds, worst, rounds,
             timeouts != 0 ? " (some never recovered)" : "");
    this->tx_pullup_(false);
  }

  // One bit at the bus rate, so the numbers above mean something without a
  // calculator: anything approaching this is fatal to a frame.
  const uint32_t bit_us = this->nominal_bit_rate_ == 0 ? 88 : 1000000UL / this->nominal_bit_rate_;
  ESP_LOGW(TAG, "assist self-test done: one bit is %" PRIu32 " us", bit_us);

  this->restore_listen_only_();
}

void ElectraCan::dump_config() {
  ESP_LOGCONFIG(TAG, "Electra single-wire CAN:");
  ESP_LOGCONFIG(TAG, "  RX pin: GPIO%u", this->rx_);
  ESP_LOGCONFIG(TAG, "  TX pin: GPIO%u", this->tx_);
  if (this->pullup_ < 0) {
    ESP_LOGW(TAG, "  Recessive assist: none - transmitted frames will be rejected");
  } else {
    ESP_LOGCONFIG(TAG, "  Recessive assist pin: GPIO%d (driven only while transmitting)", this->pullup_);
  }
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
