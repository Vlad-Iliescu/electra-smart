# Electra intercom ESPHome node

Firmware for an ESP32-C3 that joins the Electra Touch Line `C/D` bus as a native
CAN node, exposing the intercom to Home Assistant.

The protocol work behind this lives in [../docs/reverse-engineering.md](../docs/reverse-engineering.md).
The short version: `C/D` is a **single-wire CAN bus at ~11,364 bps**, and it also
carries the **analog call audio**, which shows up as the line being held dominant
for seconds at a time.

## What it exposes

| Entity | Type | Notes |
|---|---|---|
| Ring | binary sensor | set by the call frame, cleared by the explicit call-end frame |
| Monitoring | binary sensor | someone is viewing the entrance camera |
| Open door | button | transmits the terminal's own open frame |
| Silent | switch | arms the speaker relay for the ring only |
| Auto-open on call | switch | opens automatically when the panel calls |
| Auto-open delay | number | 0-60 s, re-checks the call is still ringing before opening |
| Bus idle / Call audio active | binary sensors | diagnostics |
| Frames received / sent / failures / bus errors | sensors | diagnostics |

## Why a custom `electra_can` component

The stock `esp32_can` platform cannot do this job:

1. **Bit rate.** Its `bit_rate` is an enum of standard CAN rates; the lowest on a
   C3 is 1 kbps and the nearest neighbours are 10 and 12.5 kbps. There is no way
   to ask for 11,364. `electra_can` takes a plain integer and solves it into TWAI
   register values at compile time.
2. **Listen-only is compile-time only.** Upstream does support a `LISTENONLY`
   mode, but `send_message()` then refuses outright, so it can never open the
   door. `electra_can` boots listen-only and swaps into normal mode for the few
   milliseconds it takes to transmit.

The bit timing it picks for 11,364 bps:

```
brp = 320, tseg1 = 16, tseg2 = 5, sjw = 3   ->  22 time quanta per bit
80 MHz / (320 x 22) = 11,363.64 bps         ->  0.003% off, sample point 77.3%
```

That is an exact hardware match, not an approximation. The measured bit time was
87.9 us (11,376 bps), so the request and the bus agree to about 0.1%, comfortably
inside what CAN tolerates. The solved values are printed at compile time and again
in the boot log, and can be overridden with an explicit `timing:` block.

### Transmit safety

Transmitting is gated three ways, because driving the line during a call would
corrupt the audio:

- The controller sits in **listen-only** mode, where it physically never drives
  the line: no ACKs, no error flags.
- A frame is only sent after the line has been **continuously recessive** for
  `idle_required` (50 ms default, ~570 bit times). An audio session holds the
  line dominant for 1.8-9 s, so it cannot be mistaken for an idle bus.
- If the line never goes quiet within `tx_window_timeout` (5 s), the frame is
  dropped with a warning rather than forced out.

`canbus.send` therefore *queues*; the frame goes out from the next `loop()` that
finds a quiet line.

## Hardware

### Pin map (ESP32-C3 SuperMini, HW-466AB)

| Signal | GPIO | Notes |
|---|---|---|
| CAN RX | 20 | from `C/D` through a series resistor |
| CAN TX | 21 | into the open-drain buffer |
| Speaker relay | 6 | via a transistor, relay coil on 5 V |
| WS2812 status LED | 7 | 330 ohm in series on data |

GPIO11-17 are the SPI flash and GPIO18/19 are the native USB, so they are
unavailable. GPIO2/8/9 are strapping pins and are best left alone.

### Bus interface - it must be open-drain

A single-wire CAN node may only ever **pull the line low** (dominant) and
otherwise leave it alone (recessive). Two equivalent one-chip ways to do that:

- **`74LVC1G07`** - non-inverting buffer with an open-drain output. Input = TWAI
  TX, output = `C/D`. This is the obvious one.
- **`74LVC1G125`** - tri-state buffer, **input tied to GND** and **`/OE` driven by
  TWAI TX**. Because `/OE` is active-low: TX low enables the output, which drives
  the grounded input value onto the line (dominant); TX high disables it (high-Z,
  recessive). Same behaviour, using the part already in the plan.

