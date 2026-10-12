# Electra VTM.3S402.ELB04 - Reverse Engineering Log

Unit: Electra Touch Line smart+ 3.5" video terminal, `VTM.3S402.ELB04`, batch 052019
Board: `ELECTRA PCB.3S40.VTMR-REV2` (Feb 2019)
Goal: interface Ring, Open and Silent.

**Status: reverse engineering COMPLETE.** `C/D` is a single-wire CAN bus at ~11,364 bps (section D).
Ring, open, answer, call-end and monitoring frames are all decoded and CRC-verified (section C3).
Silent needs a speaker relay because the unit's MUTE is local and emits nothing (section C5).
Next phase is hardware: build the bench node and confirm the Open frame actually opens the door.

## Identified silicon (from teardown photos, 2026-06-20)

| Ref | Part | Role |
|---|---|---|
| IC7 | Microchip PIC18F25K80 | Main MCU: touch sensing, LEDs, C/D bus protocol |
| U2 | LD1117 (3.3 V LDO) | Logic rail regulator |
| IC1 | UTC MC34018 | Speakerphone / audio amp (speaker + MIC block) |
| IC6 | HEF4066BT | Quad analog switch (audio routing) |
| - | NJM4580 | Audio op-amp |
| U4 | Techwell TW9900 | Video decoder (not relevant to controls) |
| J1 | RJ45 | Bus connector (alternative to screw terminals, T568B) |

Touch pads - confirmed from the front-panel photo ([docs/front-panel.jpg](docs/front-panel.jpg)),
top to bottom:

| # from top | Icon | Function |
|---|---|---|
| 1 | handset | call answer; **monitoring** from standby (~15 s) |
| 2 | key | **access / door open** (standby = long touch 2-3 s) |
| 3 | speaker with waves | volume during talk; **MUTE / silent** (standby = long touch 2-3 s on, **short** touch off) |
| 4 | plain rectangle | **AUX** auxiliary automation (gate / garage / lighting), standby = long touch 2-3 s |

(Corrects an earlier note in this log that listed the fourth pad as "Monitor" - monitoring is on the
*handset* key, and the fourth pad is AUX.)
### Sound path - the Silent tap point (2026-08-11)

| Item | Finding |
|---|---|
| Emitter | **One dynamic loudspeaker**, ~40 mm, cone + magnet, screwed into the rear cover ([rear-cover-speaker-terminals.jpg](rear-cover-speaker-terminals.jpg)) |
| Separate piezo buzzer | **None.** Nothing resembling a piezo disc anywhere on the main board ([pcb-full-board.jpg](pcb-full-board.jpg)) |
| Speaker connection | Red/black twisted pair into **`J101`**, a small 2-pin plug (JST-style) at the lower edge of the board, pitch measured **~1.08 mm and "definitely not smaller"**, so most likely **1.25 mm** |
| Microphone connection | Red/black twisted pair **soldered** to the `MIC+` / `MIC-` pads next to the MC34018 |

The round transducer in the rear cover is the loudspeaker, not a buzzer - it has a cone, a magnet and
a spider, where a piezo would be a flat disc. Since it is the *only* emitter in the unit, **the ring
melody and the call audio necessarily share it**. That is exactly what the Silent design assumes, so
the design holds: breaking the speaker leg silences the ring, and releasing it on answer restores the
conversation.

Better still, the speaker is **plugged, not soldered**. Silent can be built as a pass-through adapter
at `J101` - our pigtail plugs into the board, the original speaker plug goes into our socket, one
conductor passes straight through and the other runs via the relay's COM->NC contact. **Nothing on the
intercom gets cut or unsoldered**, and the modification is fully reversible by unplugging it.

### Silent proven with no hardware (2026-08-11)

`J101` unplugged, then a call triggered from the panel: **the terminal made no sound at all.**

That is the whole Silent feature validated before buying a single part. It confirms in one test that
`J101` is the speaker, that the ring melody comes through the speaker rather than any hidden emitter,
and that opening one leg of that pair is sufficient to silence a call. The relay only automates what
was just done by hand, so the remaining risk in the Silent path is wiring, not concept.

### Connector

Pitch read **~1.08 mm** on the caliper, and the operator's judgement is that the true value is
**bigger than that, not smaller**. That rules out 1.0 mm and puts it at **1.25 mm**, the next standard
up. Reading 1.08 on a 1.25 mm part is exactly the error you get when the jaws sit slightly inside the
pin centres, so the two observations agree.

Pin-centre measurement on a connector this small is unreliable either way. The **housing length**
across both pins is the measurement that actually discriminates, because it scales with pitch and is
easy to place a caliper on:

| Series | Pitch | 2-pin housing length |
|---|---|---|
| JST SH | 1.0 mm | ~4.2 mm |
| "JST 1.25" / GH / PicoBlade | 1.25 mm | ~5.0 mm |
| JST ZH | 1.5 mm | ~5.6 mm |
| JST PH | 2.0 mm | ~7.9 mm |

**Careful: 1.25 mm is not one family.** Genuine JST GH, Molex PicoBlade and the ubiquitous cheap
"JST 1.25" sold for LiPo balance leads all share the pitch but differ in latch and polarisation, and
they do not reliably intermate. **This was confirmed the hard way**: an SH-proportioned 1.25 mm clone
header would not seat on the intercom's plug, with the contacts registering correctly and the housing
refusing — so the pitch is right and the family is not.

