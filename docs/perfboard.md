# Perfboard build: the CAN interface

Just the receive/transmit block — `U2`, `D3`, their resistors and `U2`'s
decoupling cap. The relay, status LED, mode button and the on-board regulator are
electrically independent of this and are left for the PCB.

The point of building it solidly is not tidiness. Chasing the transmit failure
cost most of a day partly because a flying-lead rig cannot be trusted: every
measurement that disagreed with expectation raised "is that the circuit or the
clip?", and there was no way to answer. This block is the one whose edges we ended
up measuring in tens of microseconds, so it is the one that has to stop moving.
It earned that: on the rebuilt board a door frame finally transmitted and was
acknowledged on 28 Aug 2026.

Designators match `pcb/tools/design.py`, so anything learned here transfers to the
board. The connections below are transcribed from `check_net.py` output after it
reported *netlist matches design.py exactly*.

## Parts

| Ref | Value / part | Package | Job |
|---|---|---|---|
| `U2` | SN74LVC1G07DBVR | **SOT-23-5** (DBV), not SC-70 | open-drain TX driver |
| `C7` | 100 nF | 0603 | `U2` decoupling |
| `R4` | 10 k | 0603 | TX pull-up, **buffer input side** |
| `R5` | 47 R | 0603 | TX series into the line |
| `R6` | 1 k | 0603 | RX series |
| `R12` | **240 R** | 0603 | **recessive assist, new part** |
| `D3` | BAT54SLT1G | SOT-23 | RX clamp |

`R12` did not exist when the gerbers were exported. It is the reason this node can
transmit at all: `U2` is open-drain and can only sink, and nothing on the board
pulled `C/D` back up, so releasing the line was left to the intercom's own pull-up.
Measured on the wall, that takes ~44 µs of an 87 µs bit — every dominant bit we
sent overran its slot, so other nodes mis-sampled the frame and rejected it.

**The value is measured, not chosen, and 1 k is not an option.** The bus pull-up is
about 1 kΩ: adding 1 kΩ in parallel *halved* the recovery to 22 µs, which only an
equal resistor can do. A quarter of a bit is still fatal, and every frame sent with
1 k bus-off'd. 240 R took it to 8 µs and produced the first frame the panel
acknowledged.

Shrinking it further is not free. While a bit is dominant, `R12` is still sourcing
into the line against `R5`, lifting the dominant level off ground:

| `R12` | Recovery | Dominant level | GPIO5 current |
|---|---|---|---|
| 1 k | 22 µs — **fails** | 0.28 V | 3.2 mA |
| 330 R | ~11 µs | 0.53 V | 8.7 mA |
| **240 R** | **8 µs — proven** | **0.65 V** | 11.5 mA |
| 180 R | ~6 µs | 0.78 V | 14.5 mA |

Levels include the bus pull-up. Against a threshold around 1.5 V, 240 R keeps
about 0.9 V of dominant margin. 180 R buys a slightly faster edge by spending that
margin, so treat it as a trade rather than a free improvement.

If more margin is ever needed, the answer is not a smaller resistor but a
`74LVC1G125` with its input on `CAN_TX` and `/OE` gated by GPIO5, so the assist
follows the transmitted bit and stops sourcing during dominant bits. That was
considered and set aside to keep the proven circuit.

`C7` is not optional even though it looks like garnish. It goes physically across
`U2` pins 5 and 3, not somewhere convenient.

## Connections, pin by pin

One row per pin. Work down it and every joint gets made exactly once. The net name
in the last column is only a label for the wire — useful when cross-checking
against the schematic, ignore it while soldering.

