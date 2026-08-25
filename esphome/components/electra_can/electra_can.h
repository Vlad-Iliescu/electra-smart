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

  /* Pin that drives a resistor onto C/D for the duration of a transmission.
   *
   * The transmit buffer is open-drain and the board has no pull-up on the bus
   * side, so going dominant is fast but coming back recessive is left to the
   * intercom's own weak pull-up. Measured on the bus, that takes about 40 us
   * against an 88 us bit: every dominant bit we send overruns its slot by
   * nearly half a bit, other nodes mis-sample the frame, and it is rejected at
   * the end with an error flag. A 1 k resistor to 3V3 collapses the skew from
   * +46% of a bit to +1.1%, which matches the terminal's own driver.
   *
   * Leaving that resistor permanently connected is not acceptable, for two
   * reasons. It would put a 1 k path to a dead rail on a shared building bus if
   * this board ever loses power, and it is strong enough to fight whatever holds
   * the line dominant weakly - with it fitted, periodic bus events turned into
   * bursts of ~58 kHz relaxation oscillation.
   *
   * So the resistor hangs off a plain GPIO that is driven high only while a
   * frame is going out, and is an input at every other instant, including before
   * setup() runs and while the board is dead. That is how a single-wire CAN
   * transceiver behaves: recessive is driven, but only by the node that is
   * talking, and weakly enough that any dominant still wins.
   */
  void set_pullup_pin(uint8_t pin) { this->pullup_ = (int16_t) pin; }
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

  /* Drives the transmit path by hand and watches the receive pin to see whether
   * the line actually moved.
   *
   * The controller reports our door frame as never acknowledged, which in CAN
   * can only mean no other node received it intact. That points below the
   * protocol, at whether our dominant bits reach the line at all - something no
   * amount of listening can answer, because receive uses a different path.
   *
   * So this drops the TWAI driver, drives the transmit pin low as plain GPIO,
   * and samples the receive pin. Both sit on the same wire, so a working path
   * has to read back dominant. If it stays recessive, the fault is in the
   * buffer, its supply, the series resistor or a joint, not in the firmware.
   */
  void tx_path_selftest(uint32_t assert_ms = 20);

  /* Diagnostic: transmit with the acknowledge slot ignored.
   *
   * Our door frame goes out complete and then fails at the end of the frame,
   * every ~94 bit times. Two things look identical from the error counters: no
   * node acknowledging us, and a node that hears us but rejects the frame and
   * answers with an error flag. Ignoring the acknowledge separates them - the
   * first case starts succeeding, the second keeps failing the same way.
   *
   * This is not a fix to leave on: it also stops us acknowledging frames we
   * receive, and it throws away all delivery confirmation.
   */
  void set_tx_no_ack(bool no_ack) { this->tx_no_ack_ = no_ack; }
  bool get_tx_no_ack() const { return this->tx_no_ack_; }

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
  /// Drives the recessive-assist resistor, or leaves the pin high-Z when off.
  void tx_pullup_(bool on);
  /* Dumps the controller's own account of a transmit attempt.
   *
   * A queue that will not drain says nothing about why. The error counters do:
   * a rising transmit error counter means the frame is going out and failing,
   * arb_lost means we keep yielding to another node, bus-off means we already
   * gave up, and everything flat means the controller never started at all.
   */
  void log_tx_status_(const char *phase);
  /* Times the individual failures inside one transmit attempt.
   *
   * An unanswered acknowledge slot and a bit error at the very start of the
   * frame both cost the same 8 error-counter points, so the counters alone
   * cannot tell them apart. The spacing can: reaching the acknowledge slot
   * means a whole frame went out first, around 90 bit times, while dying at the
   * start costs closer to 18. This busy-waits, so it is a bring-up aid.
   */
  void probe_tx_errors_(uint32_t window_us);

  enum TxState : uint8_t {
    TX_IDLE = 0,
    TX_WAIT_QUIET,
    TX_SENDING,
  };

  static constexpr size_t MAX_TX_QUEUE = 4;

  uint8_t rx_{0};
  uint8_t tx_{0};
  int16_t pullup_{-1};  // negative means no recessive assist is fitted
  uint32_t rx_queue_len_{32};
  uint32_t idle_required_ms_{50};
  uint32_t tx_window_timeout_ms_{5000};
  uint32_t nominal_bit_rate_{0};
  twai_timing_config_t timing_{};

  bool installed_{false};
  bool tx_no_ack_{false};
  twai_mode_t mode_{TWAI_MODE_LISTEN_ONLY};

  bool line_recessive_{false};
  uint32_t recessive_since_{0};
  uint32_t dominant_since_{0};

  TxState tx_state_{TX_IDLE};
  uint32_t tx_state_since_{0};
  uint32_t tx_last_probe_{0};
  std::deque<canbus::CanFrame> tx_queue_;

  uint32_t rx_count_{0};
  uint32_t tx_count_{0};
  uint32_t tx_failure_count_{0};
};

}  // namespace esphome::electra_can

#endif  // USE_ESP32