> **Both build notes below are superseded. Kept only because their reasoning is instructive.**
> The guess that consumer gear "almost always uses generic PicoBlade-style" was never tested and is
> now moot, because the final design never mates anything of the intercom's: the factory plug stays
> in `J101` and both ends of the new speaker lead are ours. And the extension-cable trick was
> replaced outright once the design moved to a PCB — the relay contact is a **PCB trace**, not a
> splice, which removed the least reliable joint in the build. Crimping at this pitch also turned out
> to be perfectly practical with an Engineer PA-09. See
> [wiring.md](wiring.md#the-speaker-connector) for what is actually built.

**Original build note:** do not crimp anything at this pitch - it needs a dedicated crimp tool. Buy a
ready-made 2-pin **male-to-female extension cable**, cut it in the middle, and put the relay's COM->NC
contact in one conductor. That gives a plug-in pass-through with no crimping and no modification to the
intercom at all. Buying both 1.25 mm and 1.0 mm costs a few euros and settles the pitch question by fit.

### Manual details that corroborate our captures

| Manual statement | Our measurement |
|---|---|
| "The terminal rings for maximum 1 min." | call window **59.70 s** |
| Factory default call duration = **2 calls** | operator heard it "ring twice" from a single press |
| "The terminal remains on for 10 more sec." after an access command | dominant hold **8.92-8.98 s** |
| "MUTE: from STAND-BY, long touch (2-3 sec.) the speaker key. The LED turns permanently **red**. In case of a call, the image is displayed but the terminal does not ring. To exit, **short** touch." | works, but is **local only** - emits no bus traffic (C13c), so we cannot use or observe it |
| "MONITORING: from STAND-BY, touch the handset key. Video + bidirectional talk last maximum **15 sec**." | real session is **8.554 s** (C13a); "15 sec" is an upper bound |
| Access command in STAND-BY = **long touch (2-3 sec.)** of the key | how C10 was captured |
| Terminals are factory-programmed to **address 1**; 2..9999 are programmed per apartment | our unit is 223 = `0xDF` (refurbished, pre-programmed) |

## A. Cold checks (power OFF)

| # | Check | Result | Date |
|---|---|---|---|
| A1 | Probe jumpers seated: GND, C/D (Line IN), GONG1, GONG2 | | |
| A2 | Open-pad wire: continuity to pad, no bridges to neighbors | | |
| A3 | GND terminal continuity to LD1117 ground plane | | |

## B. Power-on DC survey (standby, multimeter, ref = GND terminal)

| # | Measurement | Expected | Measured | Date |
|---|---|---|---|---|
| B4 | +U to GND | ~12-14 V | **~12 V** | 2026-08-10 |
| B5 | **C/D idle (SAFETY GATE: analyzer only if <= 5 V)** | ~3.3 V? | **3.3 V -> GATE PASSED** | 2026-08-10 |
| B6 | PIC Vdd / LD1117 out (+3V3 test pad) | ~3.3 V | | |
| B7 | GONG1 idle / GONG2 idle | ? | **0 V / 0 V** | 2026-08-10 |
| B8 | Open pad idle vs touched | level shift | | |
| B9 | **C/D during a session** (monitoring, button 1) | steady 0 V = digital hold; fluctuating mid-level = analog audio superimposed | **DC: 3.3 V standby -> ~0 V during the session. AC: peak seen 0.9 V.** Reads as a hard digital hold; see C6. | 2026-08-11 |

## C. Logic analyzer captures

Analyzer: Saleae Logic (original, 8ch, 24 MS/s, digital only, ~1.5 V threshold).
Wiring: GND -> black lead | CH0 -> C/D | CH1 -> Open pad (optional) | CH2 -> GONG1.
Config: D0/D1/D2, 24 MS/s, timed 25 s. Files saved to `docs/captures/`.

| # | Capture | Action during capture | File | Result | Date |
|---|---|---|---|---|---|
| C9 | Baseline | Standby, no interaction | `captures/baseline/digital.csv` | **C/D idles HIGH, ZERO edges in 10 s (bus silent in standby). CH2/GONG1 read HIGH though meter said 0 V -> CH2 lead likely floating, recheck before ring test.** | 2026-08-10 |
| C10 | **Open command** | 4x standby long-press Open (~3 s), spaced | `captures/open/digital.csv`, `captures/open.sal`, `captures/open_decoded.csv`, **`captures/open_can.csv`**, **`captures/open_can_11364.csv`** | **2 presses registered. Each = 3 bursts within ~51 ms, then C/D held LOW ~8.97 s. Bit-for-bit identical between presses - no rolling code. Now fully decoded as CAN (see section D).** | 2026-08-10 |
| C11 | **Ring** | 1 call from outdoor panel (single press), not answered, left to time out | `captures/ring.sal`, `captures/ring/digital.csv`, `captures/ring_can.csv` | **Call start + call end (timeout) captured, 59.70 s apart, 2 frames each, all CRC-verified. No audio-session low period (unlike Open). Also 2 isolated ~0.44 ms dominant glitches at t=163 s - not frames, unexplained but benign.** | 2026-08-10 |
| C12 | **Call -> answer -> open** | Helper pressed panel button; answered with Talk; pressed Open during the call | `captures/call_answer.sal`, `captures/call_answer/digital.csv` | **Full sequence captured, 8/8 CRC-verified. Revealed the answer/Talk frame and that `0x000 00 02` precedes every audio session.** | 2026-08-10 |
| C13 | **Button frames** | Standby: MUTE on (btn 3 long), MUTE off (btn 3 short), AUX (btn 4 long), MONITORING (btn 1) | `captures/buttons.sal`, `captures/buttons/digital.csv` | **Only ONE of the four actions produced any traffic in 60 s. New command codes `08` and `0C`. Which action it was is ambiguous - see C5.** | 2026-08-10 |
| C13a | **Monitoring only** | Single touch of button 1, nothing else | `captures/monitor.sal`, `captures/monitor/digital.csv` | **Reproduced the C13 mystery event byte-identically -> `08` = MONITORING, `0C` = video-enable.** | 2026-08-10 |
| C13b | **AUX only** | One long touch (2-3 s) of button 4, nothing else, 79.8 s window | `captures/auxiliary.sal`, `captures/auxiliary/digital.csv` | **ZERO bus activity. Line recessive for the entire capture, 0 frames, 0 dominant holds. AUX is not provisioned on this system.** | 2026-08-10 |
| C13c | **MUTE only** | Long touch btn 3 (LED -> red), 10 s gap, short touch btn 3 (LED -> white), 47.4 s window | `captures/mute.sal`, `captures/mute/digital.csv` | **ZERO bus activity - only 2 edges in the whole file, both the same level. MUTE is entirely local to the MCU. Silent must be done in hardware.** | 2026-08-10 |

## C2. CRC-15 verification (definitive proof of CAN)

The Saleae analyzer reports a CRC field but does not prove bit alignment. `tools/can_decode.py`
independently de-stuffs each burst and recomputes **CRC-15** (poly `0x4599`) over
SOF+ID+RTR+IDE+r0+DLC+data, then compares against the transmitted CRC. It parses **multiple
frames per burst** (back-to-back frames separated by only the inter-frame space merge into one
burst) and separately measures long dominant holds.

**Result: 18/18 frames MATCH** across all three captures (6 Open, 4 Ring, 8 Call/Answer).
Since the CRC covers the identifier, a matching CRC also proves the decoded IDs are correct.
All frames are standard data frames with `RTR=0, IDE=0, r0=0`, and every one reads ACK.

## C3. Frame catalogue (all frames observed, all CRC-verified)

### Ring, unanswered (C11)

| t offset | CAN ID | DLC | Data | Meaning |
|---|---|---|---|---|
| +0 | `0x0DF` | 4 | `04 03 01 00` | **call / ring start** |
| +0.016 s | `0x001` | 3 | `01 01 03` | response |
| +59.698 s | `0x0DF` | 2 | `04 04` | **call end** (timeout) |
| +59.734 s | `0x000` | 3 | `01 01 04` | response |

### Call answered, then opened (C12)

| t offset | CAN ID | DLC | Data | Meaning |
|---|---|---|---|---|
| +0 | `0x0DF` | 4 | `04 03 01 00` | call / ring start |
| +0.018 s | `0x001` | 3 | `01 01 03` | response |
| +2.769 s | `0x001` | 4 | `01 05 DF 00` | **answer / Talk** |
| +2.769 s | `0x0DF` | 3 | `04 01 05` | response (same burst, back-to-back) |
| +2.796 s | `0x000` | 2 | `00 02` | **engage audio** |
| +2.803 s | - | - | line dominant **1.839 s** | audio session (talking) |
| +4.703 s | `0x0DF` | 4 | `02 07 01 00` | **open** |
| +4.728 s | `0x0DF` | 3 | `01 01 07` | response |
| +4.746 s | `0x000` | 2 | `00 02` | engage audio |
| +4.753 s | - | - | line dominant **8.924 s** | audio session |

### Open from standby (C10, two presses)

Identical both times: `0x0DF` `02 07 01 00` -> `0x0DF` `01 01 07` -> `0x000` `00 02`,
then line dominant **8.975 s / 8.971 s**.

### Event codes (byte 1 of the DLC-4 announcement)

| Code | Meaning |
|---|---|
| `03` | call / ring start |
| `04` | call end |
| `05` | answer / Talk |
| `07` | open door |

Announcements are `<originator> <cmd> <other party> [00]`. Acknowledgements are the special case
**`<originator> 01 <cmd>`**: a command byte of `01` means "this is an ack" and the command being
acked moves into byte 2. That single rule accounts for every response frame in the catalogue:

| Frame | Reading |
|---|---|
| `0x001` `01 01 03` | ack of `03` (call) |
| `0x0DF` `04 01 05` | ack of `05` (answer) |
| `0x0DF` `01 01 07` | ack of `07` (open) |
| `0x000` `04 01 08` | ack of `08` (monitoring) |

It also explains why not every DLC-3 frame is an ack: `02 08 00` and `00 08 02` have `08` in the
command position, so they are a monitoring start and a monitoring end, not responses. Firmware must
therefore check for the `01` marker rather than keying off the data length - reading byte 1 as the
command unconditionally would silently misread every ack, and reading byte 2 unconditionally would
misread monitoring.

`0x000` / `00 02` is an **"engage audio"** command: in all four occurrences the line goes dominant
within ~7 ms of it.

**Addressing is solved:** the unit is labelled **223 = `0xDF`**, so `0x0DF` is this terminal's own
address, not a broadcast ID - and the `DF` byte in the answer frame is the same address. See
section D for the full field model. The practical consequence is that **`0xDF` must be a
configurable device address in the firmware**, so the same build works on a unit left at the
factory default (which would use `0x001`).

The remaining ambiguity is only *which node* physically emitted each frame, which a single-wire
probe cannot show. That does not block anything - the frames we need to *recognise* and the one we
need to *send* are both known.

## C4. The line is held dominant for seconds during a session - important design constraint

> The original title of this section claimed `C/D` carries the call audio. **B9 disproved that** -
> see C6. The design consequences below all still stand, for reasons that never depended on audio.

Every session shows up as the line being held **dominant for seconds** (1.8 s while talking,
~8.9-9.0 s after an open, 8.55 s while monitoring), and **no CAN traffic is possible during it**.
The terminal *releases* the line before transmitting: after answering, the 1.839 s hold ended at
t=14.337 and the open command went out at t=14.398, only 61 ms later.

This was originally read as analog voice riding on `C/D`, on the grounds that 11.4 kbps cannot carry
speech digitally and the digital-only analyzer shows anything under ~1.5 V as low. The bandwidth
argument is sound but the conclusion was not: metering the line during a session shows a hard ~0 V,
so the voice travels elsewhere (`Vin`/`Vout` or `+U`). What the hold actually is remains unclear -
most likely a simple "line busy / session active" signal.

**Consequences for our node:**

1. **Never drive `C/D` during a session.** A CAN controller in normal mode *will* try to: a
   multi-second dominant run looks like a stuff error, so it answers with active error flags (6
   dominant bits) until its receive error counter passes 127 and it goes error-passive (after which
   error flags are recessive and harmless). Those error flags are real dominant bits on a bus in the
   middle of a call - avoid that window regardless of what the hold means.
2. **Default to listen-only** (`TWAI_MODE_LISTEN_ONLY`), switching to normal mode only for the
   moment we transmit. In listen-only the controller never drives the line at all - no ACKs, no
   error flags. This suits a bus we are only eavesdropping on 99.9% of the time.
3. ~~Consider a hardware enable on TX~~ - dropped. See section E: the tri-state wiring that was
   proposed here would have driven the recessive state high, and listen-only already guarantees the
   open-drain output is high-Z.
4. **Only transmit when the line has been recessive**, mirroring what the terminal itself does.
5. Auto-open is unaffected: the ring capture contains **zero** dominant holds, so the line is free
   during a ring.

**Verified in C6 - and the audio guess was wrong.** See below.

## C6. B9 result: the hold is a hard digital pull, not analog audio (2026-08-11)

Measured on `C/D` to GND during a monitoring session (button 1, the repeatable 8.5 s window):

| Mode | Reading |
|---|---|
| DC, standby | ~3.3 V |
| DC, during the session | **~0 V** |
| AC, during the session | **0.9 V peak observed** |

**The DC result settles it: the line is pulled hard to ground, not modulated.** The 0.9 V seen on the
AC range is almost certainly the CAN bursts and the 3.3 V -> 0 V step edges rather than voice. Two
reasons to read it that way:

1. The AC figure was a *peak glimpsed*, not a settled mid-session reading, and the session opens with
   frames plus a full-swing 3.3 V transition - exactly what makes a DMM's AC range twitch.
2. The two readings cannot both describe voice. A genuine 0.9 V RMS signal is ~±1.3 V peak; sitting
   on a ~0 V DC average that would have to swing **below ground**, which a pull-down-to-GND node
   physically cannot do beyond a diode drop.

So section C4's inference - that voice must be analog on `C/D` because 11.4 kbps cannot carry it
digitally - was half right. The bandwidth argument holds, but the audio is **not on `C/D`**. On a
4-wire system that leaves `Vin`/`Vout` (already carrying video) or `+U` as the audio path. Worth
knowing, but it changes nothing we need to build, so it is not worth chasing.

### What this changes

- **RX input protection: relaxed.** The line stays within 0-3.3 V, so ~1 k in series into the RX GPIO
  is electrically sufficient. Fit the BAT54S clamp anyway - it is a few cents and one SOT-23 against
  the risk of a dead ESP32, and the AC reading is not clean enough to bet the board on.
- **Listen-only default: unchanged and still correct.** The reason was never only audio. A controller
  in normal mode reads a multi-second dominant hold as a stuff error and answers with dominant error
  flags; that is disruptive whether or not voice is present. Listen-only avoids it entirely.
- **"Never transmit during a hold": unchanged.** While the line is held dominant no frame can be sent
  regardless, so waiting for a quiet line remains the right rule.

## C5. Button capture (C13) - partial result

Capture spans 60.2 s. The bus is **completely silent** from 0 to 39.4 s and from 48.6 s to the end.
The single active window:

| t | CAN ID | DLC | Data | Note |
|---|---|---|---|---|
| 39.4152 | `0x0DF` | 3 | `02 08 00` | originator `02` = terminal, **new command code `08`** |
| 39.4152 | `0x000` | 3 | `04 01 08` | panel acknowledges code `08` (same burst) |
| 39.4293 | - | - | unparsable 28-bit dominant burst | likely a CAN error/abort frame |
| 39.9405 | `0x000` | 4 | `00 0C 02 00` | **new command code `0C`** |
| 39.9567 | `0x000` | 2 | `00 02` | engage audio |
| 39.9636 | - | - | line dominant **8.553 s** | session |
| 48.5785 | `0x000` | 3 | `00 08 02` | session end for code `08` |

### Operator observations - and a contradiction

The operator confirms **all three** actions visibly worked: the mute LED went solid red (and white
again on the short touch), monitoring turned the screen on with the camera view, and the AUX
long-press lit the screen/keys for several seconds.

That conflicts with the capture: **two** visible session activations (AUX and monitoring) but only
**one** traffic window in 60 s. Candidate explanations:

1. The actions were performed closer together than 5 s, so a later press landed *inside* the 8.553 s
   dominant session. No CAN traffic is possible during a hold, and a press that merely continues an
   already-active session may need no new frames - which would collapse two visible activations into
   one traffic window.
2. The bus was silent for the first 39.4 s, so some presses may have happened before the operator
   actually began, or the ordering differed from the instructions.

Either way a single mixed capture cannot resolve it. **Next step: single-action captures, one button
per capture**, starting with monitoring (safe - it cannot fire an external relay).

Note this weakens the "mute is local-only" conclusion slightly: it still holds under explanation 1
(mute genuinely produced nothing), but it should be re-confirmed by a mute-only capture.

### Resolved by a monitoring-only capture: code `08` = MONITORING

`captures/monitor.sal`, `captures/monitor/digital.csv`. A capture containing **only** a single touch
of button 1 reproduced the C13 mystery event **byte-identically and to within 1-2 ms** on every
offset (hold 8.554 s vs 8.553 s; final frame at +9.165 s vs +9.163 s).

So **`08` = monitoring**, and `0C` (frame `00 0C 02 00`) is the **video-enable** step - it only
appears in the one action that turns the screen on. The earlier guess that `08` was AUX (because it
sits next to `07`) was wrong.

Consequences:

- The manual's "monitoring lasts maximum 15 sec" is an upper bound; the real session is **8.554 s**,
  close to but measurably distinct from the Open hold (8.92-8.98 s).
- **AUX generated no traffic** in C13, despite the operator reporting the screen/keys lighting up.
  Most likely that was just the keyboard backlight responding to a touch, not an AUX session - any
  pad touch lights the keys. AUX remains unconfirmed and needs its own capture.
- Mute still looks local-only - **since confirmed** by its own capture, below.
- Bonus for the integration: monitoring is both **detectable** (we can tell when someone is viewing
  the entrance) and **triggerable** (send `02 08 00` on our channel).

### Resolved by an AUX-only capture: AUX emits nothing

`captures/auxiliary.sal`, `captures/auxiliary/digital.csv`. One long touch of button 4, nothing else, over a
**79.77 s** window. The result is unambiguous: the line stayed **recessive for the entire capture** -
five edges total, all at the same level, i.e. no transitions at all. Zero frames, zero dominant
holds.

So the C13 reading was right and the operator's "the device lit up" was the **keyboard backlight**,
which any pad touch triggers, not an AUX session. AUX either is not provisioned in this closed-loop
installation (there is no auxiliary relay module on the bus to command) or the firmware suppresses
the command when no AUX device is configured.

Nothing is lost - AUX was never part of the integration. The useful takeaway is a negative control:
it proves a button press can be genuinely bus-silent, which makes the same conclusion for MUTE
plausible rather than suspicious.

### Resolved by a mute-only capture: MUTE is local, there is no mute frame

`captures/mute.sal`, `captures/mute/digital.csv`. Mute on (long touch btn 3, LED confirmed red), a
10 s gap, then mute off (short touch, LED back to white), over **47.45 s**. The file contains
**two edges, both at the same level** - the line was recessive from the first sample to the last.
Neither the on nor the off transition put anything on the bus.

**MUTE is handled entirely inside the PIC18F25K80 and never announced.** This is a firm negative
result, not an inconclusive one: the operator visually confirmed both LED transitions, so the
feature definitely executed while the bus stayed silent. It also means we cannot *read* the unit's
mute state from the bus, so a firmware switch mirroring the native mute could silently drift out of
sync with a manual touch.

**Consequence: Silent is a hardware feature after all** - a relay contact in the speaker leg, as
originally planned. The `74LVC1G125`-gated CAN TX and the relay are independent, so this does not
disturb anything else in the design. See section G for the refined behaviour this enables.

### Unidentified but consistent

Both captures contain a short unparsable dominant burst ~14 ms after the first frame pair (28 bits in
C13, 23 bits here). It reproduces, so it is a real protocol element rather than noise - possibly an
error/overload frame or part of the video-enable handshake. Harmless for our purposes.

## D. C/D bus = SINGLE-WIRE CAN BUS (breakthrough, 2026-08-10)

**The C/D line is a CAN bus.** Confirmed three independent ways:
1. Electra's own Touch Line catalogue: *"Green LED (C/D) for working CAN BUS system"*, *"1 CAN input for the main BUS ... 4 CAN outputs for 4 video/audio terminals"* ([catalogue](https://electra.ro/uploads/download/ELT_Touch-Line-Catalogue_EN_27.02.2019_web.pdf)).
2. The MCU on this board, **PIC18F25K80**, has an integrated **ECAN** controller.
3. Saleae's CAN analyzer decodes our capture with **valid CRCs and ACK=true on every frame**.

The earlier UART confusion is fully explained: the **max run of exactly 5 identical bits** in the histogram is **CAN bit stuffing** (a stuff bit of opposite polarity is inserted after 5 identical bits). Idle-high/pulled-low = CAN **recessive/dominant**.

### Bus parameters
- Physical: **single-wire CAN**, ~3.3 V logic level, recessive = HIGH (3.3 V), dominant = pulled LOW
- Bit time **87.9 us** -> **~11,364 bps**. Decodes identically (same CRCs) at both 11379 and 11364, so nominal is almost certainly **11,363.6 bps** = `16 MHz / (2 x 44 x 16)`, a natural PIC ECAN config (Fosc 16 MHz, BRP 43, 16 TQ/bit).
- Identifiers: **standard 11-bit**
- `ack=true` on every frame proves other active nodes are present and acknowledging.

### Addressing - solved by the unit's own label (2026-08-10)

The operator noted the unit is **labelled 223**, and that the outdoor panel must be given **223**
to call this terminal. **223 decimal = `0xDF`** - which is exactly the CAN identifier that dominates
our traffic, and also the `DF` byte inside the answer frame `01 05 DF 00`.

So `0x0DF` is **not** a magic broadcast ID. It is **this terminal's address**. (The manual says
terminals are addressed 1..9999, factory default 1; this is a refurbished unit that someone
previously programmed to 223.)