| Component | Pin | Connects to | Net |
|---|---|---|---|
| **`U3`** ESP32-C3 SuperMini | `3V3` | `U2.5`, `C7.1`, `R4.1`, `D3.2` | `3V3` |
| | `GND` | `U2.3`, `C7.2`, `D3.1` | `GND` |
| | `GPIO5` | `R12.1` | `CD_ASSIST` |
| | `GPIO20` | `R6.2`, `D3.3` | `CAN_RX` |
| | `GPIO21` | `U2.2`, `R4.2` | `CAN_TX` |
| **`U2`** SN74LVC1G07 | 1 (NC) | *nothing — leave floating* | — |
| | 2 (A) | `U3.GPIO21`, `R4.2` | `CAN_TX` |
| | 3 (GND) | `U3.GND`, `C7.2`, `D3.1` | `GND` |
| | 4 (Y) | `R5.1` | `CAN_TX_OD` |
| | 5 (VCC) | `U3.3V3`, `C7.1`, `R4.1`, `D3.2` | `3V3` |
| **`C7`** 100 nF | 1 | `U2.5`, `U3.3V3`, `R4.1`, `D3.2` | `3V3` |
| | 2 | `U2.3`, `U3.GND`, `D3.1` | `GND` |
| **`R4`** 10 k | 1 | `U3.3V3`, `U2.5`, `C7.1`, `D3.2` | `3V3` |
| | 2 | `U2.2`, `U3.GPIO21` | `CAN_TX` |
| **`R5`** 47 R | 1 | `U2.4` | `CAN_TX_OD` |
| | 2 | **intercom `C/D`**, `R6.1`, `R12.2` | `CD` |
| **`R6`** 1 k | 1 | **intercom `C/D`**, `R5.2`, `R12.2` | `CD` |
| | 2 | `U3.GPIO20`, `D3.3` | `CAN_RX` |
| **`R12`** 240 R | 1 | `U3.GPIO5` | `CD_ASSIST` |
| | 2 | **intercom `C/D`**, `R5.2`, `R6.1` | `CD` |
| **`D3`** BAT54S | 1 (A) | `U3.GND`, `U2.3`, `C7.2` | `GND` |
| | 2 (K) | `U3.3V3`, `U2.5`, `C7.1`, `R4.1` | `3V3` |
| | 3 (COM) | `R6.2`, `U3.GPIO20` | `CAN_RX` |
| **intercom `C/D`** | — | `R5.2`, `R6.1`, `R12.2` | `CD` |

Three parts meet at `C/D` and nowhere else: `R5` feeds the line, `R6` taps it, and
`R12` pulls it up. That junction is the whole circuit in one node, so make it a
single tidy point rather than a chain of hops.

Resistors and the capacitor are not polarised, so pin 1 and 2 are whichever way
round they land. `U2`, `D3` and `U3` are.

## Same thing as nets

Seven nets. Useful as a cross-check: if a pin above ended up on the wrong net,
comparing the two lists catches it.

| Net | Connections |
|---|---|
| `3V3` | `U3.3V3` — `U2.5` (VCC) — `C7.1` — `R4.1` — `D3.2` (K) |
| `GND` | `U3.GND` — `U2.3` — `C7.2` — `D3.1` (A) |
| `CAN_TX` | `U3.21` — `U2.2` (A) — `R4.2` |
| `CAN_TX_OD` | `U2.4` (Y) — `R5.1` |
| `CD` | **intercom `C/D`** — `R5.2` — `R6.1` — `R12.2` |
| `CD_ASSIST` | `U3.5` — `R12.1` |
| `CAN_RX` | `R6.2` — `U3.20` — `D3.3` (COM) |

`U2.1` is NC — leave it floating. On `U3`, only `3V3`, `GND`, 5, 20 and 21 are used
by this block.

## Pinouts, so nothing is from memory

**`U2` SN74LVC1G07, SOT-23-5.** These numbers are for the DBV package only — the
`1G` family does not share one pinout across its packages, so if you substitute a
different part or package, re-check against its own datasheet.

| Pin | Function | Goes to |
|---|---|---|
| 1 | NC | leave floating |
| 2 | A, input | `CAN_TX` |
| 3 | GND | `GND` |
| 4 | Y, open-drain output | `R5.1` |
| 5 | VCC | `3V3`, with `C7` to `GND` |

Non-inverting: input low pulls the output low, which is dominant. Input high
leaves the output floating, which is recessive. The firmware depends on that
polarity.

**`D3` BAT54S, SOT-23.** Two diodes in *series*, which is what makes the clamp
work rather than short the rail: pin 1 to `GND`, pin 2 to `3V3`, pin 3 the signal.
A signal below ground conducts through the lower diode, above 3V3 through the
upper.

## Two details that will bite if skipped

