"""Canbus platform for the Electra Touch Line intercom bus.

The stock ``esp32_can`` platform cannot be used here for two reasons: its bit rate
is an enum of common CAN rates and this bus runs at ~11,364 bps, and its
listen-only mode is fixed at compile time so it can never transmit. This platform
takes an arbitrary bit rate, solves it into TWAI register values at compile time,
and switches modes at runtime instead.
"""

import logging
import math

from esphome import pins
import esphome.codegen as cg
from esphome.components import canbus
from esphome.components.canbus import CONF_BIT_RATE
import esphome.config_validation as cv
from esphome.const import CONF_ID, CONF_RX_PIN, CONF_TX_PIN

# Newer ESPHome needs to be told to pull in the IDF component that provides
# driver/twai.h; older versions include it unconditionally.
try:
    from esphome.components.esp32 import include_builtin_idf_component
except ImportError:  # pragma: no cover - depends on the installed ESPHome
    include_builtin_idf_component = None

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ["esp32"]

CONF_IDLE_REQUIRED = "idle_required"
CONF_RX_QUEUE_LEN = "rx_queue_len"
CONF_TX_WINDOW_TIMEOUT = "tx_window_timeout"
CONF_TIMING = "timing"
CONF_BRP = "brp"
CONF_TSEG1 = "tseg1"
CONF_TSEG2 = "tseg2"
CONF_SJW = "sjw"
CONF_TRIPLE_SAMPLING = "triple_sampling"

electra_can_ns = cg.esphome_ns.namespace("electra_can")
ElectraCan = electra_can_ns.class_("ElectraCan", canbus.CanbusComponent)

# The TWAI controller is clocked from APB, which is a fixed 80 MHz on every ESP32
# variant that has this peripheral.
TWAI_CLOCK_HZ = 80_000_000
BRP_MIN = 2
BRP_MAX = 16384
TSEG1_MAX = 16
TSEG2_MAX = 8
SJW_MAX = 3

# A late sample point buys tolerance for propagation delay, which is what a long,
# slow, single-wire bus has plenty of.
TARGET_SAMPLE_POINT = 0.80
# CAN needs the oscillators of all nodes to agree within a fraction of a percent.
MAX_BIT_RATE_ERROR = 0.005


def _split_segments(total_tq):
    """Choose the tseg1/tseg2 split whose sample point is closest to target."""
    best = None
    for tseg1 in range(1, TSEG1_MAX + 1):
        tseg2 = total_tq - 1 - tseg1
        if not 1 <= tseg2 <= TSEG2_MAX:
            continue
        sample_point = (1 + tseg1) / total_tq
        distance = abs(sample_point - TARGET_SAMPLE_POINT)
        if best is None or distance < best[0]:
            best = (distance, tseg1, tseg2, sample_point)
    return best


def solve_timing(bit_rate):
    """Solve an arbitrary bit rate into TWAI bit timing registers.

    Candidates are ranked by rate error first and then by time quanta per bit,
    preferring more quanta because that gives a finer sample point and more
    resynchronisation headroom.
    """
    candidates = []
    for total_tq in range(1 + TSEG1_MAX + TSEG2_MAX, 7, -1):
        split = _split_segments(total_tq)
        if split is None:
            continue
        _, tseg1, tseg2, sample_point = split
        exact = TWAI_CLOCK_HZ / (bit_rate * total_tq)
        # The prescaler register holds brp/2, so only even divisors exist.
        for brp in {2 * math.floor(exact / 2), 2 * math.ceil(exact / 2)}:
            if not BRP_MIN <= brp <= BRP_MAX:
                continue
            actual = TWAI_CLOCK_HZ / (brp * total_tq)
            error = abs(actual - bit_rate) / bit_rate
            candidates.append(
                (round(error, 9), -total_tq, brp, tseg1, tseg2, actual, sample_point)
            )

    if not candidates:
        raise cv.Invalid(
            f"{bit_rate} bps cannot be produced by the TWAI controller from an "
            f"{TWAI_CLOCK_HZ} Hz clock"
        )

    error, neg_total_tq, brp, tseg1, tseg2, actual, sample_point = min(candidates)
    if error > MAX_BIT_RATE_ERROR:
        raise cv.Invalid(
            f"The closest achievable bit rate to {bit_rate} bps is {actual:.1f} bps, "
            f"which is {error * 100:.2f}% off. CAN needs better than "
            f"{MAX_BIT_RATE_ERROR * 100:.1f}%, so nodes would not stay in sync."
        )

    _LOGGER.info(
        "electra_can: %d bps requested -> %.2f bps (%+.3f%%) using "
        "brp=%d, tseg1=%d, tseg2=%d, %d tq/bit, sample point %.1f%%",
        bit_rate,
        actual,
        (actual - bit_rate) / bit_rate * 100,
        brp,
        tseg1,
        tseg2,
        -neg_total_tq,
        sample_point * 100,
    )

    return {
        CONF_BRP: brp,
        CONF_TSEG1: tseg1,
        CONF_TSEG2: tseg2,
        CONF_SJW: min(SJW_MAX, tseg2),
        CONF_TRIPLE_SAMPLING: False,
    }