A model that fits all nine frames observed so far:

| Field | Meaning |
|---|---|
| **CAN ID** | per-device channel: `0x0DF` = our terminal (223), `0x001` = the panel / apartment 1, `0x000` = system/broadcast |
| **byte 0** | originator class: `04` = panel / SCU, `01`-`02` = terminal |
| **byte 1** | command code (`03` call, `04` call end, `05` answer, `07` open) |
| **byte 2** | the other party's address (`01` = panel; `DF` = us) |

Strong corroboration for the `01`: the Touch Line manual states that *"the VPM1 main outdoor panel
keeps address **1**, set by the manufacturer"*. So the `01` appearing opposite our `DF` is exactly
the outdoor panel's factory address - the two addresses in every frame are accounted for.

Checked against every frame: the panel calls us on our channel (`0x0DF`, `04 03 01 00` - from panel,
cmd call); we answer on the panel's channel (`0x001`, `01 05 DF 00` - cmd answer, from `DF`); the
panel acknowledges on our channel (`0x0DF`, `04 01 05`); we open on our channel (`0x0DF`,
`02 07 01 00`); the panel ends the call on our channel (`0x0DF`, `04 04`).

This is still inference rather than proof, but it is self-consistent and it yields one concrete
requirement:

> **`0xDF` / 223 must be a configurable device address in our firmware, not a hardcoded constant.**