**`R4` is on the buffer's input, not the line.** GPIO21 is a floating input before
`setup()` runs, during the listen-only/normal mode swap, and across every reboot
and OTA. A floating buffer input can drive its output low, which holds the bus
dominant and **jams the intercom** — no calls, no door for anyone. `R4` makes
recessive the default at every instant the firmware is not in control.

**`R12` must not become a permanent pull-up.** It goes to GPIO5, which the
firmware drives high only while a frame is going out and leaves as a floating
input the rest of the time. Tied to 3V3 instead it does work electrically — that
is how the fix was first proven, and jumpering GPIO5 to 3V3 was also the A/B test
that ruled out weak pin drive — but permanently connected it fights whatever holds
the bus dominant weakly, which showed up as bursts of ~58 kHz oscillation, and it
would leave a low-value path to a dead rail on shared building wiring if this board
ever loses power.

## Layout

Cluster all seven parts right where `C/D` enters the board, with a short direct
ground return to the same point as `U3`'s ground. Nothing here is fast in the
usual sense — 11.4 kbps — but the whole failure mode was tens of microseconds of
edge slew, so stray resistance and capacitance in this cluster is exactly what we
are trying to remove from the experiment.

## Bring-up

Do it in this order; each step ends somewhere you can check.

1. **RX only.** `R6`, `D3`. Listen to the bus, confirm frames decode and that
   "Bus errors" stays at zero. Nothing can disturb the intercom yet, because there
   is no path from us to the line.
2. **TX buffer.** `U2`, `C7`, `R4`, `R5`. Before transmitting anything, confirm
   `C/D` still idles at 3.3 V and that the intercom still works completely
   normally — call, answer, door, screen. Then run **TX path self-test**, which
   should PASS.
3. **The assist.** `R12` from GPIO5 to `C/D`. Run **Assist self-test** and check
   the numbers below *before* sending a frame. **Do not press Open door** until
   assist ON reads in the single-digit microseconds — it unlocks the building door,
   and a frame sent with a weak assist will bus-off instead.

### Assist self-test decoder

The test sinks the line through GPIO21 and `U2`, then times the rise on GPIO20.
One bit is 87 µs and it gives up at 2000 µs. It holds the line dominant for 500 µs
first, so it reports the fully discharged worst case — in-frame edges recover from
only a few dominant bits and come out better than this, which is why a frame can
measure +6.2% skew while the self-test says 8 µs.

| assist ON | Meaning on *this* bus |
|---|---|
| 1–2 µs | Isolated bench with `C/D` off the wall — almost no capacitance, proves wiring and gating only |
| **8–10 µs** | **Working.** 240 R on the live bus. This is the state that transmitted |
| ~22 µs | 1 kΩ on the live bus. Too weak for this capacitance — TX will bus-off. Not a wrong part |
| ~2000 µs | Line never recovered — `C/D` is not actually connected |

Assist OFF should read **~44 µs**, which is the intercom's pull-up on its own and
confirms you really are on the bus. Two OFF readings that mean something else:
~600 µs is a high-resistance joint or extra capacitance — long Dupont crimps did
exactly this — and a mean far above the worst-case spread (e.g. 155 µs mean with a
611 µs worst over five rounds) is usually four good rounds plus one collision with
real bus traffic, not a fault.

### Then transmit

A working frame reads on the analyzer as
`ID=0x0DF DLC=4 data: 02 07 01 00 CRC MATCH ACK`, the controller logs `tx done`
with TEC 0, and the panel answers `0x0DF 01 01 07` about 26 ms later. For skew
reference from `tools/bit_timing.py`:

| Frame | Skew |
|---|---|
| Terminal's own driver | −1.3% |
| Ours, 240 R on the wall | **+6.2%** — acknowledged |
| Ours, 1 kΩ on the wall | +29% — rejected |
| Ours, no assist at all | +46% — rejected |

## Open items

- The perfboard currently has a **330 Ω tack in parallel with the 1 kΩ `R12`**,
  giving the 245 Ω that was proven. `design.py` now specifies a single 240 R part.
  Do not remove the tack until that part is fitted.
- Whether the acknowledged frame actually moved the lock has not been confirmed —
  the panel acked it, but nobody was at the door.
- OTA reports success without taking effect, so the node had to be flashed over
  USB at offset 0. Worth resolving before anything is closed into the housing,
  because USB is not reachable afterwards.
