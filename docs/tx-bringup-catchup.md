# TX bring-up catch-up (2026-08-25 → 2026-08-28)

Written so a later session can pick up without re-reading the chat. Scope is
everything after the user prompt **"can you check if the board is online?"**
(2026-08-25 18:38 +0300) through the first successful door-frame TX
(2026-08-28 09:55 +0300). Chat: [TX bring-up](681d677e-49a4-47b0-be88-aab0c1deeb97).

## Headline

**Transmit works.** One captured Open door produced

`ID=0x0DF DLC=4 data: 02 07 01 00 CRC MATCH ACK`

on C/D. The TWAI controller logged `tx done`, TEC 0, bus_err 0. 26 ms later the
panel answered `0x0DF 01 01 07` (ack of open). The lock should have released.
The user was not asked to confirm they heard it.

The missing piece was not baud, ACK, GPIO drive, or a wrong `R12` marking. It
was **recessive assist too weak for this building's bus C**. `R12` at 1 kΩ rose
in 22 µs (a quarter of an 87 µs bit) and every frame was illegal. `1 kΩ || 330 Ω
≈ 245 Ω` from GPIO5 to C/D rose in 8 µs and the same firmware sent a legal frame.

The perfboard has a 330 Ω tack in parallel with the fitted 1 kΩ. Do not desolder
that tack until a single 240 R part replaces both.

**Updated 2026-09-01:** `design.py` and the `wiring.md` BOM now say **240 R**
(`CRCW0603240RJNEA`). The **gerbers still do not contain `R12` at all** — the PCB
has not been re-laid. See the pending list.

## Already true before this window (do not re-prove)

- Unit: Electra Touch Line VTM.3S402.ELB04, indoor terminal CAN ID **`0x0DF`**.
- C/D is single-wire CAN at **11,363.6 bps** (87.9 µs/bit). YAML `bit_rate: 11364`.
- Node: ESPHome `electra-intercom` at **192.168.50.177**, SuperMini ESP32-C3.
- RX of other nodes already worked. Terminal frames CRC-match at −1.3% skew.
- Early TX failed: 32 retries, TEC 128, bus-off, errors every ~95 bit times.
- Root cause then: no pull-up on the `CD` net. `R4` 10 kΩ is on the **74LVC1G07
  input** (GPIO21), not the bus. Recessive recovery ~40 µs.
- A **permanent 1 kΩ C/D–3V3 tack** (2026-08-25 morning, before this window)
  gave CRC MATCH ACK, skew +1.1%. Same 1 kΩ left on idle turned weak dominants
  into ~58 kHz oscillation (~8 nF). That is why assist is **gated**.
- Firmware: `electra_can` `pullup_pin` = GPIO5, driven high only in the TX
  window, high-Z with pulls disabled otherwise. Buttons: **Assist self-test**,
  **TX path self-test**, **Open door**.
- `R12` was added in `design.py` (GPIO5–C/D). Schematic regenerated. **PCB was
  not re-laid. Boards were not ordered.**
- OTA often reports success and the node boots the previous image. USB flash at
  offset 0 worked. Firmware on the node may still be the 2026-08-25 11:11 +0300
  USB image.

## Lab rules (break these and the session goes sideways)

- **Never USB 5 V and external 3V3 at once.** USB-only for serial.
- **COM4** = `USB Serial Device`, Espressif `VID_303A` = SuperMini.
- **COM3** = Intel AMT SOL on the PC. Not the board, not the Saleae. Do not open it.
- Saleae: original Logic, id `EA4F1A9AD5D228EC`, Logic 2 MCP `127.0.0.1:10530`.
  **CH0 = C/D**. Late in this window **CH1 = GPIO5**. CH2 was stuck high (3V3 or
  unused). No configurable threshold (omit `digitalThresholdVolts`).
- SuperMini, USB-C at the bottom facing you: **right = RESET**, **left = BOOT**.
  RESET drops USB CDC (`Serial port closed!`).
- **Do not press Open door** unless Assist ON is in the single-digit microseconds
  and the user said **go**. It unlocks the building door.
- API is flaky when Home Assistant is also connected. `tools/press_button.py`
  and `tools/device_state.py` use host `192.168.50.177`.
- Timed Saleae captures die during the API's ~15–20 s connect. Use **≥30 s**
  timed captures and start them *before* `press_button.py`.

## Hardware as it sits (2026-08-28)

Perfboard CAN block only (`docs/perfboard.md`):

