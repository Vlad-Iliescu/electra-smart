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

The physical mode button (`SW1`) is deliberately **not** an entity: each press cycles
off → Silent → Auto-open → both → off by driving the same two template switches HA
uses, so HA's toggles, the LED and the pending-auto-open cancellation all stay in sync
regardless of which side made the change.

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

The full bill of materials, the connection diagram and the step-by-step assembly
order live in [../docs/wiring.md](../docs/wiring.md). What follows is the summary the
firmware itself depends on.

### Pin map (ESP32-C3 SuperMini, HW-466AB)

| Signal | GPIO | Notes |
|---|---|---|
| CAN RX | 20 | from `C/D` through a series resistor |
| CAN TX | 21 | into the open-drain buffer |
| Speaker relay | 6 | via a BCW65A NPN; **12 V coil on `+U` through 150 R**, not on a 5 V rail |
| `WS2812B` status LED | 7 | 330 ohm in series on data. **Must be a `WS2812B`** (3.3-5.5 V), not an `SK6812` (3.5/3.7 V) - see `docs/wiring.md` |
| Mode button | 10 | `SW1`, active low: 10 k pull-up (`R11`) + 100 nF (`C9`) on the PCB. No strapping role on the C3, and the firmware also enables the internal pull-up so a bench node without `R11` reads idle |

GPIO11-17 are the SPI flash and GPIO18/19 are the native USB, so they are
unavailable. GPIO2/8/9 are strapping pins and are best left alone.

### Bus interface - it must be open-drain

A single-wire CAN node may only ever **pull the line low** (dominant) and
otherwise leave it alone (recessive). Two equivalent one-chip ways to do that:

- **`74LVC1G07`** - non-inverting buffer with an open-drain output. Input = TWAI
  TX, output = `C/D`. This is the obvious one. Order **`SN74LVC1G07DBVR`**, the
  **SOT-23-5** package, which is the only version comfortable to hand-solder.
  Pinout is `1` = N.C., `2` = A in, `3` = GND, `4` = Y out, `5` = VCC — note that
  **pin 1 is not the input**. It also has TI's **Ioff** feature, so with VCC at 0 V
  it leaks under 10 uA and an unpowered node cannot disturb the bus.
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
GPIO21 (TWAI TX) -------+------> 74LVC1G07 pin 2 (A, input)
                                 74LVC1G07 pin 4 (Y, open-drain) --[47R]--> C/D

C/D --[1k]--> GPIO20 (TWAI RX)      + BAT54S clamp to 3V3 / GND (cheap insurance)

