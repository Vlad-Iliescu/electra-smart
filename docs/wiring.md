# Wiring and bill of materials

Bench prototype for the Electra Touch Line `VTM.3S402.ELB04` -> Home Assistant node.
Protocol background is in [reverse-engineering.md](reverse-engineering.md); firmware
is in [../esphome/](../esphome/).

**Guiding principle: nothing on the intercom gets cut, desoldered or permanently
altered.** Power and bus come off screw terminals that are already there, and the
speaker intercept is a plug-in adapter. Everything is reversible by unplugging.

## Where to buy (Romania)

**Mouser RO** can supply the entire BOM in one order — it is an authorised distributor
for Coilcraft, Bourns, Diodes, TI and Omron. That matters more than per-line price:
Mouser and Digi-Key ship from the US, so shipping plus customs handling on a small order
easily exceeds the parts cost, and splitting across suppliers pays that twice.

**Farnell RO** and **RS Romania** ship from inside the EU, which is cheaper and
customs-free for small orders, but carry less of this BOM.

**TME does not stock Coilcraft** (verified — its search returns only the
non-catalogue request form). TME is otherwise good and EU-based, so if the bulk of the
order goes there, switch L1 to the **Bourns SRP4020CC-3R3M** fallback rather than paying
a second shipping charge for one inductor.

**Digi-Key** turned out to be the one carrying both the regulator IC and the Coilcraft
inductor, and it also stocks Omron, TI, Panasonic, Nichicon, Murata and Bourns, so the
whole BOM fits in one order there.

> **Caveat on the inductor at Digi-Key:** `4652-XGL4020-332MEC-ND` is a **Marketplace**
> item sold by *Coilcraft Europe Limited*. That is the manufacturer's own European
> entity rather than a broker, so authenticity is not a concern — but Marketplace items
> **do not consolidate with Digi-Key's own stock**. Expect a separate shipment, a second
> shipping charge, and support handled by the seller. Check that cost at checkout; if it
> is significant, look for the **Bourns SRP4020CC-3R3M** in Digi-Key's own warehouse
> stock instead. The Coilcraft's lower AC loss is real but marginal, and not worth a
> second shipment plus possible customs handling.