> **Do not** wire the `74LVC1G125` the intuitive way, with the input on TWAI TX
> and `/OE` from a spare GPIO. Enabled, it would actively drive the recessive
> state **high**, fighting the other nodes during arbitration and fighting the
> analog audio during a call. The earlier plan implied that wiring; it is wrong.
> The enable gate is also unnecessary: in listen-only mode TWAI TX idles high, so
> an open-drain output is already high-Z and cannot disturb the bus.

**A pull-up on the buffer input is not optional.** Add **10 kohm from TWAI TX
(GPIO21) to 3V3**. Before `setup()` runs, during the mode swap, and across
reboots and OTA, that pin is a floating input; without the pull-up the buffer
could pull the bus dominant and jam the intercom. The pull-up guarantees
"recessive" is the default state at every moment the firmware is not in control.

```
                       +3V3
                        |
                       10k
                        |
GPIO21 (TWAI TX) -------+------> 74LVC1G07 input
                                 74LVC1G07 output --[47R]--> C/D

C/D --[1k]--> GPIO20 (TWAI RX)      + optional BAT54S clamp to 3V3 / GND

GND (unit) ------------------------ GND (board)     <- must be common
```

The 47 ohm on the output limits fault current. Keep it small: it forms a divider
with whatever pull-up the bus has, and the dominant level must land below the
receiver threshold (~1.5 V). Confirm the dominant level on the analyzer the first
time the node transmits.

> **Measure `C/D` during a live call before connecting RX** (check B9 in the
> reverse-engineering log). The line carries analog audio and its amplitude is
> still unmeasured. If it swings above 3V3 or below GND, the 1 kohm series
> resistor alone is not enough and the BAT54S clamp becomes mandatory.

### Power

MP1584EN buck from the unit's `+U` (~12 V measured) to **5 V**, into the
SuperMini's 5 V pin. Set the output with the trimmer and verify it **before**
connecting it to the board. No level shifting is needed anywhere: the bus, the
intercom's PIC18F25K80 and the ESP32-C3 all run at 3.3 V.

### Silent relay

Omron **G6K-2F-Y-5VDC**, one pole, **COM -> NC** in series with one conductor of
the speaker pair. De-energised means the speaker is connected, so an unpowered or
crashed board leaves the intercom behaving exactly as stock. Drive the coil from
5 V through an NPN or logic-level FET (MMBT2222 with ~1 k on the base, or a
2N7002) with a 1N4148 flyback diode across the coil.

Check first whether the speaker lands on a plug — if it does, build a pass-through
adapter and cut nothing.

## Build and flash

```bash
cd esphome
cp secrets.yaml.example secrets.yaml     # then fill it in
esphome run electra-intercom.yaml        # first flash over USB
```

The C3 SuperMini has no USB-UART bridge, so the first flash and all logging go
over native USB (`hardware_uart: USB_SERIAL_JTAG`). After the first flash,
everything is OTA — the router is a few metres away with line of sight.

## Bring-up order

Do not skip straight to opening the door. Each step below is safe on its own and
each one validates an assumption.

1. **Listen only.** Flash as-is and watch the log. Ring the panel. You should see
   `ID=0x0DF` with `04 03 01 00`, then `04 04` about 60 s later, matching the
   analyzer captures exactly. "Frames received" should climb and "Bus errors"
   should stay at zero. **This is the bit-timing test** — wrong timing shows up as
   zero frames or a climbing error count, not as subtly wrong data, because CAN
   checks a CRC over every frame.
2. **Survive a call.** Answer a call and confirm the node logs no errors while the
   line is held dominant for the audio session, and that "Call audio active" goes
   on. Confirm the intercom's own audio is unaffected.
3. **Transmit.** Press "Open door" with the line idle. If the door does not open,
   the open announcement may need its follow-up frames (`01 01 07`, then `00 02`)
   — see the open items in the plan.
4. **Silent.** Arm Silent, have the panel call, confirm the ring is silent, then
   answer and confirm you can hear. This also tells us whether the ring melody and
   the voice share one emitter.

## Adapting to another unit

The only unit-specific value is the terminal address, at the top of the YAML:

```yaml
  terminal_addr: "0xDF"   # 223, from the label on this unit
```

A terminal left at the factory default is address 1, so `"0x001"`.
