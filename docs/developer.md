# Developer guide

How the Electra intercom node works, and the contracts a caller can rely on.
This is the API document. Hardware, the capture log, and the bring-up procedure
live elsewhere and are linked at the end.

There is no HTTP server. Home Assistant and the scripts in `tools/` both speak
the ESPHome native API (Noise-encrypted, TCP 6053). The only other interface is
the Electra `C/D` bus, which the firmware both listens to and, for one frame,
transmits on.

## Current state

Firmware on the wall is `project.version` **0.9.2-dev**, compiled 2026-10-02,
ESPHome 2026.7.4. Board 1 (PCB v0.9, relay coil bodged to the v1.0 polarity) is
powered from the intercom and joined to `C/D`. Proven on that install:

- Receive decodes ring and monitoring, CRC-valid, including while the handset is up.
- `Open door` sent into a **resting** bus (handset down, no ring) was acknowledged
  on the wire (`tx done`, TEC 0) and the building lock buzzed, 7 Oct 2026. The
  single frame `02 07 01 00` is sufficient. The panel's `01 01 07` reply was not
  seen in the log that time; the lock is the result that counts, and the firmware
  does not wait for the reply.
- Assist ON is 8–10 µs in both bus states. Assist OFF is ~600 µs with the terminal
  at rest and ~45 µs while the handset is up. The intercom only puts its strong
  pull-up on `C/D` when it is active.

Not done, and called out where it changes behaviour:

- The speaker is still on the intercom's own wiring. `Silent` will energise `K1`,
  but it cannot mute anything until the factory speaker lead is moved to `J2` and
  a new lead runs from `J3` to the speaker.
- The three self-test buttons, `Transmit without ACK`, the 500 ms TX probe and the
  DEBUG logger are still in the image. They come out before the unit is sealed.
- A spare SuperMini carries the same hostname, OTA password and Noise key. Do not
  power both at once.

## How the pieces fit

```
door panel ── C/D bus ── indoor terminal (PIC18, address 0x0DF)
                 │
                 └── this node (ESP32-C3, listen-only except while sending)
                        │
                        ├── ESPHome native API :6053
                        │     Home Assistant, tools/open_door.py
                        └── status LED, mode button, speaker relay (local)
```

The node does not sit between the panel and the terminal. It is a third CAN
node on the same wire. Losing power, crashing, or being unplugged leaves the
intercom exactly as it was: the controller is listen-only almost all the time,
the relay is normally-closed, and the recessive-assist GPIO is high-Z unless a
frame is actually going out.

`esphome/electra-intercom.yaml` is the application: entities, the frame handler,
and the scripts. `esphome/components/electra_can/` is the bus driver. The YAML
never talks to the TWAI controller directly; it sends through `canbus.send` and
reads through `on_frame`.

## Home Assistant API

### Connecting

| | |
|---|---|
| Transport | ESPHome native API, TCP **6053** |
| Encryption | Noise PSK, `api_key` in `esphome/secrets.yaml` |
| Host | `electra-intercom.local`, or `192.168.50.138` on this network |
| Discovery | Home Assistant picks the node up on its own once both are on the LAN |

Entity names below are the names Home Assistant shows. Internal ids (`ring`,
`speaker_cut`, `do_open`, …) are not exposed.

### Entities

| Name | Type | Survives reboot | What it does |
|---|---|---|---|
| Ring | binary sensor | no | The panel is calling this terminal. |
| Monitoring | binary sensor | no | Someone is viewing the entrance camera on this terminal's channel. |
| Open door | button | — | Transmits the open frame. Unlocks the building door. |
| Silent | switch | restored, default off | Arms the speaker cut for the **next ring only**. |
| Auto-open on call | switch | restored, default off | Sends the open frame when a ring starts, after the delay. |
| Auto-open delay | number, 0–60 s | restored, default 0 | Wait before auto-open. 0 sends as soon as the ring frame arrives. |
| Bus idle | binary sensor, diagnostic | — | The line has been recessive for 50 ms. |
| Call audio active | binary sensor, diagnostic | — | The line has been dominant for 100 ms. A call or monitoring hold. |
| Frames received | sensor, diagnostic | resets on reboot | CAN frames accepted since boot. Updates every 60 s. |
| Frames sent | sensor, diagnostic | resets on reboot | Frames handed to the controller since boot. |
| Transmit failures | sensor, diagnostic | resets on reboot | Queue drops, `twai_transmit` errors, and aborted sends. |
| Bus errors | sensor, diagnostic | resets on reboot | The controller's bus-error counter. Climbs by thousands during a dominant hold. That is the hold, not a bad frame. |
| WiFi signal | sensor, diagnostic | — | RSSI, dBm, every 60 s. |
| TX path self-test | button, diagnostic | — | Bring-up only. See below. |
| Assist self-test | button, diagnostic | — | Bring-up only. |
| Relay self-test | button, diagnostic | — | Bring-up only. Energises `K1` for 5 s. |
| Transmit without ACK | switch, diagnostic | always off | Bring-up only. Next transmit ignores the ACK slot. |