**Buy only from authorised distributors.** Searches for these parts surface brokers
(Avaq, Enrgtech, XinYun and similar, usually shipping from Hong Kong). Remarked and
counterfeit passives are common there, which defeats the whole reliability rationale
below. Coilcraft also runs a free-sample programme worth using for prototype quantities.

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
| 2 | **Littelfuse 0453.250MR** | 2410, 250 mA, 125 V | **In line with the `+U` tap, from the very first power-up.** Not just a PCB part - the hand-wired stage is when a mistake is most likely. Solder it inline between two wire ends; buy a spare |
| 1 | 10 k resistor | 0805 | **Mandatory** pull-up on CAN TX |
| 1 | 1 k resistor | 0805 | CAN RX series limit |
| 1 | 47 R resistor | 0805 | CAN TX series limit |
| 1 | 1 k resistor | 0805 | Relay transistor base |
| 1 | 150 R resistor | 0805 | Relay coil dropper, so a 12 V coil sees 12 V on a 13.5 V rail |
| 1 | 330 R resistor | 0805 | WS2812 data line |
| 1 | 100 nF ceramic X7R | 0805, 50 V | Decoupling at the buffer |
| 1 | **Panasonic EEH-ZA1V470P** polymer hybrid | SMD V-chip, 47 uF, **35 V, 105 C 10000 h** | Bulk on `VIN` - see the LC-spike note, and why not an MLCC. The only wear-out part in the design, hence the hybrid |
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
  raises the Q and can make the ringing *worse*. The hybrid specified trades ESR
  (60 mohm, not 360 mohm) for 5x the endurance, and the endurance note shows why that
  costs nothing: F1's series resistance leaves the input LC overdamped regardless.
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
| U1 | **AP63203QWU-7** | fixed 3.3 V, 2 A, 3.8-32 V in | **TSOT-23-6** | The whole regulator. `Q` = AEC-Q100 Grade 1, see reliability notes. Digi-Key `31-AP63203QWU-7CT-ND` (Cut Tape) |
| L1 | **Coilcraft XGL4020-332MEC** | 3.3 uH, **Isat 4.8 A**, Irms 6.6 A, DCR 34 mohm max | 4.0 x 4.0 x **2.1 mm** | AEC-Q200 Grade 1, ultra-low AC loss. Digi-Key `4652-XGL4020-332MEC-ND`, **Marketplace item** - see supplier note |
| C1 | **TDK CGA5L3X5R1H106M160AB** | **10 uF / 50 V**, X5R, ±20% | 1206, 1.6 mm | Input bulk. AEC-Q200, -55/**+85 C**. Digi-Key `445-12883-1-ND`. Shortest possible loop to VIN/GND. See the X5R note |
| C1b | **TDK CGA3E3X8R1H104K080AB** | **100 nF / 50 V**, X8R, ±10% | 0603, 0.8 mm | Input HF bypass, **closer to the pins than C1**. AEC-Q200, -55/+150 C. Digi-Key `445-12606-1-ND`. Present on the official EVM - see note |
| C2a, C2b | **TDK CGA6P1X7R1C226M250AC** | **22 uF / 16 V**, X7R, ±20%, **two of them** | **1210**, 2.5 mm | Output. Datasheet specifies 2 x 22 uF. AEC-Q200, -55/+125 C. Digi-Key `445-5723-1-ND`. **1210, not 1206** - see note |
| C3 | **TDK CGA3E3X8R1H104K080AB** | **100 nF / 50 V**, X8R, ±10% | 0603, 0.8 mm | Bootstrap, BST to SW. Must be ceramic. **Same part as C1b**, so order 2 per board - see note |
| R1 | **Panasonic ERJ-3GEY0R00V** | **0 ohm** jumper fitted, 1 A, 100 mW | 0603 | In series with C3. AEC-Q200, -55/+155 C. Digi-Key `P0.0GCT-ND`. An EMI knob - **also buy 10R (`541-10GCT-ND`) and 22R (`P22GCT-ND`)**, see below |
| C4 | **Panasonic EEH-ZA1V470P** | **47 uF / 35 V**, polymer hybrid, **105 C 10000 h**, ESR 60 mohm | SMD V-chip **6.3 x 5.8 mm** | Bulk and LC damping on the feed from `+U`. AEC-Q200, fails **open**. Digi-Key `P15454CT-ND`. See the endurance note |
| F1 | **Littelfuse 0453.250MR** | **250 mA**, 125 V AC/DC, fast, I2t **15.8 mA2s** | **2410**, 6.1 x 2.69 mm | On the `+U` tap. **Protects the intercom from us.** 50 A breaking, -55/+125 C, UL/CSA. Digi-Key `F5688CT-ND`. Not 1206 and not slow-blow - see note |
| D1 | TVS | **SMAJ18A** | SMA (DO-214AC) | Transient clamp on `VIN`, **fitted behind Q1**. V_C 29.2 V max, matched to C4. Digi-Key `SMAJ18ABCT-ND` - see note |
| Q1 | **Diodes DMP4065SQ-7** | **-40 V**, Vgs ±20 V, 100 mohm max, **-20 A pulsed** | SOT-23 | Reverse-polarity ideal-diode. **AEC-Q101 + PPAP.** Digi-Key `DMP4065SQ-7DICT-ND` (`-7` = tape). Drain to F1, source to `VIN` - see note |
| R3, R4 | **Vishay Dale CRCW0603100KJNEA** x2 | **100 k** ±5%, 0.1 W, 75 V | 0603 | Gate divider for Q1. **Not a plain pull-down** - it halves Vgs so a TVS clamp cannot exceed ±20 V. AEC-Q200, -55/+155 C. Digi-Key `541-100KGCT-ND`. See note |

Wiring beyond that is trivial, because the fixed-output variant has its divider inside:

- **`FB` connects straight to `VOUT`.** No divider, no resistors, no tolerance stack.
- **`EN` ties to `VIN`.** The datasheet permits leaving it open, but tying it is
  deterministic and costs nothing. `EN` is rated to 35 V so 13.5 V is fine directly.
- `VIN` -> C1b then C1 then C4 (smallest nearest the pin), `SW` -> L1 -> `VOUT`,
  C3 from `SW` to `BST`, `GND` to plane.
- **Input chain order is fixed: `+U` -> F1 -> Q1 -> D1 -> C4/C1/C1b -> `VIN`.** D1 must sit
  *behind* Q1. In front of it, reversed wiring would forward-bias the unidirectional
  SMAJ18A into a dead short and blow F1 on a mistake Q1 exists to make harmless.

Fourteen components, no unpopulated positions. The regulator core itself — U1, L1, the four
ceramics, R1 and C4 — fits in roughly 10 x 8 mm; F1, D1, Q1 and the gate divider form a
separate input-protection block ahead of it.

**Per-board multiples, since three positions are easy to under-order:** C1b and C3 are the
same part number, so that is **2 per board**; C2a and C2b are **2 per board**; R3 and R4 are
**2 per board**. Everything else is one. The R1 values are alternatives, not three fitted
parts. Note also that **F1 is consumed by the bench build** before any PCB exists, so buy at
least one more fuse than boards.

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

### Choosing the inductor

**AC loss at the switching frequency is the deciding spec, not DCR and not `Irms`.**

Core loss is roughly independent of load current, so at our ~100 mA average it becomes a
*large* fraction of total converter loss — and this node idles at that load permanently.
Conduction loss, by contrast, is negligible: at 0.1 A even a 145 mohm part burns under
1.5 mW. So the part to buy is the one optimised for low AC loss at ~1 MHz, which is why
the **XGL4020-332MEC** wins. Coilcraft specifies it at 1 MHz, essentially our 1.1 MHz, and
publishes core-loss curves (coilcraft.com/coreloss) so the claim is checkable rather than
marketing. This is also a **reliability** decision: less loss means less permanent heat
inside a sealed wall box, and heat is what ages everything else in there.

`Isat` is the second criterion. It must clear the **IC's peak current limit**, not our
load current, because that is what flows during a short before hiccup mode intervenes;
saturate below it and inductance collapses faster than the controller can react. The XGL
holds 3.5 A even at a conservative 20% inductance drop, and 4.8 A at 30%.

`Irms` — which distributor filters unhelpfully label "maximum DC current" — is the
current for a 40 C temperature rise. It is a *thermal* limit and irrelevant here, since
we draw a fraction of an amp. **Do not filter on it.**

| | **Coilcraft XGL4020-332MEC** | Bourns SRP4020CC-3R3M |
|---|---|---|
| `Isat` (30% drop) | **4.8 A** | 4.0 A |
| DCR max | **34 mohm** | 76 mohm |
| Footprint | **4.0 x 4.0 mm** | 4.45 x 4.06 mm |
| Height | 2.1 mm | **1.8 mm** |
| AEC-Q200 | **Grade 1** | not rated |
| AC loss characterised | **yes, at 1 MHz** | no |
| Price | ~4-6x | 3.38 lei |

The only thing the Bourns wins on is 0.3 mm of height, which is free to give up — C4,
the electrolytic, is 5.8 mm tall, so the inductor is nowhere near the limiting part.
**Bourns SRP4020CC-3R3M is a perfectly good fallback** if the Coilcraft is unavailable;
it is carbonyl composite with soft saturation and its datasheet even lists "low
radiation" and "low buzz noise", both relevant next to capacitive touch pads and inside
an audio device.

Avoid **ferrite** parts such as the SRR5228A-3R3Y. Ferrite saturates abruptly where
composite rolls off gradually, and that part is a cautionary example in its own right:
the highest `Irms` of the obvious candidates at 3.6 A but the *lowest* `Isat` at 2.3 A,
which is at or below the IC's current limit. Filter on the wrong parameter and it looks
like the best of the bunch.

For reference, at 13.5 V in, 3.3 V out, 1.1 MHz and 3.3 uH the ripple is ~0.69 A peak to
peak, so peak inductor current at a 0.5 A load is ~0.84 A. Normal operation uses well
under a quarter of the part's capability; the headroom is entirely for the fault case.

### Choosing the input capacitor (C1 / C1b)

**The 50 V rating is set by the TVS clamp, not by the 13.5 V rail.**

Diodes' own evaluation board uses a **35 V** part here, and against a 13.5 V input that
looks generous. It is the wrong number to design to. During a full-energy surge the
SMAJ18A (D1) clamps at up to **29.2 V** (datasheet: V_RWM 18 V, V_BR 20.0-22.1 V,
**V_C max 29.2 V at I_PP 13.7 A**), and C1 sits directly across that clamp. A 35 V cap
would be left with 5.8 V of margin at the exact moment it is being stressed. At 50 V the
margin is 20.8 V, and the nominal rail gets 3.7x derating, which satisfies the 3x rule
for ceramics in the project's hardware preferences.

Worth noting the clamp is consistent with the IC too: 29.2 V clamped sits comfortably
under the AP63203's 35 V DC absolute maximum, so the same TVS protects both.

**DC bias derating is real but irrelevant here.** Any Class II ceramic loses capacitance
under DC bias, and this part will deliver noticeably less than 10 uF at 13.5 V. It does
not matter, because the datasheet's 10 uF recommendation is sized for a **2 A** load and
we draw about **0.15 A**. The datasheet's own criterion is an RMS rating above half the
maximum load current; the actual input ripple current is

> D = 3.3 / 13.5 = 0.244, so I_rms = I_out x sqrt(D(1-D)) = 0.15 x 0.43 = **~65 mA**

which a 1206 MLCC exceeds by more than an order of magnitude. Do not be tempted to
"compensate" for bias derating by going to 1210 or paralleling more bulk. Fit the
recommended 10 uF, undersized on paper, and it is still enormous margin.

**Add C1b, the 100 nF 0603.** Our earlier BOM had only the bulk cap. The official
AP63203WU-EVM fits a 100 nF / 50 V 0603 at the input *in addition* to the 10 uF, and it
is worth copying: a 1206 has too much ESL to snub the fast dI/dt edges that the bulk cap
cannot follow. Place it **closer to VIN/GND than C1**, with C1 just outside it and the
electrolytic C4 furthest away. On a board that lives millimetres from capacitive touch
pads and a WiFi antenna, cents of HF bypass are the cheapest EMI insurance available.

X7R rather than the EVM's "X5R/X7R" for the usual reason: X5R stops at 85 C and this part
sits inside a sealed box next to a switching regulator.

#### C1 substitutes - only the 50 V is non-negotiable

The X7R `CGA5L1X7R1H106K160AC` was first choice but is frequently out of stock, so the
part actually fitted is **`CGA5L3X5R1H106M160AB`** — X5R instead of X7R, otherwise the same
1206 body, 10 uF, 50 V and AEC-Q200. Reasoning below.

Substituting is low risk provided one rule holds: **keep the 50 V rating**, because C1 sits
directly across the SMAJ18A clamp at up to 29.2 V. Everything else has slack, for the
reasons above — the 10 uF figure is sized for a 2 A load against our 0.15 A, and C4 already
supplies bulk on VIN, leaving this part responsible only for fast dI/dt.

**Beware NRND part numbers.** `C3216X5R1H106M160AB` looks like a fine 10 uF / 50 V / 1206
part on Digi-Key, but TDK lists it as **Production (NRND)** and names
`C3216X5R1H106K160AB` as its replacement. Distributor pages do not surface this. Always
check the status field on TDK's own product page before committing to a part for a
ten-year install.

**Why X5R is acceptable at C1**, despite the project's general preference for X7R:

- X5R holds ±15% only to **85 C** against X7R's 125 C. In a sealed plastic box on an
  interior wall — 25-40 C ambient plus maybe 15-20 C internal rise — this cap sees roughly
  45-60 C. That is 25-35 C of margin: thinner than X7R's ~65 C, but real.
- **Diodes' own evaluation board specifies "X5R/X7R" at this position**, so the IC vendor
  sanctions it.
- Exceeding 85 C causes capacitance *drift*, not failure, on a part already oversized
  roughly sixtyfold against our 65 mA RMS requirement.
- Higher DF (7.5% vs 5%) is thermally irrelevant at 65 mA RMS — sub-milliwatt.

**The real choice is AEC-Q200 with X5R versus commercial grade with X7R.** The X7R options
in 1206 at 50 V (`CL31B106KBHNNNE`, `GRM31CR71H106KA12L`, `C3216X7R1H106K160AC`) are all
commercial. AEC-Q200 wins here: its board-flex, vibration, thermal-shock, humidity and
endurance testing matters far more for a board screwed into a wall box than 40 C of ceiling
we never approach.

**This is now the thinnest thermal margin in the design.** If the unit ever ends up
somewhere hot — direct sun, or a sealed metal enclosure — revisit this part first.

| Option | Part | Trade-off |
|---|---|---|
| Samsung | `CL31B106KBHNNNE` | Exact match, commercial not AEC-Q200 |
| TDK commercial | `C3216X7R1H106K160AC` | Same body and dielectric as the CGA, minus qualification |
| Murata | `GRM31CR71H106KA12L` | Same, third source |
| TDK soft-term | `CGA5L1X7R1H106K160AE` | **Keeps AEC-Q200, adds soft termination**. Farnell only, ~22k stock |
| Two in parallel | 2 x 4.7 uF / 50 V X7R 1206 | Most commodity, slightly lower total ESL |

In practice, filter Digi-Key on 10 uF / 50 V / X7R / 1206 with in-stock and take any
tier-one maker: TDK, Murata, Samsung, Kyocera/AVX, Kemet, Taiyo Yuden.

**Dropping AEC-Q200 here is a smaller compromise than it sounds.** TDK's C-series is the
same ceramic and body as the CGA; the difference is qualification testing and paperwork,
not construction.

**The `AE` suffix is worth understanding**, because it is the one substitution that is an
actual upgrade. `CGA5L1X7R1H106K160AE` is soft-terminated: a conductive resin layer between
ceramic and plating that absorbs board flex. That addresses the same cracking risk noted
for the 1210 output caps, and this board gets screwed into a wall box where it may be
flexed on install. Not worth a dedicated second shipment, but take it if ordering from
Farnell anyway.

### Choosing the output capacitors (C2a / C2b)

**These are 1210, not 1206 — the earlier BOM was wrong, because 22 uF / 16 V / X7R does
not exist in 1206.** This is not a stocking accident. Murata's own press release
announcing the `GCM31CC71C226ME36` calls it the *world's highest capacitance* for a 22 uF
16 V MLCC in 1206, and even that part is **X7S**, not X7R. So insisting on both X7R and
1206 at this value asks for a part nobody makes. TDK's automotive X7R at 22 uF / 16 V is
the CGA6P series in **1210**.

Three ways out, and the trade-off is worth understanding:

| Option | Part | Why not |
|---|---|---|
| 1206, X7R, **10 V** | Murata `GCM31CR71A226KE02L`, DK `490-14439-1-ND` | Only 3.0x derating at 3.3 V, and more bias loss |
| 1206, **X7S**, 16 V | Murata `GCM31CC71C226ME36` | X7S is a looser dielectric, and the part is new and thinly stocked |
| **1210, X7R, 16 V** | **TDK `CGA6P1X7R1C226M250AC`** | **Chosen.** Costs 0.9 mm of width per cap |

The 1210 wins on two counts beyond dielectric grade. First, **a regulator failure puts
the full input rail on the output.** If the AP63203's high-side switch ever fails short,
C2 sees ~13.5 V. That destroys the ESP32 either way, but a 16 V cap survives it while a
10 V cap may fail short and burn — and this box is screwed to a wall in a shared
building. Second, **DC bias derating actually matters on the output**, unlike on the
input: the AP63203 has fixed internal compensation designed around 2 x 22 uF, so loop
behaviour depends on the *effective* capacitance. A 16 V part at 3.3 V bias keeps more of
its nominal value than a 10 V part does, landing closer to what the compensation expects.

The cost is 0.9 mm of extra width each and 2.5 mm of height. Neither binds: C4, the
electrolytic, is 5.8 mm tall and sets the profile on its own.

Stock at the time of writing was 4,044 at Digi-Key and 1,484 at TME, so this is
comfortably sourced, and TME is the EU fallback if Digi-Key runs dry.

### The two 0603 ceramics (C1b input bypass, C3 bootstrap)

**One part number in two positions.** The BOM previously called for 25 V on the bootstrap
cap and 50 V on the input bypass. They are now both the 50 V part, deliberately: 50 V is
required at C1b because it sits behind the TVS clamp, and paying the same few cents at C3
collapses two BOM lines into one, gets a better price break, and removes any chance of
fitting the wrong one. Buy ten of `445-5666-1-ND` and forget about it — 10 cents each at
one, 7.5 cents at ten.

**50 V is genuine overkill at C3, which is fine.** The bootstrap cap sits between `BST`
and `SW`. Its *pin* swings to VIN plus the boot voltage relative to ground, but the
capacitor itself only ever sees the differential boot rail of a few volts, so a 10 V part
would be electrically sufficient. Commonality is worth more than that optimisation.

**One reason not to skimp on it anyway:** the datasheet notes that boot refresh — turning
the low-side switch on for 220 ns to recharge C3 when its voltage falls below 2.3 V —
happens during long periods of non-switching, specifically calling out **PFM at light
load**. That is not an edge case for us, it is our permanent operating point. C3 is the
part that gets exercised most in this design, so a 50 V X7R holding essentially its full
nominal capacitance at a few volts of bias is the right call.

**0603 rather than the project's default 0805** is justified for both positions by the
same clause in the hardware preferences: go smaller when it buys something concrete, here
a tight input loop and a bootstrap cap close to the pins. The official EVM uses 0603 for
both as well.

Murata `GCM188R71H104KA57D`, Digi-Key `490-3277-1-ND`, is an exactly equivalent AEC-Q200
alternative if TDK is ever short.

**On X7R vs the X8R part actually fitted.** Digi-Key flags `CGA3E3X8R1H104K080AB` (X8R) as
an "upgrade" to `CGA3E2X7R1H104K080AA` (X7R). The two are electrically identical — same
100 nF ±10%, 50 V, 3% DF, 5000 MΩ IR, same 1.6 x 0.8 x 0.8 mm body, same AEC-Q200, same
reflow compatibility — differing only in upper limit, **150 C instead of 125 C**, at
roughly 2.3x the price ($0.23 vs $0.10 at one).

That extra 25 C buys nothing here. Inside a sealed box on an interior wall we see maybe
45-50 C, so even X7R carries ~75 C of margin we cannot use. Worth knowing that Digi-Key's
"upgrade" tag is automated — their parametric database flags any part whose every field
meets or exceeds the original, with no knowledge of the application.

**We fitted the X8R anyway, because it was the one in stock and the delta is cents.** That
is the right call: availability beats a preference for a dielectric grade whose only
advantage we do not need. Nothing is compromised by it.

The one parameter not compared between them is the DC bias curve, where X8R formulations
can behave differently. It does not matter at either position — C3 sits at a few volts of
boot rail and C1b is an HF bypass whose exact value is irrelevant — but if this part number
ever migrates to a position where capacitance is load-bearing, check the curve first.

**Keep the 0 ohm bootstrap resistor footprint (R1).** Diodes' own evaluation board
does this, and it is a free EMI adjustment knob: fitting 10-20 ohm there slows the
high-side turn-on and quiets the switching node, at a small efficiency cost. This node
sits next to **capacitive touch pads**, so having somewhere to back off the edge rate
without redesigning the board is worth an unpopulated part.

**Buy the alternate values in the same order.** R1 exists to be swapped, so ordering only
the 0 ohm jumper builds an adjustment that cannot be made without waiting on another
delivery. Take ten each of the same Panasonic ERJ-3GE series so footprint and thermals are
identical:

| Value | Part | Purpose |
|---|---|---|
| **0 ohm** | Panasonic `ERJ-3GEY0R00V`, DK `P0.0GCT-ND` | **Fit this by default** |
| 10 ohm | **Vishay Dale `CRCW060310R0JNEA`**, DK product 1179321 | First step if EMI or touch-pad interference appears |
| 22 ohm | `ERJ-3GEYJ220V` | Further backoff |

The 10 ohm is Vishay rather than Panasonic simply because it was what Digi-Key had in
stock. **Mixing manufacturers across these three is a non-issue.** Verified identical on
every parameter that matters: 0603, thick film, 100 mW, 75 V, ±5%, -55/+155 C, AEC-Q200.
And the point of the part is to compare *values* — a deliberate 10 ohm swamps any
manufacturer-to-manufacturer difference in parasitics, which are fractions of a nH.

Ratings are ample and not worth agonising over. The bootstrap path only replenishes the
high-side gate charge once per switching cycle; at a couple of nC and 1.1 MHz that is a
few **milliamps** average, against a 1 A rated current and 100 mW. (Gate charge is an
estimate - Diodes does not publish Qg for the integrated FET.) Even with 22 ohm fitted,
dissipation stays a small fraction of the rating.

There is also room to *use* this knob: at 13.5 V in and 3.3 V out the duty cycle is only
24%, so C3 has the remaining 76% of every cycle to recharge. Slowing the high-side turn-on
does eat into the bootstrap refresh window, but at this duty ratio there is plenty to
spare.

### Reliability: what actually decides whether this lasts ten years

This is a permanent install in a sealed plastic box on a wall, wired into shared
building infrastructure. The failure modes that matter are not the obvious ones.

**1. C4 is the only real wear-out item, and this is why it is a hybrid.** Everything else
here is solid-state or barely operated.

The plan was a wet electrolytic at ">=5000 h". **That specification cannot be met in this
size.** Every wet 47 uF / 35 V chip can on the market is **2000 h at 105 C** — Nichicon UCD
and UCL, Panasonic FK and FT alike. Capacitor life roughly doubles per 10 C below the
rating, which cuts both ways:

| Cap temperature | 2000 h part | 10000 h part |
|---|---|---|
| 45 C | ~15 years | ~73 years |
| 50 C | **~10 years** | ~51 years |
| 55 C | **~7 years** | ~36 years |

A 2000 h part lands exactly at our ten-year target with no margin, and under it if the box
runs warm. So C4 is a **Panasonic EEH-ZA1V470P** polymer hybrid: same 47 uF, same 35 V,
same 6.3 x 5.8 mm footprint, AEC-Q200, but **10000 h at 105 C**. A drop-in that turns the
one wear-out item into a fifty-year part.

Two further gains. A hybrid holds far less liquid electrolyte, so the dry-out mechanism the
extrapolation models barely applies. And Panasonic specifies its **failure mode as open
circuit** — for a device wired into shared building infrastructure, failing by
disconnecting beats a wet cap that can vent or go leaky.

**The apparent cost is ESR: 60 mohm against 360 mohm**, and damping is why an electrolytic
was chosen over an MLCC to begin with. This looked like it needed a snubber. **It does not** —
the input LC is already overdamped, and an earlier draft of this document was wrong to add
one.

The resonance is the feed inductance against ~54 uF of input capacitance, so f0 lands
between 12 and 50 kHz. Damping factor is `Q = sqrt(L/C) / R`, and R is the whole series loop:
**F1's 0.577 ohm**, Q1's ~0.1 ohm, C4's ESR, plus the wiring:

| Feed | L | Z0 = sqrt(L/C) | Total R | Q |
|---|---|---|---|---|
| 20 cm tap | 0.2 uH | 61 mohm | 0.77 ohm | 0.08 |
| 3 m | 3 uH | 236 mohm | 1.04 ohm | 0.23 |
| 20 m bell wire | 20 uH | 609 mohm | 2.74 ohm | 0.22 |

Critical damping is Q = 0.5, so every case is overdamped: monotonic, zero overshoot. Two
things make this robust rather than lucky:

- **Inductance and resistance scale together in thin bell wire.** The long-run case never
  develops a high-Q resonance, because the same metres that add L add R. Q stays flat
  instead of climbing, which is the opposite of the intuition that long runs are worse here.
- **F1 alone would settle it.** Even deleting the fuse from the sum, Q only reaches ~0.67,
  worth about 7% overshoot on a 13.5 V step.

**Why the snubber that was specified would not have worked anyway**, recorded so it is not
reinvented: it was ~1-2.2 ohm with 100 nF, and 100 nF presents ~70 ohm at 20 kHz against a
resonance of characteristic impedance under 1 ohm. That RC damps MHz-scale edge ringing, a
different phenomenon. An effective snubber at this frequency would need tens of uF — that
is, another electrolytic.

So C4 needs no insurance. **If ringing ever did appear**, the fix is ESR, not an RC: fit a
wet `EEE-FK1V470P`, which shares the identical 6.3 x 5.8 mm land pattern.

Wet fallback if preferred: `EEE-FK1V470P` (Panasonic, 360 mohm, AEC-Q200, 6.3 x 5.8 mm),
understood as a part to replace in a decade. Note ours sees almost no ripple current
regardless — 100 mA drawn from a 2 A converter — so the usual cause of early electrolytic
death, running hot near the ripple limit, does not apply either way.

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
and hard to diagnose. A 250 mA fuse turns our fault into a local, self-contained one. It
costs almost nothing and it is the single most considerate part in the design.

**But "250 mA slow-blow in 1206" is not purchasable, and the 1206 fast part is a trap.**
Slow-blow construction needs thermal mass, so the low end of every 1206 range sits far
above us: Littelfuse `1206SFS` starts at 1.0 A, Bourns `SF-1206SA-W` at 1.5 A, Bourns
`SF-1206SP` time-lag at 500 mA, Schurter `UST 1206` at 7 A. The obvious fallback,
Littelfuse `0466.250NR`, is *very* fast-acting with a melting I2t of only **2.2 mA2s** —
and charging our ~54 uF of input capacitance costs **2-8 mA2s**, so it would open on
power-up, or on the second or third one.

So the current rating was right and the package was wrong. **F1 is a `0453.250MR`, NANO2
453 in 2410**, whose melting I2t is **15.8 mA2s** — seven times the 1206 part, and real
margin over inrush. Three further reasons it is the better body:

- **125 V AC/DC.** The 1206 slow-blow families are 63 V, and some are 24-32 V. D1 can clamp
  to 29.2 V, so those parts would be protecting the board with little margin on themselves.
- **50 A breaking capacity** and -55/+125 C, UL and CSA listed.
- Its **0.577 ohm cold resistance limits the very inrush it must survive**, and costs only
  35 mV and 2 mW at our 60 mA draw.

Derating is comfortable: 60 mA typical, ~120 mA worst case with WiFi transmitting and the
relay energised, against a 250 mA element that wants to stay under 75%. We are at 24-48%,
which matters over ten years because fuse elements age open if run near rating.

**Inrush rests on that I2t margin alone, because soft-start is not available.** The obvious
idea — slew Q1's gate so the FET turns on over milliseconds — **does not work**, for a
structural reason explained under Q1 below: the body diode conducts the inrush before the
channel ever participates. Genuine inrush limiting would need back-to-back FETs and an
ideal-diode controller, which is disproportionate here. The margin is adequate instead
because **this install power-cycles a handful of times in its life**; fuse pulse fatigue
needs repetition to matter, and the fuse's own 0.577 ohm caps the peak.

**Why not the PTC** the plan offered as an alternative: the voltage ratings do not work.
Bourns `MF-MSMF030-2` (300 mA hold) is rated **30 V** against our 29.2 V clamp — 0.8 V of
margin on the protection device itself. Littelfuse `1206L` also tops out at 30 V and its
low-hold variants are 6 V. Reaching a sane 60 V means 1812L or larger, bigger than the
NANO2 anyway, and carrying 3 ohm post-trip resistance plus hold current that derates with
temperature. Decisively, **a PTC trips at about 2x hold**, so a 300 mA device passes 600 mA
of fault current before acting — worse protection for the intercom than a 250 mA fuse,
which is this part's entire purpose. A fuse also fails as a clean, permanent open, the same
property that recommended the hybrid at C4.

**D1, the TVS**, clamps transients picked up by building wiring, which can be
substantial on long runs. About twenty cents.

**Match D1 to C4.** C4 is a **35 V** part, chosen because a 50 V SMD electrolytic at 47 uF
runs roughly 8 mm diameter and 10 mm tall — the largest object in the regulator and awkward
in the space behind the intercom PCB. At 35 V it is **6.3 x 5.8 mm** and still gives 2.6x
derating on 13.5 V.

With a 35 V capacitor, use an **SMAJ18A** rather than an SMAJ24A: the 24 V part can clamp as
high as ~39 V, uncomfortably close to a 35 V capacitor's surge rating, whereas the 18 V part
clamps near 29 V and still will not conduct at the normal rail voltage. That 29 V also sits
under the AP63203's own 35 V absolute maximum, so one TVS protects both. If you ever have
the vertical room, 50 V plus an SMAJ24A is the more relaxed pairing.

**Q1, reverse-polarity protection.** The AP63203 has none, and neither does the
D24V10F3 module. A P-channel MOSFET wired as an ideal diode is nearly lossless, unlike
a series Schottky, and removes the one irreversible mistake available during
installation. The part is a **`DMP4065SQ`**: -40 V, SOT-23, AEC-Q101 with PPAP.

**Orientation: drain to F1, source to `VIN`.** This looks backwards and is not. The body
diode must face *along* normal current flow, because that orientation is what gives the
device a direction to block. At power-up the body diode conducts until the gate is pulled
below the source and the channel shorts it out; on reversed wiring the channel is off *and*
the body diode is reverse-biased, so nothing gets through. Wire it the intuitive way round
and the body diode happily passes reverse polarity, defeating the entire part.

**That is also why gate soft-start is impossible**, correcting the note under F1: the body
diode carries the inrush before the channel does anything, so no amount of gate slewing
limits it. Inrush control needs back-to-back FETs with an ideal-diode controller.

**Why -40 V and not -30 V.** In normal operation Q1 is on and Vds is ~0, so a positive
surge does not stress it — D1 clamps downstream. The stress case is a **line transient
arriving while the wiring is reversed**, where D1 sits behind an open channel and cannot
clamp, leaving most of that transient across drain-source. A -30 V part against a ~29 V
event has no margin.

**The gate needs R3/R4 as a divider, not a plain pull-down to GND.** With the gate tied
straight to GND, Vgs equals the whole rail — and during a clamp that is **-29.2 V against
this part's ±20 V rating**, destroying the device meant to be protecting us. Two 100 k
resistors, source-to-gate and gate-to-GND, halve it: **-6.75 V normally** and -14.6 V at
worst case. Three things make this free rather than a compromise:

- -6.75 V is still well past the -4.5 V point where Rds(on) is specified.
- Rds(on) is irrelevant at our current — 120 mA through 100 mohm is **1.4 mW** — so giving
  up half the gate drive costs nothing measurable.
- 68 uA of divider current is 0.1% of the board's draw, and it avoids adding a gate Zener
  as a separate part number.

The fitted part is **`CRCW0603100KJNEA`** (Vishay Dale, ±5%, 0.1 W, 75 V, AEC-Q200) rather
than the Panasonic equivalent, on stock, and it is the same CRCW family as the 10R bought
for R1. Two loose-looking specifications both turn out not to matter:

- **±5% stacks into the safety-critical number, so check it.** The worst pairing, 95 k over
  105 k, gives -7.09 V normally and **-15.3 V during a full clamp** — still 4.7 V inside the
  ±20 V rating.
- **±200 ppm/K largely cancels.** This is a ratio, and both resistors are the same family on
  the same board at the same temperature, so their drift is common-mode.

Dissipation is 0.46 mW each normally and ~2 mW during a clamp, against 100 mW; each sees
6.75 V against a 75 V working rating.

The pulsed rating is the spec that actually matters: the body diode absorbs the inrush
spike, roughly 8 A for tens of microseconds. At about 0.65 mJ that is ~25 C of transient
junction rise against a **-20 A pulsed** limit and a 9.8 mJ avalanche rating.

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