That matters for portability - a unit left at the factory default would use `0x001` instead, so the
same firmware should work on the operator's friend's unit by changing one number.

Corrects an earlier note in this log which guessed that the `01` byte was the terminal address. It
is the opposite way round: `DF` is us, `01` is the other end.

### Direction of the Open frames

Under the model above the Open announcement `0x0DF` / `02 07 01 00` carries originator class `02`
(terminal), so it is **ours to send**. Regardless, direction is no longer a blocker: CAN has
built-in arbitration, so a proper CAN controller cannot jam the bus the way a blind waveform replay
could, and a frame that was not ours is simply ignored.

## E. Decision - REVISED: use a real CAN controller, not waveform replay

- [x] **Path B (bus) - CONFIRMED, upgraded to native CAN**
- [ ] Path A - touch injection (no longer needed)

The ESP32-C3 has a built-in **TWAI** (CAN) peripheral, so instead of bit-banging a captured waveform we speak CAN properly. Benefits:
- Hardware framing, CRC, ACK, arbitration, error handling - no timing hacks
- We can **receive** everything: ring, open, talk, mute - so **ring detection comes from the bus itself** and the GONG tap becomes an optional fallback (this also makes the flaky CH2 lead moot)
- Full state awareness even when the intercom is used physically

### Bit rate feasibility on ESP32-C3
`80 MHz / 11363.6 = 7040` time quanta. With 16 TQ/bit -> `brp = 440`: `80e6 / (440 x 16) = 11363.6 bps` **exactly**. `brp=440` is within the C3's range, so an exact match is achievable. Caveat: ESPHome's `canbus`/`esp32_can` may only expose preset bit rates, so a custom timing config (or small custom component) is likely needed.

