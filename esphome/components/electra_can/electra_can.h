#pragma once

#ifdef USE_ESP32

#include "esphome/components/canbus/canbus.h"
#include "esphome/core/component.h"
#include "esphome/core/hal.h"

#include <driver/twai.h>

#include <deque>

namespace esphome::electra_can {

/* Single-wire CAN node for an Electra Touch Line intercom bus.
 *
 * Two things make the stock esp32_can component unusable here:
 *
 *  - The bus runs at ~11,364 bps, which is not one of the bit rates the stock
 *    component offers. Timing is supplied here as raw brp/tseg values instead.
 *  - The C/D line carries the analog call audio as well as CAN data, showing up
 *    as the line sitting dominant for seconds at a time. A controller in normal
 *    mode reads that as a stuff error and answers with dominant error flags,
 *    which would step on the audio. So the controller stays in listen-only mode
 *    (where it physically never drives the line) and only enters normal mode for
 *    the few milliseconds it takes to send a frame, and only once the line has
 *    been quiet.
 *
 * Because of that, send_message() queues rather than transmits, and the frame
 * goes out from loop() once the mode swap is safe.
 */
class ElectraCan final : public canbus::Canbus {
 public:
  void set_rx_pin(uint8_t rx) { this->rx_ = rx; }
  void set_tx_pin(uint8_t tx) { this->tx_ = tx; }
  void set_rx_queue_len(uint32_t len) { this->rx_queue_len_ = len; }
  void set_idle_required_ms(uint32_t ms) { this->idle_required_ms_ = ms; }
  void set_tx_window_timeout_ms(uint32_t ms) { this->tx_window_timeout_ms_ = ms; }
  void set_nominal_bit_rate(uint32_t bit_rate) { this->nominal_bit_rate_ = bit_rate; }
  void set_timing(uint32_t brp, uint8_t tseg1, uint8_t tseg2, uint8_t sjw, bool triple_sampling);

  void loop() override;
  void dump_config() override;

  /// True once the line has been continuously recessive for the configured quiet time.
  bool bus_is_idle() const;
  bool is_transmitting() const { return this->tx_state_ != TX_IDLE; }
  /// True while the line is held dominant, which on this bus means a call is up.
  bool audio_session_active() const;

  uint32_t get_rx_count() const { return this->rx_count_; }
  uint32_t get_tx_count() const { return this->tx_count_; }
  uint32_t get_tx_failure_count() const { return this->tx_failure_count_; }
  uint32_t get_bus_error_count() const;

 protected:
  bool setup_internal() override;
  canbus::Error send_message(canbus::CanFrame *frame) override;
  canbus::Error read_message(canbus::CanFrame *frame) override;

  bool install_(twai_mode_t mode);
  void uninstall_();
  bool restore_listen_only_();
  bool enter_normal_mode_();
  void sample_line_();
  void service_tx_();

  enum TxState : uint8_t {
    TX_IDLE = 0,
    TX_WAIT_QUIET,
    TX_SENDING,
  };

  static constexpr size_t MAX_TX_QUEUE = 4;

  uint8_t rx_{0};
  uint8_t tx_{0};
  uint32_t rx_queue_len_{32};
  uint32_t idle_required_ms_{50};
  uint32_t tx_window_timeout_ms_{5000};
  uint32_t nominal_bit_rate_{0};
  twai_timing_config_t timing_{};

  bool installed_{false};
  twai_mode_t mode_{TWAI_MODE_LISTEN_ONLY};

  bool line_recessive_{false};
  uint32_t recessive_since_{0};
  uint32_t dominant_since_{0};

  TxState tx_state_{TX_IDLE};
  uint32_t tx_state_since_{0};
  std::deque<canbus::CanFrame> tx_queue_;

  uint32_t rx_count_{0};
  uint32_t tx_count_{0};
  uint32_t tx_failure_count_{0};
};

}  // namespace esphome::electra_can

#endif  // USE_ESP32