GND (unit) ------------------------ GND (board)     <- must be common
```

The 47 ohm on the output limits fault current. Keep it small: it forms a divider
with whatever pull-up the bus has, and the dominant level must land below the
receiver threshold (~1.5 V). Confirm the dominant level on the analyzer the first
time the node transmits.

**Input levels, measured (B9).** During a session `C/D` reads 3.3 V standby and a
hard **~0 V** while held, so it stays inside the rails and the 1 kohm series
resistor is electrically sufficient. The earlier assumption that the line carried
analog call audio turned out to be wrong. Fit the BAT54S anyway: it is a few cents
and one SOT-23, and the AC measurement (0.9 V peak, most likely the CAN bursts and
the step edges) is not clean enough to bet an ESP32 on.

The part is **onsemi `BAT54SLT1G`**, or `SBAT54SLT1G` if stocked — the leading `S` is
onsemi's AEC-Q101 variant of the same die. It must be a Schottky: at 0.32 V max forward
drop the clamp sits at 3.62 V, where a silicon diode's 0.7 V would exceed the ESP32-C3's
VDD + 0.3 V absolute maximum and become the hazard rather than the protection.

### Status LED

**`WS2812B`, not `SK6812`.** World Semi specifies the `WS2812B` at **3.3-5.5 V** in all
packages, so it runs in spec directly off our only rail, and the `V6` revision explicitly
optimises constant-current drive at 3.3 V. Every `SK6812` needs 3.5 V or more. The
`chipset: WS2812` already in `electra-intercom.yaml` is therefore correct as written —
check `rgb_order` if colours come out swapped.

### Power

**Pololu D24V10F3**, a fixed **3.3 V** 1 A buck, from the unit's `+U` (~13.5 V)
straight into the SuperMini's **`3V3`** pin. There is deliberately **no 5 V rail**.

Two reasons. Feeding 5 V would route it through the SuperMini's onboard LDO, which
is only 66% efficient dropping 5 V to 3.3 V and would put total efficiency near 57%
instead of ~87%. And a *fixed* output removes the trimpot that could otherwise be
mis-set or drift and put 13.5 V on the ESP32 — worth avoiding in an assembly that
gets sealed inside a wall unit. Full reasoning and the comparison against the 2.6 A
D24V22F3 are in [../docs/wiring.md](../docs/wiring.md).

**One rule this creates: never have USB and `+U` connected simultaneously**, since
feeding `3V3` backfeeds the onboard LDO's output. Flash on USB first, then go OTA.

No level shifting is needed anywhere: the bus, the intercom's PIC18F25K80 and the
ESP32-C3 all run at 3.3 V.

### Silent relay

Omron **G6K-2F-Y DC12** (the `F` is Omron's gullwing SMD terminal code), one pole,
**COM -> NC** in series with one conductor of the speaker pair. De-energised means the
speaker is connected, so an unpowered or crashed board leaves the intercom behaving
exactly as stock. Drive the coil from **raw `+U`**, not the 3.3 V rail: it costs no
conversion loss and keeps the switching step off the MCU's supply. The 12 V coil is
1315 ohm / 9.1 mA, so add **150 R in series** to bring it to nominal on our 13.5 V
rail, tapped downstream of the fuse and the TVS. Switch the low side with an **onsemi
BCW65ALT1G** NPN — ~1 k from the GPIO to the base, plus 10 k base to emitter so the base
stays down while the ESP32's GPIOs are high-impedance during reset — and a 1N4148W
flyback diode across the coil. See `docs/wiring.md` for why an NPN rather than a FET, and
why that 10 k matters given the part's 32 V Vceo.

**Nothing needs cutting, and the concept is already proven.** With `J101` unplugged
the terminal makes no sound at all during a call, so opening one leg of the speaker
pair is all Silent needs to do.

The speaker is on a small 2-pin plug at **`J101`**, measured ~1.08 mm at the pin
centres and judged low, so most likely **1.25 mm** ("JST 1.25"). **The speaker plugs
into our board**: a 1.25 mm SMD vertical header (`J3`) takes the speaker's own factory
plug, and a short crimped lead (`J2`) runs from our board back to `J101`. The relay's
COM->NC contact then sits in one conductor as a **PCB trace** rather than a splice in a
thin cable. Nothing is crimped on the speaker side, nothing on the intercom is modified,
and it is reversible by plugging the speaker straight back into `J101`. See
[../docs/wiring.md](../docs/wiring.md) for how to confirm the pitch and for the one
fit test to do before committing the footprint.

The unit has a **single dynamic loudspeaker** in the rear cover and no separate
piezo buzzer, so the ring melody and the call audio share it. That is what makes
Silent work at all, and also why the relay must be released on answer.

## Build and flash

```bash
cd esphome
cp secrets.yaml.example secrets.yaml     # then fill it in
esphome run electra-intercom.yaml        # first flash over USB
```

The C3 SuperMini has no USB-UART bridge, so the first flash and all logging go
over native USB (`hardware_uart: USB_SERIAL_JTAG`). After the first flash,
everything is OTA — the router is a few metres away with line of sight.

Verified to compile clean on ESPHome 2026.7.4 / ESP-IDF 5.5.5: no warnings,
RAM 33.7%, flash 53.9%. That build includes the mode button; before it the
flash figure was 53.8%, so the button cost 0.1%.

### Two Windows-only build snags

Both bit while getting the first build through, and neither is a code problem:

- **`The filename or extension is too long` — set `CCACHE_BASEDIR`.** This is
  `CreateProcess`'s 32,767-character *command line* limit, not `MAX_PATH`. ninja
  keeps its own commands short by passing a response file, but `ccache` (4.12.1,
  bundled with the ESP-IDF tools) expands that file back into a real command line
  before it execs gcc, so the limit applies again. Exactly one file is big enough
  to trip it: libsodium's `salsa20_xmm6-asm.S`, whose response file measures 33,503
  characters — and it is dead code on RISC-V, so the build dies on an object that
  would have been empty. Fix it by giving ccache a base directory, which makes it
  rewrite absolute paths into shorter relative ones:

```powershell
$env:CCACHE_BASEDIR = "C:\"
esphome compile electra-intercom.yaml
```

  The obvious ways out do **not** work, so do not waste time on them. Setting
  `IDF_CCACHE_ENABLE=0` makes things *worse*: ESPHome reads it correctly, but
  ESP-IDF's `idf.py` declares that flag with a click `envvar`, so the variable
  merely *existing* passes `-DCCACHE_ENABLE=1`. Unsetting it does not help either,
  because ESPHome then enables ccache on its own after finding the binary on the
  PATH it exports internally (`shutil.which("ccache")` from an ordinary shell
  returns `None`, which is misleading). `CCACHE_DISABLE=1` still expands the
  response file. Shortening the build path with `ESPHOME_BUILD_PATH` helps but is
  not enough on its own — measured, it removes about 700 of the ~1,540 characters
  that need to go.

- **Avoid the Microsoft Store build of Python.** It virtualises `%LOCALAPPDATA%`
  into `AppData\Local\Packages\PythonSoftwareFoundation...\LocalCache\Local`, and
  ESPHome resolves that path inconsistently: it extracts ESP-IDF to the
  virtualised location but hands CMake the literal one, which then fails with
  `include could not find requested file: .../tools/cmake/project.cmake`. Install
  Python from python.org, or junction the literal path onto the virtualised one.

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