### Interface hardware (much simpler than expected)
- **RX:** `C/D` -> ~1 k series resistor -> TWAI RX GPIO (already 3.3 V, direct). Add a BAT54S clamp to 3V3/GND if B9 shows the audio swinging outside the rails.
- **TX:** TWAI TX -> **74LVC1G07** (single-gate *non-inverting open-drain* buffer) -> ~47 R -> `C/D`. TX low pulls the bus dominant-low; TX high leaves it high-Z/recessive. That is precisely a single-wire CAN driver in one tiny IC (no MOSFET+inverter needed, no level shifting).
- **10 k pull-up from the TWAI TX pin to 3V3 is mandatory.** That GPIO is a floating input before `setup()` runs, during the listen-only/normal mode swap, and across reboots and OTA. Without the pull-up the buffer input floats and could pull the bus dominant, jamming the intercom.
- **A gated recessive assist is also mandatory, and this list originally missed it.** 240 R from a GPIO to `C/D`, driven high only while transmitting. Open-drain alone cannot transmit on this bus at all - see E2.

**Correction to the note added after C12.** That note said to use a tri-state
`74LVC1G125` with `OE` on a GPIO so the ESP32 "physically cannot drive `C/D`". As
literally described - input on TWAI TX, `OE` from a GPIO - that is **wrong**: when
enabled, a tri-state buffer drives the recessive state *actively high*, which
fights the other nodes during arbitration and fights the analog audio during a
call. A single-wire CAN node may only ever pull low and release.

