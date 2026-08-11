# Wiring and bill of materials

Bench prototype for the Electra Touch Line `VTM.3S402.ELB04` -> Home Assistant node.
Protocol background is in [reverse-engineering.md](reverse-engineering.md); firmware
is in [../esphome/](../esphome/).

**Guiding principle: nothing on the intercom gets cut, desoldered or permanently
altered.** Power and bus come off screw terminals that are already there, and the
speaker intercept is a plug-in adapter. Everything is reversible by unplugging.

## Shopping list

**Everything is SMD except the two modules**, which only exist as modules. Passives are
specified as **0805** because that is the comfortable size, not because anything finer
is off the table — hot air and a preheat plate are available, so DFN/QFN and 0603 are
fair game where they buy something. The regulator section of the PCB uses 1206 and
0603 for exactly that reason.

**Buy quality, not cheap.** This is a permanent install that should outlive several
phone upgrades, and the entire bill of materials is around EUR 50 at good-part prices —
there is no meaningful saving available by economising. Genuine Omron relay, genuine TI
or Nexperia logic, named-brand capacitors. See the reliability notes in the power
section for which choices actually matter and which are theatre.

| Qty | Part | Package | Purpose |
|---|---|---|---|
| 1 | **ESP32-C3 SuperMini** | module | The node. Small enough to hide behind the PCB |
| 1 | **Pololu D24V10F3** (#2830) | module, **fixed 3.3 V**, 1 A, 3.4-36 V in | 13.5 V from `+U` straight to 3.3 V. See the power section for why fixed and why 1 A |
| 1 | **SN74LVC1G07DBVR** (TI) | **SOT-23-5 (DBV)** - not SC-70 | Open-drain CAN TX driver. Package matters, see below |
| 1 | **Omron G6K-2F-Y DC12** | **SMD gullwing**, DPDT, gold bifurcated contacts | Speaker cut for Silent. `F` in the part number *is* the surface-mount terminal code |
| 1 | **MMBT2222** or **2N7002** | SOT-23 | Relay coil driver |
| 1 | **1N4148W** | **SOD-123** | Coil flyback. `W` = SOD-123, `WS` = smaller SOD-323 |
| 1 | **BAT54S** | SOT-23, *series* pair | Clamps the CAN RX pin to the rails |
| 1 | **WS2812B** (5050) or **SK6812 MINI** (3535) | SMD, single pixel | Status LED. The 3535 is smaller and couples to fibre more neatly |
| 1 | **"JST 1.25" 2-pin extension cable** | pre-crimped | Speaker pass-through. Buy the 1.0 mm SH version too - see note |
| 1 | 10 k resistor | 0805 | **Mandatory** pull-up on CAN TX |
| 1 | 1 k resistor | 0805 | CAN RX series limit |
| 1 | 47 R resistor | 0805 | CAN TX series limit |
| 1 | 1 k resistor | 0805 | Relay transistor base |
| 1 | 150 R resistor | 0805 | Relay coil dropper, so a 12 V coil sees 12 V on a 13.5 V rail |
| 1 | 330 R resistor | 0805 | WS2812 data line |
| 1 | 100 nF ceramic X7R | 0805, 50 V | Decoupling at the buffer |
| 1 | 47-100 uF **aluminium electrolytic** | SMD V-chip, **50 V, 105 C, >=5000 h** | Bulk on `VIN` - see the LC-spike note, and why not an MLCC. Quality brand: this is the only wear-out part in the design |
| 1 | 10 uF ceramic X7R | 0805, 16 V+ | On 3V3 next to the ESP32, for WiFi bursts |
| - | 26-28 AWG silicone wire | | Thin and flexible; there is not much room |
| - | Kapton tape, heat-shrink | | Insulating the install |
| - | 2 mm end-glow PMMA fibre | + opaque heat-shrink | Light pipe to the case face (later) |

**Do not buy a differential CAN transceiver** (TJA1051, SN65HVD230, MCP2551). This
bus is single-wire; those parts need CANH/CANL and will not work.

### Notes on the SMD choices

- **The relay is already surface-mount.** In Omron's G6K numbering the third field is
  the terminal shape: **`F` = outside-L gullwing SMD**, `G` = inside-L SMD, `P` =
  through-hole. So `G6K-2F-Y` is the gullwing SMD part, and gullwing is the *easier*
  of the two SMD options to hand-solder because the leads are visible outside the body.
  Avoid the `G` variant, whose terminals tuck underneath. Note SMD versions ship in
  moisture-proof packaging.
- **Use an electrolytic on `VIN`, not an MLCC.** Two reasons. A 50 V MLCC loses a large
  fraction of its rated capacitance under DC bias, so a nominal 22 uF may deliver half
  that at 13.5 V. More importantly, the cap is there to damp LC ringing on an
  inductive feed, and an electrolytic's ESR does the damping — a low-ESR ceramic
  raises the Q and can make the ringing *worse*.
- **For prototyping**, either a small SMD-footprint protoboard (SOT-23 + 0805 pads) or
  a SOT-23-5 breakout adapter for the buffer. The only genuinely fiddly part is the
  buffer; everything else is 0805 or SOT-23.
- **Buy passives as an 0805 assortment book** rather than individually. The five
  resistor values and three capacitor values here cost less as one kit than as eight
  line items, and you will want spares of 0805 parts anyway.
- **When the custom PCB comes**, the two modules are what to replace: the SuperMini
  becomes an **ESP32-C3-MINI-1** castellated SMD module, and the regulator becomes a
  discrete **AP63203** design — see the regulator BOM in the power section below.

Buy the SC-70 and SOT-23 parts in threes. They cost the same as one, and they are
small enough that losing or cooking one is a matter of when, not if.

### The speaker connector

`J101` measured ~1.08 mm at the pin centres, judged to be on the low side of true, so
**1.25 mm** is the best estimate — the next standard up, and exactly the error you get
when the caliper jaws sit inside the pin centres. Confirm by **housing length** across
both pins instead, which scales with pitch and is far easier to measure: **~4.2 mm**
means 1.0 mm SH, **~5.0 mm** means 1.25 mm, ~5.6 mm means 1.5 mm ZH.

Two traps here:

- **1.25 mm is not one family.** Genuine JST GH, Molex PicoBlade and the cheap
  "JST 1.25" sold for LiPo balance leads share the pitch but differ in latch and
  polarisation, and do not reliably intermate. Consumer gear like this almost always
  uses the generic **"JST 1.25"**, so buy that one.
- **Buy both pitches.** A 1.0 mm and a 1.25 mm extension cable together cost a few
  euros, and fit settles the question in seconds where measurement has already cost
  two attempts. The spare gets used on something else eventually.

### Choosing the 74LVC1G07 package

TI sells this die in several packages and only one is sensible to hand-solder:

| Package | Body size | Verdict |
|---|---|---|
| **DBV (SOT-23-5)** | 2.9 x 1.6 mm, 0.95 mm pitch | **buy this one** |
| DCK (SC70-5) | 2.0 x 1.25 mm, 0.65 mm pitch | doable but fiddly |
| DRL (SOT-5X3) | smaller again | avoid |
| DSF (X2SON-6) | 1.0 x 1.0 mm | not hand-solderable |

So the order code is **`SN74LVC1G07DBVR`**. If TME is out of the TI part, any
manufacturer's 74LVC1G07 is fine — just check the package field says **SOT-23-5**
(also written SOT753 or SC-74A) and not SOT-353 / SC-70 / SOT-553.

### Pinout (DBV and DCK, from the TI datasheet)

| Pin | Function |
|---|---|
| 1 | **N.C.** - no internal connection, leave floating |
| 2 | **A** - input, from GPIO21 |
| 3 | **GND** |
| 4 | **Y** - open-drain output, to the 47 R and then `C/D` |
| 5 | **VCC** - 3V3, with 100 nF to GND |

**Pin 1 is not the input.** That is the mistake to avoid here; the input is pin 2.

Output drive is 24-32 mA depending on VCC, far more than needed to pull the bus
dominant.

### A bonus that matters: Ioff

This part has TI's **Ioff** partial-power-down feature: with VCC at 0 V, the input and
output leak no more than **10 uA** even with voltage applied to them. So if our node
loses power or is disconnected, the buffer cannot load or pull the `C/D` line.

Together with the 10 k pull-up, that closes the fail-safe story completely. The
intercom is undisturbed whether our board is running, rebooting, mid-OTA, crashed, or
completely dead.

### Acceptable substitutions

- **`74LVC1G125` instead of `74LVC1G07`**: works, but only wired as **input tied to
  GND, `/OE` driven by CAN TX**. Since `/OE` is active-low, TX low enables the
  output and drives the grounded input onto the line (dominant), TX high tri-states
  it (recessive). Do *not* put TX on the input and `/OE` on a GPIO — enabled, it
  would drive the recessive state actively high and fight the bus.
- **`SK6812` instead of `WS2812`**: better behaved at 3.3 V. Change `chipset:` in the
  `light:` block of the YAML to match, and check `rgb_order` if the colours come out
  swapped.
- **Plain RGB LED + 3 PWM GPIOs** instead of the addressable pixel: more robust and
  fully in spec, at the cost of two extra GPIOs (there are six spare). Requires
  swapping the `light:` block in the YAML for an `rgb` light over three `ledc`
  outputs.
- **Optocoupler (PC817) on `GONG1`/`GONG2`**: no longer needed. Ring detection comes
  off the CAN bus. Only worth adding as a fallback if bus receive proves unreliable.

## Power architecture

**One 3.3 V rail, plus raw `+U` for the relay coil. There is no 5 V rail anywhere.**

### Why 3.3 V rather than 5 V

Feeding 5 V to the SuperMini's `5V` pin sends it through the board's onboard linear
regulator to reach 3.3 V, and an LDO dropping 5 V to 3.3 V is only 3.3/5 = **66%
efficient** no matter how good the buck ahead of it is. A ~87% buck followed by that
LDO gives about **57% end to end**. Going straight to 3.3 V and feeding the `3V3` pin
bypasses the LDO entirely for roughly **87%**.

That is a ~35% cut in what we draw from the shared intercom supply, and it dwarfs any
difference between one buck module and another. It is the single decision that matters
for efficiency here.

### Why fixed output, not a trimpot

This is the stronger reason to buy a Pololu module, more than efficiency.

An adjustable module (MP1584EN and friends) sets its output with a tiny multi-turn
trimpot. If that pot is mis-set, drifts, or is nudged while stuffing the board into
the case, it can put anything up to 13.5 V onto the ESP32's supply rail and destroy
it — and this assembly gets sealed inside a wall-mounted unit you would rather not
open again. A **fixed 3.3 V** module deletes that entire failure mode, along with the
"set the buck first and measure it" step that was otherwise the most dangerous step of
the build.

The Pololu parts also use known-genuine components with a documented layout, where
cheap adjustable modules are routinely built with relabelled or substituted regulator
ICs and vary batch to batch. For a sealed install, provenance is worth more than the
price difference.

### Why the 1 A part and not the 2.6 A one

The **D24V22F3** (3.3 V, 2.6 A, #2857, $18.95) is over-specified for this job and
worse at it. Our load is ~100 mA average with brief WiFi peaks — about **4% of its
rating**, the worst end of any converter's efficiency curve — and it sits there 24/7
because the node has to listen on the bus continuously and never sleeps. Light-load
behaviour is therefore what actually matters, and by Pololu's own figures:

| | D24V10F3 (#2830) | D24V22F3 (#2857) |
|---|---|---|
| Rated current | 1 A | 2.6 A |
| **Light-load power-save mode** | **yes** | not stated |
| **No-load quiescent** | **200 uA** | 1 mA |
| Thickness | **3.5 mm** | 8 mm |
| Size | 18 x 13 mm | 17.8 x 17.8 mm |
| Price | **$12.95** | $18.95 |
| Reverse-voltage protection | no | **yes** |

The 1 A part wins on the two things that matter here — it drops into a reduced
switching frequency at light load, and its idle draw is 5x lower (200 uA vs 1 mA is
2.7 mW vs 13.5 mW burned continuously at 13.5 V doing nothing). It is also **less than
half the thickness**, which is worth real money when the whole assembly has to hide
behind the intercom PCB, and it costs less.

Its one disadvantage is **no reverse-voltage protection**, which the 2.6 A part has.
Mitigate it by measuring polarity at the terminal block before you connect anything —
you have the multimeter out at that point anyway.

The 500 mA **D24V5F3** is the same family and smaller again, but 500 mA is uncomfortably
close to the ESP32-C3's WiFi transmit peaks. The 1 A part is the right amount of
headroom.

### Be honest about the efficiency itself

At ~100 mA and 3.3 V we are converting about 0.33 W. The difference between a mediocre
75%-efficient module and a good 88% one is roughly **65 mW**, or about **0.6 kWh and
€0.15 a year**. Buy the Pololu for the fixed output, the provenance, the protections
and the soft-start, not for the electricity bill. The bypass-the-LDO decision above is
where the actual efficiency came from, and that one is free.

### For the custom PCB: discrete regulator instead of the module

The module exists only because a bench prototype needs something known-good. On the
PCB, replace it with a **Diodes AP63203** and five passives. This is strictly better
than the Pololu board for our use, not just smaller.

| Ref | Part | Value | Package | Notes |
|---|---|---|---|---|
| U1 | **AP63203QWU-7** | fixed 3.3 V, 2 A, 3.8-32 V in | **TSOT-23-6** | The whole regulator. `Q` = AEC-Q100 Grade 1, see reliability notes |
| L1 | shielded power inductor | **3.3-3.9 uH**, Isat >= 2 A, DCR <= 100 mohm | ~4 x 4 mm | Datasheet table says 3.9 uH, the Diodes EVM uses 3.3 uH |
| C1 | MLCC X7R | **10 uF / 50 V** | 1206 | Input. Shortest possible loop to VIN/GND |
| C2a, C2b | MLCC X5R or X7R | **22 uF / 16 V**, two of them | 1206 | Output. The datasheet specifies 2 x 22 uF |
| C3 | MLCC X7R | **100 nF / 25 V** | 0603 | Bootstrap, BST to SW. Must be ceramic |
| R1 | resistor | **0 ohm** fitted | 0603 | In series with C3. An EMI knob - see below |
| C4 | Al electrolytic | **47-100 uF / 50 V**, 105 C, >=5000 h | SMD V-chip | Bulk and LC damping on the feed from `+U` |
| F1 | fuse | **250 mA** slow-blow or PTC | 1206 | On the `+U` tap. **Protects the intercom from us** |
| D1 | TVS | **SMAJ24A** | SMA | Transient clamp on `VIN` |
| Q1 | P-channel MOSFET | -30 V, low Rds(on) | SOT-23 | Reverse-polarity ideal-diode |

Wiring beyond that is trivial, because the fixed-output variant has its divider inside:

- **`FB` connects straight to `VOUT`.** No divider, no resistors, no tolerance stack.
- **`EN` ties to `VIN`.** The datasheet permits leaving it open, but tying it is
  deterministic and costs nothing. `EN` is rated to 35 V so 13.5 V is fine directly.
- `VIN` -> C1 and C4, `SW` -> L1 -> `VOUT`, C3 from `SW` to `BST`, `GND` to plane.

Nine components including the electrolytic, in roughly 10 x 8 mm.

**Why this part specifically:**

- **22 uA quiescent**, against 200 uA for the D24V10F3 module and 1 mA for the
  D24V22F3. For a node that idles permanently on a shared supply, that is the single
  most relevant number, and it is an order of magnitude better than the module.
- **PFM at light load**, which is the behaviour we care about most.
- **Frequency Spread Spectrum** (±6% jitter) plus a gate-driver scheme that gives a
  ringing-free switching node. This matters more here than in a normal design: the
  regulator will sit millimetres from **capacitive touch pads** and a WiFi antenna.
  Spreading the switching energy instead of concentrating it at one frequency is
  cheap insurance against upsetting either.
- **Fixed 3.3 V** keeps the no-trimpot, no-divider safety argument intact.
- Abs max **35 V DC / 40 V for 400 ms** leaves generous LC-spike margin over 13.5 V.
- 1.1 MHz switching keeps the inductor down to 3.9 uH, hence the small footprint.
- Integrated compensation, 4 ms soft-start, hiccup overcurrent, OVP, OTP.

**Two cautions.**

First, keep the Pololu module for the **bench prototype** and only move to the
AP63203 on the PCB. If the node misbehaves during bring-up you do not want to be
debugging your own regulator and the CAN interface at the same time.

Second, you inherit responsibility for layout. The input capacitor loop must be as
short as physically possible, the `SW` node small, the output caps close, and there
should be copper under the IC for heat. A hand-laid switcher with a sloppy input loop
will radiate, and this one lives inside a device with capacitive touch sensing.

If PFM burst noise ever shows up as a faint whine in the intercom audio, the
forced-PWM sibling is the **AP63201** — adjustable, 500 kHz, no PFM — at the cost of
the light-load efficiency and a divider. Unlikely, but that is the escape hatch.

**Keep the 0 ohm bootstrap resistor footprint (R1).** Diodes' own evaluation board
does this, and it is a free EMI adjustment knob: fitting 10-20 ohm there slows the
high-side turn-on and quiets the switching node, at a small efficiency cost. This node
sits next to **capacitive touch pads**, so having somewhere to back off the edge rate
without redesigning the board is worth an unpopulated part.

### Reliability: what actually decides whether this lasts ten years

This is a permanent install in a sealed plastic box on a wall, wired into shared
building infrastructure. The failure modes that matter are not the obvious ones.

**1. The electrolytic (C4) is the only real wear-out item.** Everything else here is
solid-state or barely operated. Specify **105 C, >=5000 h, from Nichicon / Panasonic /
Rubycon**, at 50 V. Do that and it stops being a concern: capacitor life roughly doubles
for every 10 C below the rated temperature, so a 105 C / 10000 h part running at ~45 C
extrapolates to decades. The bad reputation electrolytics have comes from cheap parts
run hot near their ripple limit, and ours sees almost no ripple current — 100 mA drawn
from a 2 A converter.

A **hybrid polymer** (Panasonic ZC/ZA) is the belt-and-braces upgrade since it has no
electrolyte to dry out. One caveat: its much lower ESR damps the LC ringing less well,
and damping is why an electrolytic was chosen over an MLCC in the first place. If you go
polymer, keep a wet electrolytic or an RC snubber alongside it.

**2. Heat is the master variable, and the efficiency work already paid for itself
twice.** No airflow, and the intercom's own dissipation shares the box. Going straight
to 3.3 V instead of through the SuperMini's LDO removed roughly 200 mW of permanent heat
from inside that enclosure. Since every failure mechanism accelerates with temperature,
that efficiency decision was also a reliability decision.

**3. Take AEC-Q grade where it is nearly free.** The **AP63203QWU-7** is AEC-Q100
Grade 1 (-40 to +125 C), PPAP capable, built in IATF 16949 facilities, with identical
22 uA quiescent and FSS behaviour to the non-Q part. It is usually cents more. The same
logic applies to the passives where a Q-grade or automotive option exists.

**4. Derate.** 50 V ceramics on a 13.5 V rail is 3.7x, which is right. Prefer **X7R over
X5R** for temperature stability, and do not use the smallest available package for a
given value — a larger case has less DC-bias capacitance loss and far less risk of
flex cracking.

**5. The relay is not a wear item at our duty cycle.** It only operates during a
silenced ring, so perhaps ten operations a day at the very worst — around 36,000 in ten
years, orders of magnitude below any signal relay's mechanical rating. Gold-clad
bifurcated contacts also handle the opposite risk, oxidation from sitting unused. Buy
genuine Omron rather than a clone, and note the **unused second pole is a free spare**:
if one ever degrades, move the speaker leg to the other.

**6. Use a genuine Espressif module on the PCB.** SuperMini clones vary enormously in
LDO, antenna tuning and USB connector quality. **ESP32-C3-MINI-1** removes that lottery
and drops the USB connector, which is a mechanical weak point we do not need once OTA
works.

### Three protections for a permanent install

**F1, the fuse, is the important one, and it is not there to protect us.** This node
taps a supply shared by the SCU, the outdoor panel and every terminal in the
installation. If our board develops a short and there is no fuse, it can drag that rail
down and **disable the entire building's intercom** — a failure that is both alarming
and hard to diagnose. A 250 mA slow-blow or a resettable PTC turns our fault into a
local, self-contained one. It costs almost nothing and it is the single most considerate
part in the design.

**D1, the TVS**, clamps transients picked up by building wiring, which can be
substantial on long runs. An SMAJ24A is about twenty cents.

**Q1, reverse-polarity protection.** The AP63203 has none, and neither does the
D24V10F3 module. A P-channel MOSFET wired as an ideal diode is nearly lossless, unlike
a series Schottky, and removes the one irreversible mistake available during
installation.

### The one rule this creates

**Never have USB and `+U` connected at the same time.** Feeding the `3V3` pin
backfeeds the onboard LDO's output. That is common practice and generally harmless,
but with USB also plugged in you have two regulators driving the same node and fighting
each other. Disconnect the `+U` wire before plugging USB in, which is easy because the
first flash happens on the bench and everything after that is OTA.

## Pin map

| Signal | GPIO | Direction | Notes |
|---|---|---|---|
| CAN RX | 20 | in | via 1 k, clamped |
| CAN TX | 21 | out | via buffer, **10 k pull-up to 3V3** |
| Speaker relay | 6 | out | via transistor |
| Status LED data | 7 | out | via 330 R |
| *spare* | 0, 1, 3, 4, 5, 10 | | available if needed |

Unavailable on the C3: **GPIO11-17** are the SPI flash, **GPIO18/19** are the native
USB, and **GPIO2/8/9** are strapping pins best left alone.

## Where to tap on the unit

Everything needed is on the rear-cover screw terminal block: `+U`, `C/D`, `GND`.

**Use the unused `Line OUT` set.** The block has `Line IN` (`+U`, `C/D`, `GND`,
`Vin`) and `Line OUT` (`+U`, `C/D`, `GND`, `Vout`). `Line OUT` exists to daisy-chain
a second terminal; if nothing is chained off this unit, those three screws are free
and you avoid doubling up wires under the live `Line IN` screws.

> Verify first, with the unit **powered off**: check continuity between `Line IN`
> and `Line OUT` for `+U`, `C/D` and `GND`. They should read as shorted pass-through
> pairs. If they do not, use `Line IN` and share the screws.

The speaker taps at **`J101`** on the main board, not at the terminal block.

## Connection diagram

```
INTERCOM TERMINAL BLOCK (Line OUT, unused)
  +U  (~13.5 V) --------------+------------------+
  GND --------------------+   |                  |   (to relay coil, below)
  C/D ---------------+    |   |                  |
                     |    |   |                  |
                     |    |   +--> D24V10F3  VIN  (47-100 uF / 50 V across VIN-GND)
                     |    +------> D24V10F3  GND
                     |               |
                     |               +--> VOUT = 3.3 V --> SuperMini **3V3 pin**
                     |               +--> GND ------------> SuperMini GND
                     |                                      (single common ground)
                     |               SHDN, PG -> leave disconnected
                     |               10 uF ceramic on 3V3 near the ESP32
   ---- CAN RX ----   |
                     +---[ 1k ]---+---------------------> GPIO20
                                  |
                                  +--> BAT54S (series pair), wired as a dual clamp:
                                         common (middle) pin -> this node
                                         one end -> GND    (clamps below 0 V)
                                         other end -> 3V3  (clamps above 3V3)

   ---- CAN TX ----
                              +3V3
                               |
                             [ 10k ]        <-- MANDATORY, see note
                               |
   GPIO21 ---------------------+------> pin 2  A   (input)
                                        pin 5  VCC -> 3V3 (100 nF to GND)
                                        pin 3  GND -> GND
                                        pin 1  N.C. -> leave floating
                                        pin 4  Y   (open-drain output)
                                                      |
                                                   [ 47R ]
                                                      |
                                                      +--> C/D

   ---- SPEAKER RELAY (Silent) ----
   GPIO6 ---[ 1k ]--- base | MMBT2222
                    emitter -> GND
                  collector -> relay coil pin A
                               relay coil pin B ---[ 150R ]--- +U
                                                  (~13.5 V, NOT the 3.3 V rail)
                               1N4148W across the coil ONLY, cathode to the 150R
                               (put the diode across the coil, not across coil+150R)

   Relay pole 1 contacts, spliced into ONE conductor of the JST extension cable:
       cut end towards the board   -> COM
       cut end towards the speaker -> NC
       NO                          -> not connected
   The other conductor passes straight through, uncut.
   De-energised = COM-NC closed = speaker connected = rings normally.

   ---- STATUS LED ----
   3V3 --> WS2812 VDD          (the only rail there is - conveniently correct)
   GND --> WS2812 VSS
   GPIO7 ---[ 330R ]--> WS2812 DIN
```

**The relay coil runs off raw `+U`, not the regulated rail.** The coil current never
passes through the regulator, so it costs no conversion loss, and it keeps a 10 mA
switching step off the 3.3 V rail feeding the MCU. The MMBT2222 is rated 40 V, so
switching 13.5 V on its collector is unremarkable, and the flyback diode keeps it
below ~14.2 V.

**Why the 150 R dropper.** From the Omron datasheet the 12 V coil is **1315 ohm /
9.1 mA / ~100 mW**, and the "150% maximum" figure is an *instantaneous* rating, not a
continuous one. Straight off 13.5 V the coil would sit at 112% of rated voltage and
**139% of rated power**, which is more than it is specified for continuously. A single
150 R in series makes it 12.1 V and 111 mW — essentially nominal — while leaving plenty
of margin over the **9.6 V must-operate** threshold (80% of rated). It costs one 0805
resistor and 14 mW.

In practice the coil is only energised during a silenced ring, so at most a minute at a
time, and it would very likely survive without the resistor. Fit it anyway: it turns
"probably fine" into "in spec".

Contacts are rated **1 A switching / 2 A carry**, comfortably above the few hundred mA
a small speaker draws. Expect a faint click when the contact opens and closes, which is
unavoidable and harmless.

If you can only get a 3 V coil version it will run from 3.3 V, but it draws ~37 mA from
the regulated rail — a large fraction of our total. Prefer the 12 V part. A 24 V coil
will *not* work: 13.5 V is below its must-operate voltage.

Those buffer pin numbers are for the **DBV / DCK** packages of the `SN74LVC1G07`. If
you substitute a different part or package — including the `74LVC1G125` — re-check
against its own datasheet, because the `1G` family does not share one pinout.

For the BAT54S, do not trust anyone's pin numbering including this document — the
`A`/`C`/`S` variants share a package and differ only in internal connection. Put your
multimeter on diode test and find the orientation directly: the **common pin is the
one that reads a forward drop with both other pins**, in opposite directions. It goes
to the signal node, and the end that reads forward *from* it goes to 3V3.

## Three details that will bite if skipped

### 1. The 10 k pull-up on CAN TX is not optional

GPIO21 is a floating input before `setup()` runs, during the listen-only/normal mode
swap, and across every reboot and OTA update. A floating buffer input can drive its
output low, which pulls the bus dominant and **jams the intercom** — no calls, no
door. The pull-up makes "recessive" the default at every instant the firmware is not
in control.

### 2. Do not add a 5 V rail for the status LED

The single-rail design makes this correct by accident, so do not "fix" it later. A
WS2812B run from 5 V wants a data high of about 0.7 x VDD = 3.5 V, which a 3.3 V GPIO
does not reliably reach — the classic cause of intermittent flicker and wrong colours.
Running the pixel from 3V3 puts the threshold at 2.3 V and the problem disappears. It
is marginally below the datasheet's minimum supply and slightly dimmer, which is
irrelevant for a status dot at 35% brightness behind a fibre. SK6812 parts are
explicitly rated for 3.3 V if you want to be strict about it.

### 3. Check what you are doing to the bus supply

The whole installation — SCU, outdoor panel, every terminal — runs off one supply.
Going straight to 3.3 V keeps our draw on `+U` down to roughly **28 mA average**
(~0.38 W), with brief WiFi peaks. Still measure `+U` before and after fitting it, under
load with the screen on, and confirm it has not sagged. If it has, feed the regulator
from its own supply and take only `C/D` and `GND` from the intercom.

The regulator's 2 ms soft-start helps here: it limits inrush so powering up our node
does not disturb the shared bus.

## Assembly order

Each step is safe alone and verifies one thing. Do not skip ahead.

1. **Flash the ESP32 first, on USB alone.** Nothing else connected. Confirm it boots,
   joins WiFi and appears in Home Assistant. Everything after this can go over OTA,
   which is why this step comes first.
2. **Check the regulator, in isolation.** Verify `+U` polarity at the terminal block
   (the D24V10F3 has no reverse-voltage protection), then feed the regulator with
   nothing on its output and measure `VOUT`. It should read 3.3 V ±4%. Only then
   connect it to the SuperMini's `3V3` pin — **and unplug USB before you do.**
3. **RX only.** Fit the 1 k, the clamp and the wire to `C/D`. Leave the TX buffer out
   entirely. Ring the panel and confirm the log shows `0x0DF` `04 03 01 00` and then
   `04 04`, matching the analyzer captures, with "Bus errors" staying at zero. This is
   the bit-timing test.
4. **Add the TX buffer, then stop.** Fit the buffer *and its pull-up*. Before
   transmitting anything, confirm `C/D` still idles at 3.3 V and that the intercom
   still works completely normally — calls, answer, door, screen. This proves the
   node is electrically invisible.
5. **Transmit.** Press "Open door" with the line idle.
6. **Relay last.** Fit the JST adapter, arm Silent, ring, confirm silence, then answer
   and confirm you can hear.

## Permanent install

There is room behind the main PCB inside the case. Insulate everything with Kapton
before reassembly, keep the regulator's inductor away from the touch pads and the
antenna end of the SuperMini clear of metal, and route the fibre so the LED-to-fibre
junction is shrouded in opaque heat-shrink. Confirm the intercom behaves normally with the case
closed — the touch pads are capacitive and dislike conductive things pressed against
them.