def validate_bit_rate(value):
    if isinstance(value, str):
        raise cv.Invalid(
            "bit_rate for electra_can is a plain number of bits per second, not one "
            "of the standard CAN rate names. For the Electra bus use 11364."
        )
    return cv.int_range(min=1000, max=1_000_000)(value)


TIMING_SCHEMA = cv.Schema(
    {
        cv.Required(CONF_BRP): cv.int_range(min=BRP_MIN, max=BRP_MAX),
        cv.Required(CONF_TSEG1): cv.int_range(min=1, max=TSEG1_MAX),
        cv.Required(CONF_TSEG2): cv.int_range(min=1, max=TSEG2_MAX),
        cv.Optional(CONF_SJW, default=3): cv.int_range(min=1, max=SJW_MAX),
        cv.Optional(CONF_TRIPLE_SAMPLING, default=False): cv.boolean,
    }
)


def resolve_timing(config):
    """Fill in bit timing from the requested bit rate, or check what was given.

    Done during validation rather than code generation so that an unachievable bit
    rate is reported by `esphome config`.
    """
    timing = config.get(CONF_TIMING)
    if timing is None:
        return {**config, CONF_TIMING: solve_timing(config[CONF_BIT_RATE])}
    if timing[CONF_BRP] % 2 != 0:
        raise cv.Invalid(
            "brp must be even; the prescaler register holds brp/2",
            [CONF_TIMING, CONF_BRP],
        )
    return config


CONFIG_SCHEMA = cv.All(
    canbus.CANBUS_SCHEMA.extend(
        {
            cv.GenerateID(): cv.declare_id(ElectraCan),
            cv.Required(CONF_RX_PIN): pins.internal_gpio_input_pin_number,
            cv.Required(CONF_TX_PIN): pins.internal_gpio_output_pin_number,
            cv.Optional(CONF_BIT_RATE, default=11364): validate_bit_rate,
            cv.Optional(CONF_TIMING): TIMING_SCHEMA,
            cv.Optional(
                CONF_IDLE_REQUIRED, default="50ms"
            ): cv.positive_time_period_milliseconds,
            cv.Optional(
                CONF_TX_WINDOW_TIMEOUT, default="5s"
            ): cv.positive_time_period_milliseconds,
            cv.Optional(CONF_RX_QUEUE_LEN, default=32): cv.int_range(min=4, max=256),
        }
    ),
    resolve_timing,
)


async def to_code(config):
    if include_builtin_idf_component is not None:
        include_builtin_idf_component("driver")

    var = cg.new_Pvariable(config[CONF_ID])

    # The shared canbus setup looks bit_rate up in its table of standard rates, so
    # hand it a valid name. The real timing is applied through set_timing() below.
    await canbus.register_canbus(var, {**config, CONF_BIT_RATE: "125KBPS"})

    timing = config[CONF_TIMING]
    cg.add(
        var.set_timing(
            timing[CONF_BRP],
            timing[CONF_TSEG1],
            timing[CONF_TSEG2],
            timing[CONF_SJW],
            timing[CONF_TRIPLE_SAMPLING],
        )
    )
    cg.add(var.set_nominal_bit_rate(config[CONF_BIT_RATE]))
    cg.add(var.set_rx_pin(config[CONF_RX_PIN]))
    cg.add(var.set_tx_pin(config[CONF_TX_PIN]))
    cg.add(var.set_rx_queue_len(config[CONF_RX_QUEUE_LEN]))
    cg.add(var.set_idle_required_ms(config[CONF_IDLE_REQUIRED].total_milliseconds))
    cg.add(
        var.set_tx_window_timeout_ms(config[CONF_TX_WINDOW_TIMEOUT].total_milliseconds)
    )