The `74LVC1G125` can still be used, but wired differently: **input tied to GND,
`/OE` driven by TWAI TX**. Since `/OE` is active-low, TX low enables the output and
drives the grounded input onto the line (dominant), and TX high tri-states it
(recessive). That is an open-drain driver built from a tri-state buffer, and it is
equivalent to the `74LVC1G07`.

The separate enable gate turns out to be unnecessary anyway: in listen-only mode
the TWAI controller holds TX recessive, so an open-drain output is already high-Z
and cannot disturb the bus. Listen-only plus the pull-up gives the same guarantee
with fewer parts.

**Second correction, 2026-08-28.** The paragraph above rejects driving recessive
actively high as something a single-wire CAN node "may only ever" avoid. On this bus
that is not true, and believing it cost most of a week. Nothing above is wrong about
*arbitration* — a node that drives recessive hard cannot be overruled — but a node
that never drives recessive at all cannot transmit here either. See below.

### E2. The transmit stage does not work open-drain alone (2026-08-28)

Receive worked from the first build. Transmit failed on every attempt: 32 retries,
TEC 128, bus-off, with the errors landing at ~95 bit times — the acknowledgement
region — while REC stayed at 0.

**It was not the protocol.** Ruled out individually: the bit rate (terminal frames
CRC-match at 11364), a bus that does not acknowledge (the ACK slot in captures of
terminal traffic is pulled dominant by other nodes), a missing acknowledgement of our
frames specifically (`TWAI_MODE_NO_ACK` with `TWAI_MSG_FLAG_SELF` failed identically),
and a dead transmit path (a firmware loopback self-test pulls `C/D` dominant and sees
it recover).