Not entities, on purpose:

- **Mode button** (`SW1`, GPIO10). Each press cycles off → Silent → Auto-open →
  both → off by driving the same two switches, so the LED, Home Assistant and a
  finger stay in agreement.
- **Status LED** (GPIO7, WS2812B-V6). Off, red (Silent), green (Auto-open), blue
  (both), at 35 % brightness. The V6 needs the explicit bit timings in the YAML;
  ESPHome's `WS2812` preset lights it solid white.
- **Speaker cut** (GPIO6). The coil drive. Only Silent's ring handler and the
  relay self-test turn it on.

### Behaviour

**Ring.** Set by a frame on our channel with originator `0x04` and command `0x03`.
Cleared by command `0x04` (call end) or `0x07` (open) on our channel. If neither
arrives, a 70 s backstop clears it. The measured unanswered call is 59.7 s.

**Silent** does not mute by itself. It arms the cut. The ring handler energises
the relay, and any of these release it: call end, an open, an answer (`0x05`),
or the system "engage audio" frame (`0x000` / `00 02`). Turning Silent off also
releases the coil immediately. An answered call is therefore never left muted,
and a dead node leaves the speaker connected because the contact is
normally-closed. Until the speaker lead is moved, this only clicks the relay.

**Auto-open** starts `auto_open_pending` when Ring turns on. After `Auto-open
delay` it sends the open frame only if Ring is still on, so an answer or a
timeout during the wait cancels it. Turning the switch off cancels a wait that
is already running. `mode: single` on `do_open` means a second press during a
send is dropped, not queued.

**Open door** queues one frame and returns. The driver waits until the line has
been recessive for 50 ms, drives the assist resistor, leaves listen-only, sends,
and returns to listen-only. If the line never goes quiet within 5 s the frame is
dropped and `Transmit failures` increments. A call in progress will do that.
Success in the log is `tx done` with `state=running` and `tec=0`. `state=bus-off`
or a climbing TEC means the frame was rejected; the controller is put back to
listen-only either way.

**Monitoring.** Raised only for command `0x08` on our own channel, from an
originator other than `0x00`. Cleared by the system frame `0x000` / `00 08 …`.
A 12 s backstop covers a missed end; the measured session is 8.55 s. Frames on
other apartments' channels do not raise it.

**Acknowledgements** (`<from> 01 <cmd>`) are logged (`ack of cmd 0xNN from 0xNN`)
and then ignored. Acting on them would handle every event twice.

**Call audio active** is the line level, not a frame. It is true once `C/D` has
been dominant for 100 ms. **Bus idle** is the opposite edge: recessive for the
50 ms quiet window. A dominant hold also runs the controller's error counter up,
because a multi-second dominant looks like a stuff error. In listen-only that
only increments `Bus errors`. It does not mean frames are being lost; a bad bit
time shows up as *zero* frames, since CAN drops anything whose CRC fails.

### What a client should not assume

- Pressing Open door does not report whether the lock moved. The API returns as
  soon as the button command is accepted. Read the log for `tx done`, or watch
  the door.
- `Frames sent` counts a frame handed to the controller, which happens before
  the quiet-line wait finishes. A drop after that still increments `Transmit
  failures`.
- Diagnostic sensors publish every 60 s, so a just-completed send may not have
  moved `Frames sent` yet.
- `Ring` uses device class `occupancy` and `Monitoring` uses `running`, because
  ESPHome's binary-sensor classes don't have "doorbell". Automations should key
  off the entity, not the class.

## Bus frame contract

Standard CAN, 11-bit identifiers, **11,364 bit/s**, 8-byte data max but every
observed frame is 2–4 bytes. One bit is ~88 µs. The identifier is the channel,
not the sender:

| CAN ID | Channel |
|---|---|
| `0x0DF` | This terminal. The number is the label on the unit, 223. |
| `0x001` | The panel, and a terminal left at the factory address. |
| `0x000` | System. Audio engage and the monitoring-end frame. |