| Net | Members |
|---|---|
| 3V3 | U3.3V3, U2.5, C7.1, R4.1, D3.2(K) |
| GND | U3.GND, U2.3, C7.2, D3.1(A) |
| CAN_TX | U3.21, U2.2(A), R4.2 |
| CAN_TX_OD | U2.4(Y), R5.1 |
| CD | intercom C/D, R5.2, R6.1, R12.2, **330 Ω tack** |
| CD_ASSIST | U3.5 (GPIO5), R12.1, **330 Ω tack** |
| CAN_RX | R6.2, U3.20, D3.3(COM) |

- `U2` = SN74LVC1G07DBVR SOT-23-5. `D3` = BAT54S. `R12` = 1 kΩ 0603.
- **Added 2026-08-28:** 330 Ω from SuperMini **GPIO5 pad to C/D joint** (not to
  3V3). Meter, power off: GPIO5–C/D = **245 Ω**. GPIO5–GND ~17 kΩ is irrelevant.
- A GPIO5–3V3 jumper was tried and **does nothing useful** (see below). Removed.
- C/D run to the intercom is a short Dupont pair (was ~1 m; length of copper was
  not the 605 µs problem — the crimps were).

## Timeline

### 2026-08-25 evening — “is the board online?”

Node was reachable over Wi-Fi after the perfboard-wiring / COM4 work. Then the
user asked for a CAN-block-only solder table (`docs/perfboard.md`).

### 2026-08-26 — isolated bench, then wall

Sanity: node up. User took C/D off the wall for a bench self-test.

- Saleae MCP timed out until Logic 2 was healthy. Analyzer id as above.
- **Never USB + bench 3V3.** User switched to USB-only. COM4 is the board.
- Isolated (no intercom): Assist **OFF 2000 µs (never recovered), ON 1–2 µs**.
  TX path can sink C/D; without a bus pull-up it stays low. Wiring and gating OK.
- User said wall connected; first Assist still 2000/1–2 and **0 frames** — C/D
  was not actually on the intercom.
- After rewiring: Assist **OFF ~604–617 µs, ON ~133 µs mean / ~580 µs worst**,
  then **5 frames received**. Idle meter C/D–GND = **3.28 V**. 617 µs is ~14× the
  old flying-lead ~44 µs. Did **not** send a door frame.

### 2026-08-27 morning — Wi-Fi-only, then 2.2 V

- Wi-Fi only, no USB/Saleae: **0 frames**, counters 0 (bus idle / pair off).
- User: intercom C/D–GND is **3.3 V until our board is connected, then 2.2 V**.
  That is our node loading the bus (divider), not an open wire.
- Probe slip on 3V3–GND: red LED blink, meter 0 then 3.3 V, USB CDC drop.
  Brownout, not a firmware crash.
- COM ports: user thought COM3 was the board. **COM4 is the SuperMini**
  (ESPHome CAN lines on that port). COM3 is Intel AMT.

### 2026-08-27 afternoon — DC healthy, 1 kΩ TX still illegal

Idle, board on the bus:

| Probe | Reading |
|---|---|
| C/D–GND | 3.3 V |
| ESP 3V3–GND | 3.29 V |
| GPIO5–GND | 3.3 V (can just be C/D through R12) |
| U2 pin 4 (Y)–GND | 3.29 V (high-Z, follows C/D) |

Assist, quiet bus: **OFF 43/44 µs**, **ON 22/22 µs**. An earlier 155/611 µs OFF
was one collision with a `0x01` frame; four rounds were ~41 µs.

**Open door (1 kΩ assist):** bus-off, 32 errors at ~95 bit times. Capture:
0/52 valid CRC, payload garbage (`08 A0 5C 09`), skew **+29%**. Recessive ~67 µs,
dominant stretched, 0 µs / 4 µs chatter at the Saleae ~1.5 V threshold.

GPIO5–C/D idle = **0.98 kΩ** (`R12` is the right 1 kΩ).

A/B: jumper **GPIO5 to 3V3** so `R12` is a rail pull-up. **Same failure**, skew
+28.5%. So it is not a weak GPIO. 1 kΩ at the board is not enough on this C.

Public links (`docs/links.txt`) do **not** publish a C/D CAN TX. adrian-dobre /
kind3r / analog Electra pull **button nets**. simpalean is a closed module.
Doorman is TCS. Baud is not wrong: RX CRC-matches at 11364; REC stays 0.

### 2026-08-28 — 330 Ω parallel, door TX succeeds

- 330 Ω tacked GPIO5–C/D. Combined **245 Ω**.
- Assist: **OFF 44/45 µs, ON 8/10 µs**. Capture: CH1 stays high while C/D is
  dominant on the ON pass (gating correct). CH2 unused/high.
- **Open door:** `0x0DF 02 07 01 00 CRC MATCH ACK`. Skew on that frame **+6.2%**
  (was +29%; flying-lead 1 kΩ success was +1.1%; terminal −1.3%). GPIO5 stayed
  high. Panel ack `01 01 07` at +26 ms.