**The cause is edge speed.** `74LVC1G07` is open-drain and can only sink, so return to
recessive was left entirely to the intercom's own pull-up. Measured on the wall that
takes **~44 µs of an 87.9 µs bit**. Every dominant bit we sent overran its slot by
about half a bit, so other nodes mis-sampled the frame and raised error flags, which
from our side is indistinguishable from never being acknowledged.

Captures settle it. Same probe, same session:

| Frame source | Skew | CRC |
|---|---|---|
| Terminal's own driver | −1.3% | match |
| Ours, open-drain only | +46% | garbage payload |
| Ours, 1 kΩ assist | +29% | 0 of 52 valid |
| Ours, 240 R assist | **+6.2%** | **match, ACK** |

**The bus pull-up is about 1 kΩ.** This is the number that explains the whole episode:
adding 1 kΩ in parallel *halved* recovery from 44 to 22 µs, and only a resistor equal
to what is already present can halve it. So a 1 kΩ assist could never be enough. It
has to be well below the bus pull-up — 240 R gives 8 µs.

**That pull-up is only there while the terminal is active (added 7 Oct 2026).** With the
first PCB on the wall the assist self-test read OFF **607 µs** on a quiet bus, **46 µs**
in the one round that coincided with lifting the handset, and **650 µs** the round after
hanging up — ON stayed at 8–10 µs throughout. So the intercom switches its strong
pull-up onto `C/D` when it goes active and leaves the line on something roughly 14×
weaker at rest. Every August figure, including the 44 µs above and the 26 Aug reading of
604–617 µs that was then blamed on Dupont crimps, fits that pattern. Two consequences:
an un-assisted transmit at rest would not be half a bit late, it would be seven bits
late; and the 28 Aug door frame was sent with the bus awake, so a door frame from a
resting bus was a separate thing to prove. **Proved the same day**: `Open door` from the
PCB with the handset down and the bus idle went out as `tx done`, TEC 0, zero bus
errors, and the lock buzzed with someone at the door. The panel's `01 01 07` reply did
not appear in the log this time — possibly a resting-panel difference, possibly just
outside the 10 s window — but the lock opening is the result that counts.