Data is `<originator> <command> <other party> [0x00]`, except an acknowledgement,
which is `<originator> 01 <command>`.

| Originator | Who |
|---|---|
| `0x04` | Panel |
| `0x02` | Terminal (what we send, and what the terminal itself sends) |
| `0x01` | Panel, when it is acknowledging |
| `0x00` | System |

Commands the firmware acts on:

| Command | On | Firmware |
|---|---|---|
| `0x03` | our channel, from `0x04` | Ring on. If Silent is on, energise the relay. |
| `0x04` | our channel, from `0x04` | Ring off, relay off. |
| `0x05` | any channel | Relay off. An answer must be audible. |
| `0x07` | any channel | Relay off. On our channel, also Ring off and a log line `door opened`. |
| `0x02` | `0x000`, from `0x00` | Relay off. This is "engage audio", and the line goes dominant within a few milliseconds. |
| `0x08` | our channel, from anyone but `0x00` | Monitoring on. |
| `0x08` | `0x000`, from `0x00` | Monitoring off. |

The one frame we transmit, from `do_open`:

```
CAN ID  0x0DF
data    02 07 01 00
```

That is originator "terminal", command "open", addressed to the panel at `0x01`.
It is the frame the terminal itself sends when its Open pad is touched. Captured
from the real terminal it is followed ~26 ms later by `0x0DF` / `01 01 07` (the
panel's ack) and then `0x000` / `00 02` (engage audio, and the lock buzzes). We
send only the first of those. On 7 Oct 2026 that was enough to open the lock
from a resting bus.

Anything else on the bus is received, counted, and ignored. The full capture
catalogue is section C3 of [reverse-engineering.md](reverse-engineering.md).

### Why transmit is not just `canbus.send`

The line is held dominant for seconds during a call (about 1.8 s of talking,
about 9 s after an open, 8.55 s of monitoring). A controller left in normal mode
treats that as a stuff error and answers with dominant error flags, which steps
on the call. So `electra_can` stays in **listen-only**, where it cannot drive the
pin, and enters normal mode only for the send. `send_message()` enqueues; `loop()`
sends once `bus_is_idle()` is true.

The transmit buffer is open-drain. Coming back recessive is the intercom's
pull-up, which is too slow for our bits (~45 µs of an 88 µs bit while the
terminal is active, ~600 µs when it is idle). GPIO5 drives a 240 Ω resistor onto
`C/D` only during the transmit window. With it, recovery is 8–10 µs in either
bus state. A permanent pull-up is not acceptable: it would load the building bus
through a dead board, and it turns weak dominant holds into a ~58 kHz oscillation.

## `electra_can` configuration

```yaml
canbus:
  - platform: electra_can
    id: electra_bus
    can_id: 0x0DF          # our filter address; the handler also sees every id
    rx_pin: GPIO20
    tx_pin: GPIO21
    pullup_pin: GPIO5      # optional; without it every transmit is rejected
    bit_rate: 11364        # solved to TWAI brp/tseg at config time, ±0.5 %
    idle_required: 50ms
    tx_window_timeout: 5s
    rx_queue_len: 32
    on_frame:
      - can_id: 0x000
        can_id_mask: 0x000 # mask 0 matches every identifier
```

`bit_rate` is a plain integer, not one of ESPHome's CAN rate names. The platform
rejects a rate the 80 MHz TWAI clock cannot hit within 0.5 %. `timing:`
(`brp`, `tseg1`, `tseg2`, `sjw`, `triple_sampling`) overrides the solver; `brp`
must be even. The sample point target is 80 %.

`can_id` on the component is the address passed to the stock CAN bus setup. The
handler above does not use it as a hardware filter; it matches everything and
compares `can_id` in the lambda.

Methods the YAML calls on the component id:

| Method | Used by |
|---|---|
| `bus_is_idle()` | Bus idle sensor, and both self-tests (they refuse if it is false) |
| `audio_session_active()` | Call audio active sensor |
| `get_rx_count()` / `get_tx_count()` / `get_tx_failure_count()` / `get_bus_error_count()` | the four diagnostic sensors |
| `tx_path_selftest(ms = 20)` | TX path self-test. Drives TX as GPIO and reads it back on RX. |
| `assist_selftest(rounds = 5)` | Assist self-test. Logs OFF and ON recovery in microseconds. |
| `set_tx_no_ack(bool)` | Transmit without ACK. |

Log lines worth grepping, all under tag `electra_can` unless noted:

| Line | Meaning |
|---|---|
| `electra: ring` / `call ended` / `door opened` | Frame handler, tag `electra`. |
| `electra: ack of cmd 0xNN from 0xNN` | An acknowledgement. No state change. |
| `queued 0x0df for transmission` | The controller accepted the frame. |
| `tx begin` / `tx done` | Send started / controller queue drained. |
| `tx probe: no errors in the first 300000 us` | No bus errors during the send. The 300 ms probe is a bring-up aid and blocks the loop while it runs. |
| `line never went quiet within N ms, dropping` | Busy bus. Frame discarded. |
| `frame not sent within N ms, aborting` | Controller queue never drained. |
| `TX self-test PASS` / `FAIL` / `INVALID` | The transmit path. INVALID means the line was not recessive before or after the pulse. |
| `assist OFF` / `assist ON` | Recovery times. ON in the single-digit microseconds is the working 240 Ω. OFF near 600 µs is a resting terminal; near 45 µs is an active one. 2000 µs means `C/D` is not connected. |

## Host tools

All of these use `aioesphomeapi` from the project virtualenv and the Noise key in
`esphome/secrets.yaml`. Run them from the repo root, except `open_door.py`, which
finds the secrets file itself.

| Command | Effect |
|---|---|
| `tools\open_door.bat` | Presses Open door on `192.168.50.138` and prints whether `tx done` / `tec=0` came back. Double-clickable. Unlocks the building door. |
| `.\.venv\Scripts\python.exe tools\open_door.py [host]` | Same, without the pause. |
| `python tools\press_button.py "Open door" [host] [seconds]` | Presses any button and dumps the log. Diagnostic. |
| `python tools\device_info.py [host]` | Prints the running `project.version` and compilation time. This is the check after an OTA; the uploader's "success" has been wrong. |
| `python tools\device_state.py [host] [name ...]` | Prints live entity state. |
| `python tools\watch_logs.py [host] [seconds]` | Streams logs. |

`open_door.py` is the supported way to open the door from this PC. The other
scripts default to `electra-intercom.local` and require the working directory to
be the repo root.

## Building and flashing

From `esphome/`, with the project virtualenv:

```powershell
$env:CCACHE_BASEDIR = "C:\"
..\.venv\Scripts\esphome.exe compile electra-intercom.yaml
..\.venv\Scripts\esphome.exe upload electra-intercom.yaml
```

`CCACHE_BASEDIR` is required on Windows. Without it the build dies in ccache
expanding libsodium's assembler response file past `CreateProcess`'s 32,767
character limit. The full explanation is in [esphome/README.md](../esphome/README.md).

On every flash that matters, bump `project.version` in the YAML and then read it
back with `device_info.py`. An OTA that reports success has shipped an image the
node did not boot.

Native USB logging on the SuperMini is silent under `esphome logs` unless DTR and
RTS are deasserted before the port is opened. The API is the reliable channel;
the node does not need USB once it is on Wi-Fi.

Three Pythons, and they are not interchangeable:

| Work | Interpreter |
|---|---|
| ESPHome, and everything in `tools/` | `.\.venv\Scripts\python.exe` |
| `pcb/tools` scripts that import `pcbnew` | `"C:\Program Files\KiCad\10.0\bin\python.exe"` |
| `pcb/tools` scripts that import `cadquery` | the system `python` |

## Before sealing the unit in

Remove from `electra-intercom.yaml`, then bump the version and confirm it on the
node:

- `TX path self-test`, `Assist self-test`, `Relay self-test`
- `Transmit without ACK`
- `probe_tx_errors_` and the `tx begin` / `tx done` / `tx probe` logging in
  `electra_can.cpp` (the 300 ms busy-wait is the part that should not ship)
- `logger.level: DEBUG`, once nothing is being diagnosed

Leave the frame handler, the counters, and `Bus idle` / `Call audio active`.
Those are how a later failure gets noticed.

## Where the rest of the detail is

| Document | What it is |
|---|---|
| [reverse-engineering.md](reverse-engineering.md) | Capture catalogue, CRC proof, the dominant-hold finding, the transmit-edge root cause |
| [wiring.md](wiring.md) | Schematic, BOM, tap points, bring-up sequence, the v0.9 relay bodge |
| [perfboard.md](perfboard.md) | The hand-wired node, and the assist self-test decoder table |
| [tx-bringup-catchup.md](tx-bringup-catchup.md) | Day-by-day log of the August transmit bring-up |
| [esphome/README.md](../esphome/README.md) | Build snags, OTA rollback, LED timings, adapting the address |