## Assist self-test decoder (firmware)

`ElectraCan::assist_selftest()` in `esphome/components/electra_can/electra_can.cpp`.
Sinks via GPIO21 / U2, times rise on GPIO20. One bit = 87 µs. Give-up = 2000 µs.

| ON | Meaning on *this* bus |
|---|---|
| 1–2 µs | Isolated bench, almost no C |
| **8–10 µs** | **Working** (245 Ω). Door TX CRC-matched |
| 22 µs | 1 kΩ on the live bus. TX will bus-off |
| 2000 µs | C/D not connected |

OFF ~44 µs = intercom pull-up only, line is on the real bus. OFF ~600 µs = high-R
joint or extra C (long Dupont crimps did this). OFF 155 mean / 611 worst over 5
rounds = four good ~40 µs plus one collision.

## Recommended `R12` (not in the repo yet)

Fit **one** E24 part, same family as the board (Vishay CRCW0603, J, AEC-Q200).
Do not BOM 1 kΩ || 330 Ω.

| Fit | Part | Role |
|---|---|---|
| **240 Ω (default)** | `CRCW0603240RJNEA` 0603 | This building; ≈ the proven 245 Ω |
| 330 Ω | `CRCW0603330RJNEA` (already `R10`) | First step weaker |
| 180 Ω | `CRCW0603180RJNEA` | Stronger if skew is still fat. Do not go below: `R5` 47 Ω and GPIO current |

1 kΩ is not an `R12` option. GPIO5 into 240 Ω plus `R5` 47 Ω is ~11.5 mA while
dominant; pulse power ~45 mW in a 100 mW part. The same current is what lifts the
dominant level to ~0.65 V, which is why 180 Ω is a trade and not an upgrade — see
the table in `docs/wiring.md`.

## Tools

| Script | Use |
|---|---|
| `tools/press_button.py "Assist self-test" 192.168.50.177 8` | Assist; watch logs |
| `tools/press_button.py "Open door" 192.168.50.177 12` | Door. Needs user **go** and smart-mode approval |
| `tools/device_state.py 192.168.50.177` | Entity state over API |
| `tools/watch_logs.py` | Wi-Fi logs including boot |
| `tools/can_decode.py <digital.csv>` | CRC-15, default 87.9 µs |
| `tools/bit_timing.py <digital.csv> [bit_us] [t0] [t1]` | Skew |

`ESPHOME_BUILD_PATH=C:\b` when compiling.

Successful 330 Ω capture lived in `%TEMP%\tx_330\` and `%TEMP%\assist_330\`, not
under `docs/captures/`. Older proof captures: `docs/captures/tx_with_pullup/`,
`tx_vs_terminal/`, `tx_gated/`, `bench_*`, `live_assist*`.

## What is still pending

1. ~~Change `R12` to 240 Ω, regenerate the schematic, fix the `perfboard.md`
   assist table and the stale `wiring.md` fail-safe line, write the finding into
   `reverse-engineering.md`.~~ **Done 2026-09-01.** `design.py` now specifies
   `240R`; ERC 0, netlist matches, `check_libs` clean. `wiring.md` gained an
   `R12` BOM line (`CRCW0603240RJNEA`), the pin map entry for GPIO5, a
   *Transmitting on C/D* section, and a fourth "will bite" item; two inverted
   claims about driving recessive were corrected there and in
   `reverse-engineering.md` E2. `perfboard.md` carries the assist decoder.
   **Still outstanding: place and route `R12` on the PCB and re-export gerbers.**
   Also note GPIO5 used to be listed as the fallback amber-LED pin; that fallback
   was moved to GPIO4.
2. Strip bring-up diagnostics: `tx_no_ack`, `probe_tx_errors_`, per-500 ms TX
   status logs.
3. **OTA rollback** before the board is sealed. USB flash is the path that
   actually takes.
4. Older assembly: J2 wire OD, speaker fit-test, JST calipers, SW1 plunger,
   optional 12 V coil confirm.
5. User confirmation that the 2026-08-28 open actually moved the lock.

## Do not redo

- Baud hunt. RX CRC-matches at 11364; REC was 0 while TEC exploded.
- GPIO5–3V3 resistor or jumper as an assist. Current into C/D has to come from
  GPIO5 (gated) or 3V3–C/D (ungated, temporary only).
- Analog Electra tricks (AVP, Talk/Open pad pull-downs from adrian-dobre) unless
  CAN TX is abandoned on purpose. Fallback if needed: pulse **our** Open touch
  pad and let the PIC send the frame.
- Another 1 kΩ-only door press. It will bus-off on this bus.