With it, `0x0DF 02 07 01 00` transmitted clean: `CRC MATCH ACK`, `tx done`, TEC 0, and
the panel replied `0x0DF 01 01 07` 26 ms later, which is the acknowledgement of open
already catalogued in C3.

**The assist must be gated, not tied to the rail.** A permanent pull-up on `C/D` turns
weak dominant holds — the seconds-long holds documented in C4 and C6 — into bursts of
~58 kHz relaxation oscillation, and it would put a low-value path from a dead rail onto
a bus the whole building shares. So it hangs off a GPIO driven high only across the
transmit window. Circuit values, the dominant-level trade-off, and the `74LVC1G125`
variant that would remove that trade-off are in `docs/wiring.md`; the session log is in
`docs/tx-bringup-catchup.md`.

One consequence worth recording for anyone reading the public projects listed in
`docs/links.txt`: none of them transmit on `C/D`. adrian-dobre, kind3r and the analog
Electra work all pull *button nets* instead, and simpalean is a closed module. So there
was no prior art to compare against, which is part of why this took as long as it did.

## G. What this gives us for the integration

| Need | Implementation |
|---|---|
| Ring detected | receive `0x0DF` + `04 03 01 00` |
| Ring cleared | receive `0x0DF` + `04 04` (explicit call-end, so no timeout guessing; window ~59.7 s) |
| Call answered elsewhere | receive `0x001` + `01 05 DF 00` |
| Audio session active | receive `0x000` + `00 02`, or simply watch for the line going dominant |
| Open the door | transmit `0x0DF` + `02 07 01 00` alone. **Confirmed 2026-08-28** with the recessive assist fitted (E2), and **confirmed on the lock 2026-10-07** from a resting bus. The panel's `01 01 07` and the following `00 02` are the panel's own replies, not frames we send |
| Monitoring detected / triggered | receive or transmit `0x0DF` + `02 08 00` |
| Silent | **relay contact in the speaker leg** - there is no MUTE frame (C13c) |

Operating mode: **listen-only by default**, brief switch to normal mode only to transmit, and only
while the line is recessive.

### Silent, refined - better than the unit's own MUTE

Because the bus announces ring start *and* answer *and* call end explicitly, the relay does not have
to sit open the whole time Silent is enabled. Instead:

- Idle: relay **de-energised**, wired through the **normally-closed** contact, so the speaker is
  connected. Zero coil current in the normal case, and if the ESP32 is dead or unpowered the
  intercom behaves exactly as stock. Fail-safe by construction.
- Silent on + ring start (`04 03 01 00`): energise, speaker open, terminal rings silently.
- Answer, from either the panel/HA (`01 05 DF 00`) or a physical touch, or any audio engage
  (`0x000` `00 02`): de-energise immediately, so **if you do pick up you can still hear**.
- Call end (`04 04`) or open: de-energise.

This is strictly better than the native MUTE, which stays muted regardless. It also sidesteps the
one-way-toggle problem: we command the relay, so our state is always the true state, whereas the
unit's own mute could be changed by a touch we cannot observe.

Also worth noting the native mute stays available and independent - the operator can still long-touch
button 3 - and the two do not conflict, they just both silence the speaker.

Settled 7 Oct 2026: `0x0DF` `02 07 01 00` alone opens the door. The node sent that one
frame into a resting bus, the controller logged `tx done` with TEC 0, and the lock buzzed
with someone standing at it. `01 01 07` and `00 02` are the panel answering, not part of
what we transmit. The entity-level contract is in [developer.md](developer.md).

## F. Captures - all done

| # | Capture | Purpose | Outcome |
|---|---|---|---|
| C9 | Baseline | Establish idle state | bus silent in standby, idles recessive |
| C10 | Open | The frame we need to transmit | `0x0DF` `02 07 01 00`, identical every press |
| C11 | Ring | The frame we need to detect | start `04 03 01 00`, end `04 04`, 59.7 s window |
| C12 | Call -> answer -> open | Answer frame + open during a call | `0x001` `01 05 DF 00`; found the audio-session constraint |
| C13 | Volume / Monitor / AUX / Mute | Frames for the remaining features | monitoring = `08`; **AUX and MUTE emit nothing** |

Nothing further is needed from the analyzer for the planned feature set. One measurement is still
outstanding and it **does** matter: **B9**, metering `C/D` during a live call. It is not needed to
decide the *logic* (we default to listen-only regardless), but it sizes the **RX input protection**.
If the analog audio swings above 3V3 or below GND, a series resistor into the GPIO is not enough and
a clamp (BAT54S to 3V3/GND) is required to protect the ESP32. Do B9 before wiring RX.

Two questions are deliberately deferred to the bench (Phase 2), because they can only be answered by
transmitting:

1. Whether `0x0DF` `02 07 01 00` alone opens the door, or the `01 01 07` / `00 02` follow-ups are
   also required.
2. Whether the ESP32 can hold off transmitting reliably enough to never collide with an audio
   session.

Both are safe to try: CAN arbitration means a badly-timed frame loses arbitration and retries rather
than corrupting the bus.
