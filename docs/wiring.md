# Wiring and bill of materials

Bench prototype for the Electra Touch Line `VTM.3S402.ELB04` -> Home Assistant node.
Protocol background is in [reverse-engineering.md](reverse-engineering.md); firmware
is in [../esphome/](../esphome/).

**Guiding principle: nothing on the intercom gets cut, desoldered or permanently
altered.** Power and bus come off screw terminals that are already there, and the
speaker intercept is a plug-in adapter. Everything is reversible by unplugging.

The one place this may have to bend is the speaker, and only if the intercom's 1.25 mm
connector turns out to be a family the kit cannot mate. The [fallback](#if-the-factory-plug-does-not-mate)
trades two solder joints on the speaker for certainty about the fit. It is opt-in at assembly
time and does not change the board at all, so treat the principle as intact unless the
fit-test says otherwise.

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

**Everything is SMD except the two modules**, which only exist as modules. Passives ended
up **0603 for everything except the bulk capacitors**, which are 1206 and 1210. Earlier
drafts said 0805 as the comfortable default; standardising on the Vishay `CRCW0603` family
was worth the smaller size because it means **one resistor family across bench and PCB**,
no duplicate purchase, and AEC-Q200 parts throughout. Hot air and a preheat plate are
available, so nothing finer is off the table either.

**Buy quality, not cheap.** This is a permanent install that should outlive several
phone upgrades, and the entire bill of materials is around EUR 50 at good-part prices —
there is no meaningful saving available by economising. Genuine Omron relay, genuine TI
or Nexperia logic, named-brand capacitors. See the reliability notes in the power
section for which choices actually matter and which are theatre.

| Ref | Qty | Part | Package | Purpose |
|---|---|---|---|---|
| **U3** | 1 | **ESP32-C3 SuperMini** | module | The node. Small enough to hide behind the PCB. `ESP32-C3-MINI-1` takes this designator on the PCB |
| - | 1 | **Any 12->3.3 V buck module** | **prefer fixed output**, >=300 mA | Bench stage only, so no designator - it stands in for the whole `U1` block. Reference part is the Pololu D24V10F3 (#2830), but any module does. **Buck, not linear** - a linear would burn 0.6 W in a sealed box. **If adjustable, meter it at 3.3 V before it touches the 3V3 pin** - see the one rule below |
| **U2** | 1 | **SN74LVC1G07DBVR** (TI) | **SOT-23-5 (DBV)** - not SC-70 | Open-drain CAN TX driver. Package matters, see below |
| **K1** | 1 | **Omron G6K-2F-Y DC12** | **SMD gullwing**, DPDT, gold bifurcated contacts | Speaker cut for Silent. `F` in the part number *is* the surface-mount terminal code. Coil **1315 ohm / 9.1 mA / ~100 mW**. Add `-TR` for tape, else 50-piece tube |
| **Q2** | 1 | **onsemi BCW65ALT1G** | SOT-23 | Relay coil driver. **NPN, not a MOSFET** - see note. Vceo 32 V / Vces 60 V, Ic 800 mA, **hFE >=75 at Ic = 10 mA** which is our exact operating point |
| **D2** | 1 | **1N4148W** | **SOD-123**, or SOD-123F if that is what stock offers | `K1` coil flyback. `W` = SOD-123, `WS` = smaller SOD-323. **Check which you actually received** - see the footprint note |
| **D3** | 1 | **onsemi BAT54SLT1G** | SOT-23, *series* pair | Clamps the CAN RX pin to the rails. 30 V, 200 mA, Vf **0.32 V max at 1 mA**, Ct 10 pF. **If `SBAT54SLT1G` is also in stock take that instead** - leading `S` = AEC-Q101 + PPAP, same die, see note |
| **LED1** | 1 | **`WS2812B`**, ideally `V6` | SMD single pixel, **3535 `MINI`** or 5050 | Status LED. **3.3-5.5 V, so in spec on our rail** - and `V6` specifically optimises constant-current drive at 3.3 V. **Not an `SK6812`** (3.5 V / 3.7 V) and **not `WS2812E`/`S`** (3.8 V). Take the `B` over the `C` for its internal cap and reverse-connection protection. **Not a distributor part**: AliExpress or similar, buy a handful and bench-check one - see the LED note |
| **SW1** | 1 | **Side-actuated SMD tact switch, 7.8 x 3.5 x 3.8 mm, _with bosses_** | 4-pad gullwing + 2 locating bosses | Mode button. Functionally a **CTS `225BM...RB1(S)`**, whose datasheet supplied the land pattern. From the AliExpress assortment take **variant No.5** and make sure it is a *with points* version - the bosses are what carry the side press. **Not a distributor part**: buy the 50-piece lot, and see the switch note for why the bossed variant is not optional here |
| **J3** | 1 | **"JST 1.25" 2-pin SMD vertical header** | board-mount | **The speaker's factory plug goes here** if it mates, and a plug crimped from the same kit if it does not. From the 10-set AliExpress kit; footprint is drawn from the vendor sheet, so **fit-test one against the speaker plug to settle the topology**, not the land pattern |
| **J2** | 1 | **"JST 1.25" 2-pin housing + 2 terminals** | crimped, from the same kit | Flying lead from our board to the intercom's `J101`. **Crimped with the Engineer PA-09**, which is on hand - nothing extra to buy. Use the **28 AWG** end of the wire, not 26 - see the crimping note. The board end has no connector: the wires solder into plated holes with a feed-through strain relief, so nothing extra is needed there either |
| **F1** | 2 | **Littelfuse 0453.250MR** | 2410, 250 mA, 125 V | **In line with the `+U` tap, from the very first power-up.** Not just a PCB part - the hand-wired stage is when a mistake is most likely. Solder it inline between two wire ends; buy a spare |
| **R4** | 1 | 10 k resistor `CRCW060310K0JNEA` | 0603 | **Mandatory** pull-up on CAN TX |
| **R8** | 1 | 10 k resistor, same part as R4 | 0603 | Base-to-emitter on `Q2` - see the Vces note |
| **R11** | 1 | 10 k resistor, same part as R4 | 0603 | Pull-up on `SW1`, so the button reads active low. **With R4 and R8 that makes this part 3 per board** |
| **R6** | 1 | 1 k resistor `CRCW06031K00JNEA` | 0603 | CAN RX series limit |
| **R7** | 1 | 1 k resistor, same part as R6 | 0603 | `Q2` base. **So this part is 2 per board** |
| **R5** | 1 | 47 R resistor `CRCW060347R0JNEA` | 0603 | CAN TX series limit |
| **R12** | 1 | **240 R resistor `CRCW0603240RJNEA`** | 0603 | **Gated recessive assist on `C/D`, and the part without which this node cannot transmit at all.** Value is measured on this building's bus, not chosen - see the `R12` note before substituting. **Buy this even if you already have 330 R and 1 k**, and do not fit those instead |
| **R9** | 1 | 150 R resistor `CRCW0603150RJNEA` | 0603 | `K1` coil dropper: 13.5 V across 1315 + 150 ohm draws 9.2 mA, so the 12 V coil sees **12.12 V** |
| **R10** | 1 | 330 R resistor `CRCW0603330RJNEA` | 0603 | `LED1` data line. Buy 2 if you want the two-plain-LED fallback available - at **(3.3 - 2.0) / 330 = 3.9 mA** it doubles as their series resistor |
| **C7** | 1 | 100 nF ceramic | 0603, 50 V | Decoupling at `U2`. **Same part as C2, C5 and C9** (`CGA3E3X8R1H104K080AB`), so that part is **4 per board** in total |
| **C9** | 1 | 100 nF ceramic, same part as C7 | 0603, 50 V | Debounce and ESD shunt across `SW1`, which is the one node deliberately exposed to a finger through the housing |
| **C6** | 1 | **Panasonic EEH-ZA1V470P** polymer hybrid | SMD V-chip, 47 uF, **35 V, 105 C 10000 h** | Bulk on `VIN` - see the LC-spike note, and why not an MLCC. The only wear-out part in the design, hence the hybrid |
| **C8** | 1 | 10 uF ceramic | 1206 | On 3V3 next to `U3`, for WiFi bursts. **Same part as C1** (`CGA5L3X5R1H106M160AB`), so that part is **2 per board**. Its 50 V rating means almost no DC-bias derating at 3.3 V, so you get a true 10 uF |
| **J1** | 1 | **"JST 1.25" 3-pin SMD vertical header** + housing + 3 terminals | board-mount, from the **3P** variant of the same kit | `+U`, `C/D`, `GND` tap. Same family as `J2`/`J3`, so one crimp tool and one technique covers every connector on the board. **The 3P variant is a separate order**: the listing sells one pin count per purchase, so the 2P order that covers the speaker end does not include these |
| - | - | 26-28 AWG silicone wire | | Thin and flexible; there is not much room |
| - | - | Kapton tape, heat-shrink | | Insulating the install |
| - | - | 2 mm end-glow PMMA fibre | + opaque heat-shrink | Light pipe to the case face (later) |

**Do not buy a differential CAN transceiver** (TJA1051, SN65HVD230, MCP2551). This
bus is single-wire; those parts need CANH/CANL and will not work.

### Designator map, and what to type into Digi-Key's Customer Reference

Digi-Key prints the **Customer Reference** field on the bag label, so filling it in is the
difference between a labelled parts drawer and twenty identical anti-static bags of black
SOT-23s. Fill it in for every line. The full allocation:

| Block | Designators |
|---|---|
| Regulator | `U1` buck, `L1`, `C1` in, `C2` in bypass, `C3`/`C4` out, `C5` bootstrap, `R1` bootstrap series, `C6` bulk |
| Input protection | `F1` fuse, `Q1` reverse-polarity P-FET, `R2`/`R3` gate divider, `D1` TVS |
| CAN interface | `U2` buffer, `R4` TX pull-up, `R5` TX series, `R6` RX series, `R12` recessive assist, `D3` RX clamp |
| Relay / Silent | `K1` relay, `Q2` NPN, `R7` base, `R8` base-emitter, `R9` coil dropper, `D2` flyback |
| Indicator | `LED1`, `R10` data series |
| Mode button | `SW1` side-push switch, `R11` pull-up, `C9` debounce |
| MCU | `U3`, `C7` buffer decoupling, `C8` 3V3 bulk |
| Connectors | `J1` intercom tap, `J2` speaker in, `J3` speaker out |

**There are no gaps in the sequence, and the designators changed on 12 Aug 2026.** KiCad
cannot represent references like `C1b` or `C2a`, so the whole scheme was collapsed to plain
integers to match `pcb/board/board.kicad_sch`. An earlier revision also left `R2` and `C5`
unused — they were an input RC snubber, dropped once the damping calculation showed the fuse
resistance and wiring already overdamp the input LC — and both were reused by the renumber.
**If you are reading an older revision or an older Digi-Key label, its designators will not
match this table.** The translation is:

| Old | New | Part |
|---|---|---|
| `C1` | `C1` | 10 uF input bulk |
| `C1b` | `C2` | 100 nF input bypass |
| `C2a`, `C2b` | `C3`, `C4` | 22 uF output pair |
| `C3` | `C5` | 100 nF bootstrap |
| `C4` | `C6` | 47 uF hybrid bulk |
| `C6` | `C7` | 100 nF buffer decoupling |
| `C7` | `C8` | 10 uF 3V3 bulk |
| `R1` | `R1` | 0 R bootstrap series |
| `R3`, `R4` | `R2`, `R3` | Q1 gate divider |
| `R5` | `R4` | CAN TX pull-up |
| `R6` | `R5` | CAN TX series |
| `R7` | `R6` | CAN RX series |
| `R8` | `R7` | Q2 base |
| `R9` | `R8` | Q2 base-emitter |
| `R10` | `R9` | coil dropper |
| `R11` | `R10` | LED data series |

Everything else — `U1`-`U3`, `L1`, `D1`-`D3`, `Q1`, `Q2`, `F1`, `K1`, `J1`-`J3`, `LED1` —
kept its designator.

**The mode button was added after that renumber**, so `SW1`, `R11` and `C9` appear in no
older revision and in none of the Digi-Key orders placed on 12 Aug. `R11` and `C9` are
extra pieces of two part numbers already on the list, so they change the quantities in
the table below rather than adding lines to it; only `SW1` is a genuinely new purchase,
and it does not come from Digi-Key.

**`R12` was added later still**, on 25 Aug 2026 during transmit bring-up, and its value
was settled on 28 Aug. It is a genuinely new Digi-Key line — 240 R is not otherwise on
the board — and it appears in no order placed so far. It is also **not optional**: with
it absent the node receives perfectly and cannot transmit at all.

**Three lines need a compound reference, and it is easy to get wrong** because one part
number serves more than one position:

| Part number | Reference to enter | Per board |
|---|---|---|
| `CGA3E3X8R1H104K080AB` (100 nF) | `C2,C5,C7,C9` | **4** |
| `CGA5L3X5R1H106M160AB` (10 uF) | `C1,C8` | **2** |
| `CGA6P1X7R1C226M250AC` (22 uF) | `C3,C4` | **2** |
| `CRCW060310K0JNEA` (10 k) | `R4,R8,R11` | **3** |
| `CRCW06031K00JNEA` (1 k) | `R6,R7` | **2** |
| `CRCW0603100KJNEA` (100 k) | `R2,R3` | **2** |

And **the three `R1` candidates should not all be labelled `R1`**, or you will end up with
three identically-labelled bags holding 0 R, 10 R and 22 R. Use `R1 FIT 0R`,
`R1 ALT 10R` and `R1 ALT 22R`. Only the 0 R is fitted; the other two are the EMI knob.

### What was actually ordered, 12 Aug 2026

**Every designator is covered.** The buy landed as three orders, and the cart builds
**5 complete boards** — limited simultaneously by `U1`, `L1`, `C3`/`C4`, `F1`, `Q1`, `K1`,
`R2/R3`, `R4/R8` and `R6/R7`, all at exactly five sets. The 0603 resistors, `D1`-`D3`,
`U2`, `Q2` and the 10 uF run to ten.

| Order | Contents | Cost |
|---|---|---|
| Digi-Key #100930216 | 23 lines, `U1` through `Q2` | 400.01 lei |
| Digi-Key #100930214 | `L1` alone — the Marketplace split the caveat predicted | 61.70 lei |
| LCSC | `LED1` **`WS2812B-V6`** x100, plus 0805 100 nF bench stock | $10.57 |
| AliExpress | 1.25 mm connector kit — **see the caveat below** | 66.64 lei |

**`LED1` came out better than specified.** LCSC lists `C52917433` explicitly as
**`WS2812B-V6`** from Worldsemi, so the revision is confirmed on the invoice rather than
guessed at — which was the one real risk in the LED note. The bench check is still worth
doing, but the part is now known to be the revision whose PCN claims constant-current drive
at 3.3 V, not a lottery ticket from a marketplace listing.

**Two substitutions arrived through the order rather than by choice.** Neither is a problem,
but both differ from what this document names:

- **`U2` is a `UMW` part, not TI.** Digi-Key carries UMW as a legitimate line, so this is a
  second-source brand bought through an authorised distributor rather than a broker
  counterfeit — the risk the sourcing note warns about does not apply. It is still not TI
  silicon. For an open-drain buffer toggling at 11.4 kbps the electrical demands are close
  to trivial, so the exposure is low; just expect different top marking from the TI
  datasheet, and keep one of the ten as a known-good spare.
- **`K1`'s manufacturer reads "Aratas (Formerly Omron Components)".** That is the genuine
  article. Omron divested its Electronic Components business and it now trades as Aratas;
  the part number, dies and datasheet are unchanged. No action.

**The LCSC 0805 100 nF has nothing to do with this project.** It was a long-standing
backorder that the `LED1` purchase made a convenient moment to clear. Recorded here only so
that nobody later mistakes it for `C2`/`C5`/`C7`, which it must not be used for: wrong
package for a layout drawn around 0603, X7R rather than X8R, and the Yageo `CC` series is
not AEC-Q200.

Still outstanding:

| Ref | Part | Status |
|---|---|---|
| `U3` | ESP32-C3 SuperMini (bench), `ESP32-C3-MINI-1` (PCB) | Owned / later |
| - | 26-28 AWG silicone wire, Kapton, heat-shrink, 2 mm PMMA fibre | Consumables |

**The AliExpress 1.25 mm kit covers both speaker connectors outright.** The *2P, SMD
Vertical* variant is a board-mount header plus housings and loose terminals, which is exactly
what the arrangement below needs. The vertical header becomes `J3` and **the speaker's own
factory plug mates straight into it**, so nothing is crimped on the speaker side at all; the
`J101` end is a housing and two terminals crimped onto a flying lead, and **the Engineer
PA-09 needed for that is already on hand**. See the speaker connector section for the fit-test
that decides how the speaker gets attached.

**`J1` uses the same family in its 3-way form, and that is a second order to place.** The
listing sells one pin count per purchase, so a 2P order covers the speaker end only and contains
nothing that fits the intercom tap. Everything else on the BOM is bought.

The listing is *10sets MICRO JST 1.25 2/3/4/5/6/7/8/9/10 Pin Connector 1.25MM Pitch Vertical /
Horizontal SMD Pin Header + Housing + Terminal*, and its stated contents — ten receptacles, ten
housings and the matching loose terminals per set — confirm that one order covers both
connectors several times over. What it never states is the **family**. It says only "JST 1.25",
gives no current, voltage or AWG rating, and the only mechanical figure it publishes is a
**4.25 mm** body for the 2-way part.

**The vendor datasheet in [datasheets/](datasheets/) settles it: this is not JST GH.** Its own
table gives the 2-way header a 4.25 mm body where genuine GH measures 5.75 and PicoBlade 7.65.
Look at how the body scales and the family becomes obvious — the kit's body is always the pin
span **plus 3.0 mm**, which is precisely JST SH's proportion (SH 2-way is 4.00 mm on a 1.00 mm
pitch), where GH adds 4.5 mm and PicoBlade 6.4 mm. So the part is an **SH-shaped connector
scaled to a 1.25 mm pitch**, which is exactly the "LiPo balance lead" clone the section above
warns about, and it is unlikely to intermate with either genuine family.

That has a consequence beyond the footprint: it makes the fit-test against the intercom a
genuine coin-flip rather than a formality, so the [fallback](#if-the-factory-plug-does-not-mate)
is now the more probable path rather than a contingency.

> **Trap in that datasheet, for whoever reads it next.** Both its drawings and its photo bracket
> the *outermost* span and label it "A", which invites you to read A as the overall length. It is
> not. The table's A column is exactly (n-1) x 1.25 on all fifteen rows, which can only be the
> pin span, so **A is the pin span and B is the body length** and the artwork's letters are
> shifted against its own table. Trust the arithmetic, not the brackets.

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
- **For prototyping**, either a small SMD-footprint protoboard or a SOT-23-5 breakout
  adapter for the buffer. The only genuinely fiddly part is the buffer.
- **All resistors are 0603 in the Vishay `CRCW0603` family**, `J` tolerance, AEC-Q200. An
  0805 assortment book is the easier option for hand-wiring, but buying the five values in
  the same family as R1/R2/R3 means **one part family across bench and PCB**, no duplicate
  purchase, and automotive-grade parts throughout for about 0.14 lei each.
- **Three capacitor positions are shared part numbers, which is easy to under-order.** The
  100 nF `CGA3E3X8R1H104K080AB` serves C2, C5 *and* the buffer decoupling — **3 per
  board**. The 10 uF `CGA5L3X5R1H106M160AB` serves C1 *and* the 3V3 bulk — **2 per board**.
  The designator map above lists all of them.
- **Check which `1N4148W` package actually arrived.** The Digi-Key part `1N4148WRHG` is
  **SOD-123F**, not the SOD-123 this document originally specified. Electrically identical
  and equally hand-solderable, but SOD-123F has **flat leads and a different land pattern**,
  so it needs the matching footprint on the PCB. Harmless now, a rework later if `D2` gets
  drawn from the wrong library.
- **When the custom PCB comes**, the two modules are what to replace: the SuperMini
  becomes an **ESP32-C3-MINI-1** castellated SMD module, and the regulator becomes a
  discrete **AP63203** design — see the regulator BOM in the power section below.

Buy the SC-70 and SOT-23 parts in threes. They cost the same as one, and they are
small enough that losing or cooking one is a matter of when, not if.

### The speaker connector

**The speaker plugs into our board, and our board reaches back to `J101` on a flying
lead.** Earlier drafts had this as a cut-in-half extension cable with the relay contact
spliced into one conductor. The revised arrangement is better in every respect:

```
   intercom J101 (male header)
        |
        |  J2 = 2-pin female housing, terminals crimped with the PA-09,
        |       free wire ends soldered to our board
        v
   [ OUR BOARD ]   relay K1 pole 1 sits in ONE conductor as a PCB trace:
        |            J2 pin 1 --> COM,  NC --> J3 pin 1,  NO unused
        |            J2 pin 2 -----------------> J3 pin 2 straight through
        v
   J3 = 2-pin JST 1.25 SMD vertical header on our board
        ^
        |
   the speaker's own factory plug
```

Four things this buys. **No crimping on the speaker side** — the speaker keeps its factory
plug and simply moves from `J101` to our `J3`. **The relay contact becomes a PCB trace**
rather than a hand-splice in a thin cable, which removes the least reliable joint in the
whole build. **Only one connector needs making**, the `J101` end, and with the kit's
housings and terminals plus the PA-09 that needs nothing bought. And **reversibility is
unchanged**: pull our board out, plug the speaker's factory plug straight back into `J101`,
and the unit is stock again.

**Crimping notes, since the tool is on hand.** The PA-09 is the right choice for this pitch —
it covers 0.1-0.5 mm² open-barrel terminals, which is precisely the JST SH/GH/PicoBlade
range. Three things decide whether the joint is trustworthy:

- **Use 28 AWG, not 26.** Generic "JST 1.25" terminals take roughly 28-32 AWG. Genuine JST
  GH stretches to 26, but on a no-name terminal 26 AWG risks a barrel that will not close
  properly around the conductor. The BOM's 26-28 AWG silicone wire covers this — pick the
  thin end.
- **Strip 1.5-2 mm** so the front wings take the conductor and the rear wings take the
  insulation. Insulation caught in the conductor wings is the classic intermittent crimp.
- **Tug-test every terminal** before it goes into the housing. There are ten sets in the kit,
  so practise on a spare pair first and sacrifice a couple to find the die slot that gives a
  clean closed barrel. This joint ends up sealed inside a wall, which is the wrong place to
  discover a weak crimp.

Two consequences to design around. Our board now carries the speaker's mechanical strain,
so it needs securing rather than just being tucked in. And the speaker pair now crosses the
PCB, so **route it as a pair, away from `L1` and the `SW` node** — the pair is low impedance
and driven by an amplifier so it is not especially susceptible, but there is no reason to
run audio under a 1.1 MHz switching node.

**The one test that decides the topology.** 1.25 mm is not a single family:
genuine JST GH, Molex PicoBlade and the cheap "JST 1.25" sold for LiPo balance leads share
the pitch but differ in latch and polarisation, and **do not reliably intermate**. This now
matters more than it used to, because the speaker's factory plug has to mate with *our*
header rather than with a bought cable. There are ten sets in the kit, so **take one
vertical header and try the speaker's plug on it by hand.** If it seats and latches, the plug-in
arrangement above stands. If it does not, **do not go hunting for the matching family** — take the
fallback below instead, which needs no new parts and no identification at all. Either way the
footprint is unaffected, because `J3` is the kit's own header in both arrangements.

Expect this one to fail, incidentally. The vendor sheet shows the kit is an SH-proportioned clone
rather than genuine GH, so it will only mate the intercom if the intercom uses the same clone
family — plausible for a Chinese-built unit, but no better than a coin-flip.

And confirm the pitch itself first, since the ~1.08 mm pin-centre reading was never
conclusive — that is exactly the error you get with the caliper jaws inside the pin centres.
Measure the **length of the header body on the intercom's board** instead, which is a far
easier reading to take than a two-pin span. These are the real numbers for a 2-way header,
pulled from KiCad's footprints and therefore from the manufacturers' own drawings:

| Family | Pitch | 2-way body length |
|---|---|---|
| JST SH | 1.00 mm | **4.00 mm** |
| JST GH | 1.25 mm | **5.75 mm** |
| JST ZH (`B2B-ZR-SM4-TF`) | 1.50 mm | **6.00 mm** |
| Molex PicoBlade | 1.25 mm | **7.65 mm** |

**Read that table for what it does and does not settle.** It separates the two parts most
likely to be confused here superbly: GH and PicoBlade are both 1.25 mm pitch yet differ by
nearly 2 mm of body, so a caliper tells them apart at a glance. It is nearly useless for GH
against ZH, which differ by 0.25 mm — less than the error of measuring moulded plastic in
situ — so if the reading lands anywhere near 5.75-6.00 mm the pin span has to break the tie
after all.

An earlier version of this section claimed ~4.2 mm meant 1.0 mm SH, ~5.0 mm meant 1.25 mm and
~5.6 mm meant 1.5 mm ZH. Only the first was close. The others were wrong in the dangerous
direction, because a genuine GH header reads **5.75 mm** and those numbers would have had it
misread as ZH — sending us off to re-buy an entire kit in the wrong pitch.

If it does turn out to be 1.0 mm SH, the kit is the wrong pitch outright and both `J2` and
`J3` need re-buying — which is the whole reason to measure before the PCB is drawn.

#### If the factory plug does not mate

Worth reading *before* the unit is opened, because it changes what the fit-test means: a
failure stops being a blocker and becomes a choice. **Reuse the factory plug where it already
fits, and move the soldering to the speaker instead.**

```
   intercom J101 (male header)
        |
        |  the speaker's own factory lead - plug left untouched in J101
        |
   J2 = that lead's far end, desoldered from the speaker
        and soldered into our board's plated holes
        |
   [ relay contact, as a PCB trace ]
        |
   J3 = 1.25 mm SMD vertical header on our board
        ^
        |  a new lead, both ends ours: kit housing crimped with the PA-09
        |
   soldered to the speaker's terminals
```

This eliminates **both** unknown matings in one move. The `J101` end keeps the factory plug in
its factory socket, so that fit is guaranteed and the crimp is the OEM's rather than ours —
worth something on the one joint carrying the audio, since a cheap terminal in an OEM housing
is exactly where contact force goes marginal. And `J3` mates a plug from the same kit as its
own header, so that fit is guaranteed by construction. Nothing has to be identified or matched.

**Desolder the factory lead, never cut it.** That is the difference between a reversible
modification and a one-way door. Desoldered, the lead stays one intact piece and reverting is
just moving two joints back onto the speaker tabs. Cut, restoring stock needs either a splice
or a `J101`-compatible plug — the exact unknown this arrangement exists to avoid.

**The hazard is the speaker tabs, not reversibility.** On small dynamic drivers the voice
coil's tinsel lead is usually soldered to the same tab, and cooking it turns this into "source
a replacement OEM speaker". Low temperature, quick in and out, add fresh solder to wet the
joint rather than dwelling, and put no pull on the tab.

**Check the factory lead reaches first**, because this flips which lead constrains board
placement. In the plug-in arrangement the fixed-length factory lead spans our board to the
speaker and our crimped lead can be any length; here the factory lead has to span `J101` to
our board and the new lead is the flexible one. If it will not reach, the splice needed to
extend it hands back the reliability this was bought for, and the plug-in arrangement is the
better bet.

Serviceability is unchanged either way — pulling the board is still unplug at `J101`, unplug
the speaker at `J3`, and the factory lead comes out still soldered to our board. That is also
why `J3` stays a connector even though the speaker is being soldered anyway: that plug is what
lets the board come out without touching the speaker a second time.

**The board is identical under both arrangements**, which is what makes this safe to defer.
`J3` is the kit's header in either case — if the kit mates the factory plug the plug-in
arrangement works, and if it does not this one does — so the footprint is a superset and the
layout is not blocked on the fit-test at all. The decision to desolder can be made later, with
the unit open and the parts in hand.

### The board end of the speaker lead

`J2`'s two wires **solder straight into the board**, with no connector. That is not a
compromise: the lead is already removable at the other end, where a crimped plug mates with
the intercom's `J101`, so a second connector here would add a failure point and eat scarce
space to make removable something that already is.

**They land in plated through holes, not on SMD pads, and the reasoning is worth recording
because the instinct to stay all-SMD is strong and wrong here.** A wire soldered to an SMD
pad is held only by the copper's peel strength off the laminate, so any bending moment at the
joint works to lift the pad clean off. A plated hole puts that load into the barrel and both
annular rings instead. And nothing is gained by staying SMD, because **this joint is hand-made
either way** — no stencil, no paste, no placement and no reflow ever touches it. The only
thing "keeping it SMD" would buy is the absence of a drilled hole, and the design needs holes
here regardless for the strain relief, so the plated version is free at fab.

KiCad's library is a blunt witness on this. `Connector_Wire.pretty` exists for exactly this
job and contains **330 footprints, every one through-hole**, without a single `attr smd`
among them.

**The strain relief is a feed-through, not a cable tie**, which was the other tempting option.
The wire threads down through its own Ø2.0 mm hole, runs along the far face for 9 mm and comes
back up into the solder hole, so the board is clamped between two runs of wire. Three reasons
that wins over a tie in this build: it adds **zero height**, where a tie head is a bulky
2-3 mm on a board that has to disappear behind the intercom's own PCB; nylon **creeps** when
warm and this box is sealed and permanent, so a tie that is snug now may not be in five years;
and it needs **no extra part** to lose or forget. A standard 2.5 mm tie would also need holes
bigger than Ø2.5 mm to thread, which is more board than the relief holes cost.

Assembly order matters, and it is the opposite of the obvious one: **thread both wires through
the relief holes first, then trim and solder.** Solder first and the relief holes become
unusable without desoldering. Strip only what the barrel needs, so no bare conductor is left
in the channel between the two.

### The mode button

`SW1` cycles the unit through its states from the outside, so it has to be reachable
without opening the intercom. That means it sits **at a board edge, pressed sideways
through a hole in the housing wall** — which in turn means a *side-actuated* switch,
whose plunger fires parallel to the board rather than perpendicular to it.

**Take the variant with locating bosses.** Side actuation pushes the part in exactly the
plane that peels SMD pads, and every press for the next ten years lands there. The bossed
version drops two 0.7-0.8 mm posts into holes in the board, so the press force goes into
the board instead of into four solder joints; the pad-only version is the same switch with
nothing resisting that load. The seller distinguishes the two as *with points* and
*nopoints*, and only the former is acceptable here.

**The part is a CTS Series 225B in all but the label.** The AliExpress listing gives no
manufacturer and its own drawing is a low-resolution JPEG, but the form factor — 7.8 x 3.5
mm, gullwing, side actuating, offered with and without boss — is CTS's `225BM...RB1(S)`
family, which has a real datasheet with a toleranced PCB layout. The footprint is built to
the listing's own dimensions, since that is the part actually being soldered down, and
checked against the CTS layout read out of the PDF as vector geometry rather than measured
off a scan. The two agree to within 0.05 mm, which is the cross-check that they really are
the same part.

That has a pleasant consequence: **a genuine CTS part is a drop-in replacement.** The boss
holes are drilled to the listing's Ø0.9 mm, which takes the clone's 0.7 mm boss and CTS's
0.8 mm equally, and both parts put their switch leads on the same 4.20 mm centres. If the
cheap switch ever wears out, a distributor part with a ten-year availability guarantee
solders straight onto the same land. Note the *pads* sit on 4.25 mm centres rather than
4.20: they were trimmed inward-edge-only for hole clearance, so each pad's centre moved
0.025 mm outward while its outer edge stayed put. Both parts' leads still land well inside
the copper.

**Do not trust the terminal numbers.** CTS numbers the switch contacts 1/2 and the linked
frame 3/4; the clone numbers them the other way round. What is identical on both is the
geometry: the **small inboard pads are always the switch** and the **large outboard pads
are always the frame**. The footprint therefore labels the frame pads `SH` rather than
giving them numbers, which pairs with KiCad's stock `Switch:SW_Push_Shielded` symbol and
leaves nothing to get backwards. Both `SH` pads go to `GND` — the datasheet draws that pair
tied to earth, and they are the pads taking the mechanical load, so they want a solid
connection regardless.

Electrically it is the dullest circuit on the board: `R11` pulls GPIO10 up to 3V3 so the
pin is defined while the ESP32 boots with its GPIOs floating, `SW1` shorts it to ground
when pressed, and `C9` swallows contact bounce plus whatever static comes in through the
opening the plunger pokes out of. See the pin map for why GPIO10 and not GPIO9.

Two things are still open. The footprint has **no 3D model** yet, so it will show as an
empty outline in the 3D viewer. And while the land pattern is taken straight off the part's
own dimensioned drawing, that drawing carries no manufacturer name and no tolerances — so
**put a caliper on one of the delivered switches before the board is fabbed**, checking the 7.8 mm lead span, the 2.3 mm boss pitch
and the boss diameter. While it is in hand, confirm the one thing a caliper cannot: that
**the plunger comes out on the same side as the two large frame pads**, which is what the
footprint assumes and what decides which board edge the part goes on. Both checks take two
minutes and guard against a mistake that is unrecoverable once boards are ordered.

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

Together with the 10 k pull-up, that closes the **fail-safe** story completely. The
intercom is undisturbed whether our board is running, rebooting, mid-OTA, crashed, or
completely dead.

It does **not** close the *transmit* story, which earlier revisions of this document
assumed it did. An open-drain driver can only sink, so releasing the line back to
recessive was left to the intercom's own pull-up — measured at about 1 kΩ, which
takes ~44 µs of an 87 µs bit. Every frame we sent was mis-sampled and rejected, and
the controller went bus-off on all 32 retries. The fix is `R12`, a gated recessive
assist; see [Transmitting on C/D](#transmitting-on-cd-and-why-it-did-not-work-at-first)
below. Fail-safe survives it because the assist hangs off a GPIO that is an input at
every instant the firmware is not deliberately transmitting.

### Acceptable substitutions

- **`74LVC1G125` instead of `74LVC1G07`**: works, wired as **input tied to GND,
  `/OE` driven by CAN TX**. Since `/OE` is active-low, TX low enables the output and
  drives the grounded input onto the line (dominant), TX high tri-states it
  (recessive).
  This entry used to warn against the other wiring — TX on the input, `/OE` on a
  GPIO — on the grounds that it would "drive the recessive state actively high and
  fight the bus". That reasoning was wrong, and the transmit bring-up proved it:
  driving recessive actively is exactly what this bus needs, and a passive
  open-drain stage cannot transmit here at all. That wiring is in fact the *better*
  assist topology, because the output then follows the transmitted bit and stops
  sourcing during dominant bits. It was set aside only because the plain `1G07`
  plus a gated `R12` was already proven on the wall. See `R12` below.
- **`SK6812` instead of the specified `WS2812B`**: **do not.** Earlier revisions of this
  document had it the other way round and were wrong — the `SK6812` 5050 is 3.5 V minimum
  and the `MINI-E` 3.7 V, so neither meets our 3.3 V rail, while the `WS2812B` is specified
  3.3-5.5 V. See the corrected LED note. Same for `WS2812E`/`WS2812S` at 3.8 V.
- **Two plain low-Vf LEDs, one per toggle**, instead of one RGB pixel: red and amber are
  ~2.0 V, so they are fully in spec on 3.3 V with no headroom question at all, and there is
  no driver IC to fail. Costs one extra GPIO (six are spare) and a second light pipe. This
  is the fallback if a bench check shows weak blue or green.
  A *three-colour* RGB LED on PWM does **not** solve the headroom problem — its blue and
  green dice have the same 2.8-3.4 V Vf as the pixel's.
- **Optocoupler (PC817) on `GONG1`/`GONG2`**: no longer needed. Ring detection comes
  off the CAN bus. Only worth adding as a fallback if bus receive proves unreliable.

## Transmitting on C/D, and why it did not work at first

Receiving worked from the first build. Transmitting did not work at all, and the
reason was not in this document's original design — the open-drain buffer plus a
10 k pull-up on its *input* is a complete and correct **fail-safe** story, and an
incomplete **transmit** story. Blow-by-blow account in
`docs/tx-bringup-catchup.md`; the conclusions are here.

### The symptom, and four things it was not

Every frame failed identically: 32 retries, TEC 128, bus-off, errors landing at
~95 bit times — the acknowledgement region. Receive stayed perfect throughout, with
REC at 0 while TEC exploded. Ruled out, each with a test, so **do not re-prove
these**:

- **Baud.** Terminal frames CRC-match at 11364 with −1.3% skew. If the rate were
  wrong, receive would fail first.
- **A bus that never acknowledges.** Captures of the terminal's own traffic show the
  ACK slot pulled dominant by other nodes.
- **A missing ACK on our frames specifically.** `TWAI_MODE_NO_ACK` with
  `TWAI_MSG_FLAG_SELF` failed at the same 95 bit times, so the controller was not
  waiting on an acknowledgement that never came.
- **A dead transmit path or a weak GPIO.** The TX path self-test passes: driving
  GPIO21 pulls `C/D` dominant and it recovers. Separately, jumpering GPIO5 to 3V3 —
  making `R12` a plain rail pull-up, no GPIO involved — reproduced the failure
  exactly, at +28.5% skew versus +29%.

### The actual cause

`U2` is open-drain, so it can only *sink*. Nothing on this board pulled `C/D` back
up, which left recovery to recessive to the intercom's own pull-up. Measured on the
wall, that takes **~44 µs of an 87 µs bit**: every dominant bit we sent overran its
slot by half a bit, other nodes mis-sampled the frame, and their error flags read
from our side as "never acknowledged".

Analyzer captures make it unarguable. Same probe, same session: the terminal's
frames CRC-match at −1.3% skew, ours came out at +46% with garbage payloads.

**The bus pull-up is about 1 kΩ**, which is the number that explains the whole
episode. Adding 1 kΩ in parallel *halved* recovery to 22 µs, and only a resistor
equal to what is already there can halve it. So a 1 kΩ assist was never going to be
enough — it can only ever buy a factor of two, and a quarter of a bit is still
fatal. The assist has to be well *below* the bus pull-up, not comparable to it.

### `R12`, and why 240 R

240 R took recovery to **8 µs** and the very next door frame read
`ID=0x0DF DLC=4 data: 02 07 01 00 CRC MATCH ACK` at +6.2% skew, with `tx done`,
TEC 0, and the panel's `0x0DF 01 01 07` acknowledgement 26 ms later.

The value is measured on this building's bus, not calculated, so treat substitution
carefully — and note that going *smaller* is not a free improvement. While a bit is
dominant, `R12` is still sourcing into the line against `R5`, which lifts the
dominant level off ground:

| `R12` | Recovery | Dominant level | GPIO5 current | Verdict |
|---|---|---|---|---|
| 1 k | 22 µs | 0.28 V | 3.2 mA | **fails on this bus** |
| 330 R | ~11 µs | 0.53 V | 8.7 mA | untested alone |
| **240 R** | **8 µs** | **0.65 V** | 11.5 mA | **proven** |
| 180 R | ~6 µs | 0.78 V | 14.5 mA | trades dominant margin for edge |

Levels include the bus pull-up; the threshold is around 1.5 V, so 240 R keeps about
0.9 V of dominant margin. Pulse dissipation at 240 R is ~45 mW in a 100 mW part, and
`R5` at 47 R sets the floor on how hard `U2` may be asked to sink.

### It must be gated, and that is what keeps the fail-safe

Tied permanently to 3V3, `R12` works electrically — that is how the fix was first
proven — but it is not acceptable on shared building wiring:

- It fights whatever holds the bus dominant weakly. Measured: bursts of **~58 kHz
  relaxation oscillation** on an otherwise idle bus.
- It would leave a low-value path from a dead rail onto a line the whole building
  depends on.

So `R12` lands on **GPIO5**, which the firmware drives high only across the transmit
window and leaves as a floating input with pulls disabled at every other instant —
including before `setup()` runs and while the board is unpowered. Combined with
`U2`'s Ioff and `R4` on the buffer input, a dead or rebooting board still cannot
disturb the intercom. This is roughly what a single-wire CAN transceiver does:
recessive is driven, but only by the node that is talking.

### If more margin is ever needed

Not a smaller resistor. A **`74LVC1G125`** with its input on `CAN_TX` and `/OE`
gated by GPIO5 makes the assist follow the transmitted bit, so it pulls up during
recessive and stops sourcing during dominant — dominant returns to near ground and
`R12` can grow again. Considered and set aside to keep the circuit that is proven on
the wall. Note this is the wiring an earlier revision of the substitutions list
warned against, on reasoning the bring-up disproved.

### Verifying it without a scope

Firmware exposes an **Assist self-test** button that sinks the line and times the
rise, so the resistor can be checked from Home Assistant. Expected readings, what
each one means, and the OFF-side diagnostics are tabulated in `docs/perfboard.md`.
Short version: **assist ON in the single digits of microseconds is the pass**, ~22 µs
means too weak for this bus, and ~2000 µs means `C/D` is not actually connected. Do
not send a door frame until it passes — it unlocks the building door.

## The KiCad project

Lives in `pcb/board/`. **The schematic is generated, not hand-drawn.** Editing
`board.kicad_sch` in Eeschema works, but the next generator run overwrites it — so component
values, footprints and connectivity belong in `pcb/tools/design.py`, which is the source of
truth for the netlist.

```
python pcb/tools/gen_sch.py --check    # validate the declaration, write nothing
python pcb/tools/gen_sch.py            # emit pcb/board/board.kicad_sch
```

Symbol definitions are harvested from whatever is already embedded in the sheet and only
fetched from the installed KiCad libraries when missing, so regeneration does not silently
swap a symbol under you. Every symbol is placed unrotated and connectivity is expressed
purely with net labels on 5.08 mm stubs. That is deliberate: with no rotation the
library-to-sheet coordinate transform is just `x + px, y - py`, which removes the single
most likely source of a silently wrong netlist. **The layout is functional, not pretty** —
rearrange it in Eeschema if you like, but rerunning the generator resets the positions.

### Verifying it

Four checks, all scriptable, and all four must pass:

```
kicad-cli sch erc --severity-error --severity-warning --exit-code-violations \
    --output pcb/board/erc.rpt pcb/board/board.kicad_sch
kicad-cli sch export netlist --format kicadsexpr \
    --output pcb/board/board.net pcb/board/board.kicad_sch
python pcb/tools/check_net.py
python pcb/tools/check_libs.py
```

A fifth, `python pcb/tools/check_models.py`, is advisory rather than pass/fail: it lists parts
whose footprint has no 3D model, or references one that is not on disk. Nothing else reports
this, because a missing model is not an electrical fault — ERC, the netlist diff and
`check_libs` are all perfectly happy with an empty 3D view. It bites at layout time instead,
when the 3D view is the cheapest way to catch a part fouling the enclosure or an electrolytic
taller than the lid clears.

ERC only proves the sheet is self-consistent, which is why `check_net.py` exists: it diffs
the netlist KiCad actually exported against `design.py` and fails on any difference. The
generator additionally **asserts pin names against the library symbols** — `design.py`
records that `D1.1` must be called `K`, `Q1.2` must be `S`, and so on — so a polarity or
pinout slip fails generation loudly instead of reaching the board. It also refuses to emit
unless every pin of every part is either on a net or explicitly marked no-connect.

Current state: **0 ERC violations, 39 symbols, 23 nets, 96 wired pins, 13 no-connects**, and
the exported netlist matches `design.py` exactly.

`gen_sch.py` is also **idempotent** — running it twice leaves a byte-identical
`board.kicad_sch` — so a noisy diff after regenerating means something in `design.py`
actually changed, not that the generator reshuffled the file.

### Two symbols are deliberately not the obvious ones

- **`U2` is `74xGxx:74LVC1G07`, and it matters.** An earlier revision of the sheet used
  `SN74LVC1G00DBV`, which is a **two-input NAND**: pin 1 is a second input where the real
  1G07 has `NC`, and its output carries an inverting bubble. Wiring TX to pin 1 would have
  gone to a pin that does not exist on the part, and the inversion contradicts the polarity
  the firmware depends on. The correct symbol also types pin 4 as `open_collector`, so ERC
  expects the `R4` pull-up instead of flagging the net.
- **`D1` is `Device:D_Zener` valued `SMAJ18A`, not `Diode:SMAJ18A`.** KiCad's `SMAJ18A`
  symbol extends `SM6T6V8A` and exposes pins `A1`/`A2` — it is drawn as a *bidirectional*
  TVS. SMAJ18**A** is unidirectional (the `CA` suffix is the bidirectional one), so that
  symbol misrepresents the part on a polarised SMA footprint. `D_Zener` gives proper `K`/`A`
  pins, which is what makes the footprint orientation and silkscreen unambiguous.

`Q1` uses `Transistor_FET:DMP3099L` and `Q2` uses `Transistor_BJT:BC850` as stand-ins for
the DMP4065SQ-7 and BCW65ALT1G. Both are correct: they are the standard SOT-23 pinouts
(1=G/B, 2=S/E, 3=D/C) that the real parts share, and the `Value` field carries the true part
number into the BOM.

### The project-local libraries

Custom footprints live in `pcb/libs/electra.pretty`, registered as **`electra`** in
`pcb/board/fp-lib-table` via `${KIPRJMOD}/../libs/electra.pretty`, with 3D models alongside
in `pcb/libs/electra.3dshapes` and symbols in `pcb/libs/electra.kicad_sym` (registered the
same way in `pcb/board/sym-lib-table`). Vendor downloads are kept unmodified under
`pcb/vendor/` for provenance.

Keeping all of this in-tree means **the board resolves on any machine**: every symbol and
footprint it uses comes from either this repository or a stock KiCad install, with nothing
from a personal library folder. `python pcb/tools/check_libs.py` asserts exactly that, and
it is worth running because nothing else catches a broken library reference — `gen_sch.py`
reuses symbol definitions already embedded in the schematic and ERC only ever reads those
embedded copies, so a reference that works on one machine and nowhere else still passes a
completely clean ERC.

**`F1` is done: `electra:Fuse_2410_6125Metric_Littelfuse_453`.** Its pads are the recommended
land pattern from the Littelfuse 451/453 datasheet — **1.96 x 3.15 mm on 2.45 mm centres**,
2.95 mm inner gap, 6.86 mm overall span — and the body outline is the real 6.10 x 2.69 mm.

It started from a SnapEDA download for a **Bel Fuse 0679L5000-05**, which is a *different*
part: same 2410 body, but quick-acting and **5 A** where ours is 250 mA. Only the land
pattern was reused, and only after checking it: SnapEDA's pad centres were ±2.455 mm against
Littelfuse's ±2.45 mm, agreeing to 5 µm, which is what made the pattern trustworthy. The pad
*sizes* still follow Littelfuse (SnapEDA's were 2.15 x 2.8 mm). **Nothing from that download
reaches the BOM** — the symbol stays `Device:Fuse_Small` and the value stays `0453.250MR`.

The attached 3D model is that same Bel Fuse body, kept because a 2410 fuse is
dimensionally a 2410 fuse and it is only used for clearance checks. Measured from the STEP
itself it is **6.10 x 2.54 x 2.79 mm**, so it is right on length and errs 0.1 mm generous on
height against the Littelfuse's 2.69 mm.

**`L1` is done too: `electra:Inductor_Coilcraft_XGL4020`** — pads **0.98 x 3.4 mm on 2.37 mm
centres**, which is verbatim the recommended land pattern on page 3 of Coilcraft doc 1529.

This one came from a download for an **XFL4020-222MEC**: a different family (`XFL`, not `XGL`)
and a different value (2.2 µH, not 3.3). Neither matters, because only the land pattern was
taken and **every dimension of it is identical** — pad size 0.98 x 3.4 and spacing 2.37 mm
both agree exactly, so the two Coilcraft 4020 families share one pattern. As with `F1`,
nothing from the download reaches the BOM: the symbol stays `Device:L` and the value stays
`3.3uH`. The 3D model is the XFL body, and measured from the STEP it is **4.0 x 4.0 x 2.1 mm**
— exactly the XGL's own envelope, so it is honest for clearance work.

**Both 3D models needed `(rotate (xyz -90 0 0))`, and neither would have been caught by ERC
or DRC.** They are exported **Y-up**, as vendor STEP models usually are, while KiCad reads a
model as Z-up. Left alone, each body sat **half-buried in the board and offset sideways off
its own pads** — the inductor spanned board Z from −2 to +2 mm on a part that is 2.1 mm tall.
Harmless for fabrication, since only the copper is manufactured, but it would quietly wreck
any enclosure or lid-clearance check, which is the one job these models have. `pcb/tools/check_3d.py`
renders the whole library on a scratch board so this is a look rather than a guess; **run it
whenever a footprint gains a model.** A correct one sits *on* the board in the side view and
*centred* on its pads from the top.

**Every part on the board now has a 3D model except one that needs none** — `check_models.py`
reports *"35/36 parts have a 3D model, 1 need none, 0 still to draw"* as of 16 Aug 2026. It began
at four missing. Three were drawn, below, and the fourth was never a gap: `J2`'s stock
`Connector_Wire:SolderWire-…` footprint names
`Connector_Wire.3dshapes/…`, and **that model package is absent from the install entirely** —
the directory does not exist and no `SolderWire` model is anywhere under `3dmodels`, yet 324 of
the 330 footprints in that library reference one. So it is an upstream gap, not a local
breakage, and worth knowing before hunting for a mistake in our own paths.

They are not equally worth fixing. **`SW1` earned one first**, because it is the only part whose
position is constrained by something outside the board: the plunger has to line up with a hole in
the housing wall and protrude far enough to be pressed. That is precisely the kind of thing a 3D
view catches and a schematic never will. The two connectors matter second, and for a different
reason — both are **top-entry**, so what needs checking is not the body footprint but the
headroom above it for the plug and the fingers inserting it.

### Drawing `J1`, and the height nobody had looked up

`pcb/tools/model_jst125.py` builds it, and **takes the pin count as an argument** so the same
script covers `J3`: the two parts differ only in that one number, since the vendor table is
generated from pin span A = (N−1) × 1.25 with body C = A + 1.95 and overall B = A + 3.00.

Drawing it turned up **the one dimension the land pattern never needed and nobody had looked up:
these headers stand 4.75 mm tall.** That is off the front elevation on page 2 of the vendor sheet,
and it matters more than the body outline ever did, because a top-entry connector's clearance
problem is vertical. The plug comes down from above, the mating crimp housing on page 1 is
**4.0 mm** tall in its own right, and fingers or pliers need room above that again. So the real
constraint at `J1` and `J3` is not the 5.5 × 3.7 mm of board they occupy — it is that **nothing
can sit over them**, and the enclosure needs the lid clear of roughly 10 mm above these two spots
rather than the 4.75 the part measures.

The same sheet also **confirmed the 3.70 mm depth** already in the F.Fab outlines, which was
reassuring: that figure had been carried from the CTS-style reasoning rather than read off this
drawing, and it agrees.

> **The sheet's letters contradict its own table, so read it carefully.** In the plan view the
> *wider* span is labelled A and the narrower C, while the table has A as its *smallest* column.
> The table is the one to trust, and the physical proportions settle it: on a 3-way part
> C = 4.45 mm is the only one of the three figures that can be the plastic body. This is the same
> jumbling already noted when the land pattern was derived — the drawing and the table were
> evidently lettered by different hands.

Two cavity dimensions are inferred rather than dimensioned — the 0.40 mm wall and the 1.10 mm
cavity floor — but neither affects fit or clearance, only how convincing the part looks in the
3D view.

**`J3` then cost one command**, `model_jst125.py 2`, and came out at 4.25 × 3.70 × 4.75 mm —
matching the table's 2-way row of A = 1.25, C = 3.20, B = 4.25 exactly. That is the payoff for
parameterising rather than drawing each one: the second connector needed no new measurements, no
new reasoning, and could not disagree with the first about anything they share.

One detail needed a second pass on `J1` and was worth fixing before it propagated. The anchor tabs
initially perched on a 0.5 mm sliver of their 2.00 × 3.00 mm pads, because the tab metal is
narrower than the copper. Left alone it would have read as a **footprint error** to anyone opening
the 3D view later, so the feet now run in under the housing to cover the pad, with the overlap
buried inside the plastic where it never shows.

### Drawing `SW1`'s model

No vendor supplies a model for a kit part, so it is **built rather than downloaded**, by
`pcb/tools/model_sw1.py` (cadquery, exports STEP). That is a deliberate choice over drawing it
once by hand: the vendor drawing is a raster scan of an *unlabelled* projection, so several of
its numbers are a reading rather than a transcription, and keeping every dimension as a named
constant at the top of a script makes correcting one **a one-line edit and a re-run** instead of
a remodelling job. Expect to correct one.

What the drawing states plainly: overall **7.8 × 3.5 × 3.8 mm**, a **7.0 mm** plastic body, a
**3 mm** wide plunger, **2 × Ø0.7 mm** bosses at 2.3 mm pitch, and a lead foot capped at 0.3 mm.

**Two numbers are inferred, and they are the ones that matter most.** The drawing gives 3.5 mm
of depth but never says how it divides between body and plunger. The model splits it as a
**3.0 mm body with the plunger standing 0.5 mm proud**, because 3.0 is what both the CTS sheet
and this footprint's own F.Fab already use, and that split makes the stated 3.5 come out right.
It also lands the plunger tip at exactly the +2.0 mm the F.Fab actuator was drawn to, which is a
pleasing agreement but not independent evidence — both trace to the same reading. **The plunger's
reach is therefore the one figure to caliper before cutting a hole in the housing wall**, since
an overstated reach is the dangerous direction: it would have you site the hole for a button that
then sits recessed and cannot be pressed.

One deliberate mismatch: the model's body is **7.0 mm** wide where the F.Fab outline is 6.9. The
6.9 comes from the CTS sheet, the 7.0 from the drawing for the part actually being fitted, and
the model takes the larger figure because for clearance work the generous number is the safe one.

`check_3d.py` grew two conveniences while verifying this. It now takes a **name filter**, because
the whole library rendered in a row leaves each part far too small to judge, and it **wraps
whatever it places in an `Edge.Cuts` outline** — without one KiCad renders a board it cannot
frame, and the camera points at empty space instead of at the part. The renders confirm what they
need to: the body sits *on* the board rather than buried in it, it is centred on its own pads, and
the plunger points at footprint **+Y**, which is the direction the F.Fab arrow claims. That Y
question is not a formality — the model frame negates Y relative to the footprint, and getting it
wrong is what buried the vendor STEP models earlier.

> **`J2` will never have a 3D model, and that is the correct outcome, not an omission.** It is a
> bare wire soldered through a hole: there is no body to draw, nothing for an enclosure to
> collide with, and empty space is the honest representation. It is recorded that way in
> `check_models.py`'s `WAIVED` table, with the reason attached, so the report separates it from
> the parts that genuinely still need drawing instead of nagging about it forever. The tool now
> reads *"32/36 parts have a 3D model, 1 need none, 3 still to draw."*

> **`L1` has an orientation and it is not cosmetic.** The datasheet marks one terminal as the
> start (short) lead and asks for **the high dv/dt node there for lowest EMI**. That is pin 1
> in this footprint, carrying the marker dot. `design.py` already puts pin 1 on `SW` and pin 2
> on the `3V3` output, so **do not flip `L1` in layout** to make a track shorter — it would
> turn the winding's outer layer into an antenna on the noisiest node on the board.

**`C6` is done as well: `electra:Capacitor_Panasonic_EEH-ZA_6.3x5.8`** — pads **3.2 x 1.6 mm on
5.0 mm centres**, a 6.6 x 6.6 mm base with the chamfer on the pin 1 side, and the Ø6.3 mm can
drawn on the fab layer.

The case code question is settled: Panasonic's ZA characteristics list gives `EEHZA1V470P` as
47 µF / 35 V, **Ø6.3 x 5.8 mm, size code D**, ESR 60 mΩ — which confirms both the dimensions
this document already quoted and the 60 mΩ figure the endurance argument rests on. Size D's
base is **A, B = 6.6 mm**, not 6.3; 6.3 is the can diameter, and the footprint outline is the
base.

This came from a SamacSys download for the exact part number, but it was still checked against
the datasheet rather than trusted, and it reconciles precisely: the pads run from **0.9 mm to
4.1 mm** from centre, where **P/2 = 0.9 mm** is the terminal inner edge and **H max/2 = 3.9 mm**
is the terminal tip. So the pattern is the real terminal plus a 0.2 mm fillet allowance
outward. KiCad's stock `CP_Elec_6.3x5.8` was the alternative and was **rejected**: it is
3.5 x 1.6 mm on 5.4 mm centres, which is 0.4 mm wider in spacing, and its own description says
it was generated for a **Nichicon** part.

> **`C6` is polarised and pin 1 is the positive terminal.** Panasonic's bottom-view drawing
> puts ⊕ on the side with the **two chamfered corners** and ⊖ on the square-cornered side, so
> the chamfer marks the anode. `design.py` has pin 1 on `VIN` and pin 2 on `GND`, which is
> correct, and the footprint carries a **"+" on both silkscreen and fab** next to pin 1.
> Three independent sources agree on this: the datasheet symbols, KiCad's stock convention for
> the same package, and the vendor 3D model — whose black band, which the datasheet defines as
> the *negative* marking, renders over pad 2. Reversing this part on the 13.5 V rail vents the
> can, so it is worth the redundancy.

Note that KiCad's nearest stock fuse footprint was 2512 (6.35 x 3.2 mm) — close enough to
2410 to look right and wrong enough to matter. That is the trap this library exists to avoid.

**`J2` is done, and it needs no custom footprint at all:
`Connector_Wire:SolderWire-0.15sqmm_1x02_P4mm_D0.5mm_OD1.5mm_Relief`.** The two wire ends
solder into **plated Ø0.7 mm holes on 4 mm centres**, and the **Ø2.0 mm holes 9 mm behind
them are the strain relief** — the wire feeds down through one, runs along the far face and
comes back up into its solder hole, so the board itself grips the cable and any tug is taken
by laminate rather than by a solder joint. See the speaker-lead note for why this beats both
SMD pads and a cable tie.

Two things made this a stock part rather than a drawn one. KiCad has an entire library for
soldered wire connections, `Connector_Wire`, and the size that matches is dimensioned for a
**0.5 mm conductor in 1.5 mm insulation** — which is exactly silicone-clad 26 AWG, where the
otherwise-tempting `0.127sqmm` variant assumes 1.0 mm insulation and would have made the
relief hole too tight to thread. Its 9 mm relief spacing is the datasheet bend radius of
3x the outer diameter, taken twice.

**Which variant is right depends on which speaker arrangement wins**, and it is the one thing
that choice touches on the board. The `OD1.5mm` size assumes *our* silicone-clad 26 AWG. Under
the [fallback](#if-the-factory-plug-does-not-mate), `J2` carries the intercom's **factory**
lead instead, which is likely thinner PVC nearer 1.0-1.2 mm, and a wire that rattles around in
its relief hole is barely strain-relieved at all. If it measures near 1.0 mm, switch to
`SolderWire-0.127sqmm_1x02_P3.7mm_D0.48mm_OD1mm_Relief`: Ø1.5 mm relief, the same Ø0.7 mm
plated pads, and 3 mm shorter into the bargain. So caliper whichever wire will actually land
here, not the spool on the shelf.

It costs a **7 x 12 mm strip** of board, which sounds like a lot until you notice most of it
is empty laminate: the only features are four holes. Tracks may run through the middle, and
the courtyard is there to stop *components* being placed in the wire's channel, not copper.

The symbol changed with it, from `Connector:Conn_01x02_Socket` to the genderless
`Connector_Generic:Conn_01x02`, because there is no socket on this end — it is bare holes.
Both spell their pins `Pin_1`/`Pin_2`, so nothing else in `design.py` had to move. `J3` keeps
the socket symbol, since that one really is a socket.

**`J3` is done too, and drawn rather than borrowed:
`electra:Conn_MicroJST1.25-SHstyle_1x02-1MP_P1.25mm_Vertical_SMD`.** It briefly held
`JST_GH_BM02B-GHS-TBT_1x02-1MP_P1.25mm_Vertical`, which was at least the right pitch — the sheet
before that had a 2.00 mm JWPF footprint — but as the section above establishes, this part is not
GH, and a footprint 1.5 mm too long in the body is a dead board. The vendor sheet carries its own
PCB layout, so the land pattern comes from the manufacturer's drawing rather than from calipers:
signal pads **0.50 x 1.60 mm** on the 1.25 mm pitch at x = ±0.625, and two **2.00 x 3.00 mm**
anchor pads centred at x = ±1.60 on the far side of the part, with a **0.60 mm** gap between the
two pad bands. The pattern is datumed on the origin, as KiCad datums its own SH and GH vertical
footprints, which puts the signal row at y = +1.80 and the anchors at y = −1.10 — both between
stock SH (+1.325 / −1.200) and stock GH (+1.950 / −1.400), and that is the check that the numbers
came out in family.

**Two of them are reasoned rather than stated, so confirm them before fab.** The sheet never says
what its `C` column measures. Read C = 3.20 as the plastic body and its ends fall at x = ±1.60,
where anchor pads centred on those end edges land exactly as drawn; read `B` = 4.25 as the overall
width including the metal tabs and that leaves 0.475 mm of pad proud of the part for a fillet,
with 1.00 mm tucked under the body where the tab folds beneath. The competing reading — C as the
anchor-pad centre span — independently gives the same ±1.60, and two incompatible readings
agreeing on one answer is the reason to trust it. The second inference is that the sheet's lone
0.60 figure is the band gap; stock SH leaves 0.85 mm there and GH 1.10 mm, so 0.60 is tight but
in range. **On arrival, check the anchor-tab centre span reads 3.20 mm and the clear gap to the
pin row 0.60 mm.**

Geometry verifies: silkscreen-to-pad and pad-to-pad both at 0.200 mm or better, courtyard
enclosing copper and body, and `fp upgrade` leaves the file alone. It has a 3D model too, from the
same script as `J1` — see the model section, which is also where the height finally got looked up.

**`J1` is done too, on the same family: three ways instead of two —
`electra:Conn_MicroJST1.25-SHstyle_1x03-1MP_P1.25mm_Vertical_SMD`.** Signal pads at
x = -1.25 / 0 / +1.25 and the same 2.00 x 3.00 mm anchor pads, now out at x = +/-2.225. Reusing
the family here buys more than tidiness: one crimp tool, one technique and one spare-parts
drawer then cover every connector on the board.

**It also scaled exactly as the reading of the vendor table predicted, which is the strongest
corroboration yet that the reading is right.** Row N=3 gives pin span 2.50, body C = 4.45 and
overall B = 5.50. Drop those in and the anchor centres land precisely on the body edges again
(C/2 = 2.225), and the pads again finish **0.475 mm proud** of the part's overall width — the
identical overhang the 2-way part has. Two rows of the table independently agreeing on a derived
constant is not a coincidence, so the two inferred numbers are now much safer than they were.
Caliper them anyway when the parts land.

Geometry verifies on the same terms as the 2-way: silkscreen-to-pad and pad-to-pad both 0.200 mm
or better, courtyard enclosing copper and body, `fp upgrade` idempotent. It has a 3D model, built
from these same table figures by the script described in the model section.

With that, **`check_libs` reports zero pending**: every symbol and footprint in the design now
resolves from either this repository or a stock KiCad install. There are no empty footprints left.

One practical catch, though: **the 3-way parts are a separate order.** The listing sells one pin
count per purchase, so the 2P order that covers `J2` and `J3` contains nothing that fits `J1`.

`J1` also carries the **raw 13.5 V** tap, which is worth a sentence on a 1.25 mm pitch. Current
is trivial — the board pulls a couple of hundred mA at 3.3 V, so well under 100 mA on the input
side, against a connector family good for around 1 A. Voltage is equally undemanding: the pads
leave roughly 0.75 mm of copper gap, where 13.5 V in a dry indoor enclosure needs a fraction of
that. The clone publishes no ratings at all, but nothing here comes close to stressing it. The
real reason to prefer a connector over solder pads is service: it lets the board be unplugged
from power and bus without touching the intercom's screw terminals, which matters most during
bring-up when the regulator is being checked in isolation.

Measuring `J101`'s housing is still needed, but it was never a blocker for `J2` as this
document previously implied. That measurement decides which **plug** to crimp for the `J101`
end; it says nothing about where the other ends of the wires land on our board, and those are
independent choices.

**`U3` is done: `electra:ESP32-C3_SUPERMINI_SMD` + `electra:MODULE_ESP32-C3_SUPERMINI`.**
The module was the last thing resolving through a personal library folder, and its symbol,
footprint and 3D model are now all in-tree. The footprint mounts the module as an SMD part
on two rows of eight 3.025 x 1.524 mm pads at 2.54 mm pitch, 15.97 mm between rows, under an
18 x 22.7 mm body notched at the USB-C end. Its pads are named for the module's own
silkscreen labels rather than numbered, which is why `design.py` refers to pins as `U3.3.3`
and `U3.G`.

Two things were repaired on the way in. The symbol's `Footprint` property pointed at
`ESP32-C3_SUPERMINI_SMD:MODULE_ESP32-C3_SUPERMINI`, a footprint library that does not exist
under that name — harmless only because `design.py` overrides the footprint anyway. And the
**3D model was never attached**, so the module simply did not appear in the 3D view; it is
wired up now.

Seating that model is the one case where the rule used for `F1`, `L1` and `C6` does not
apply by itself. It is Y-up like the rest of that vendor's output, so it takes the same
`rotate -90` about X, but its *lowest* geometry sits 2.39 mm below the seating plane and
lifting by that amount leaves the module floating. The seating plane is the module PCB
bottom at **Y = 0**, identifiable as a 526-point planar face with the PCB top 0.9 mm above
it as a 725-point face, so the correct offset is **zero**. What lies below are the
through-hole pin stubs, which belong below the board and are hidden inside it — we solder
the module SMD, without headers. The lesson generalises: pick the seating plane by finding
the dominant planar face, not by taking the model's extreme.

**`SW1` is done: `electra:SW_Push_Side_CTS_225B_7.8x3.5mm_Boss`.** Pads 1/2, the switch
contacts, are **0.85 x 1.25 mm centred at ±2.125, −0.925** — the drawing's 0.90 x 1.30 mm on
4.20 mm centres, shortened 0.05 mm on each axis for hole clearance, outer edges unmoved; the
two `SH` frame pads are **1.45 x 0.90 mm on 6.75 mm centres**, a 5.30 mm inner gap and an
8.20 mm outer span; the boss holes are **Ø0.9 mm NPTH on a 2.30 mm pitch**. The origin is the
**part centre**, so the 6.9 x 3.0 mm body sits symmetrically about it and the boss holes fall
**0.15 mm below** it. The switch note above covers why this part and why the bossed variant.

That 0.15 mm offset is the whole key to reading the drawing: the holes are *not* on the
part's horizontal centreline, and until that is spotted none of the vertical callouts can be
made to agree. Once it is, they all close — switch pads 0.25 mm above centre, frame pads
0.50 mm below.

**The pattern is built to the drawing for the part being bought, and corroborated against the
CTS Series 225B datasheet rather than derived from it.** The CTS figures were read out of the
PDF as **vector geometry** instead of measured off a raster scan: the hole pitch came out at
32.59 pt for a stated 2.30 mm, a 14.17 pt/mm scale against which every other callout
reconciled to three decimal places. The two sources agree to within **0.05 mm everywhere**,
which is what establishes that the unbranded part really is this form factor — and it means a
**genuine CTS part still drops in**, its 0.8 mm bosses entering these 0.9 mm holes and its
switch leads landing on the same 4.20 mm lead centres. Only its frame leads run wider, 8.30 mm
against 8.20, overhanging the pad end by 0.05 mm, which is nothing on a hand-soldered
gull-wing. Reading the vectors also settled the listing drawing's one real ambiguity: its
`4.2` is **centre-to-centre**, not the outer span it looks like, which is why
`3.3 + 0.9 + 0.9` never added up to its stated `5.3`.

**Copper-to-hole-wall clearance is 0.261 mm** at pads 1 and 2, after a trim made on
1 Sep 2026 while checking the board against the fab's quote page. A bossed side-push is
inherently cramped — the bosses have to sit between the two pad rows — and KiCad's own stock
library ships the class tighter still: **0.075 mm** on the Alps `SKRTLAE010` and **0.175 mm**
on the CK `KMS2xxGP`. Silkscreen is held 0.24 mm off the copper.

**Drawn to the raw land pattern it was 0.190 mm, and that needed fixing rather than
excusing.** An earlier revision of this section argued the figure was normal for the class,
which is true and was beside the point: 0.190 mm is inside KiCad's own default 0.25 mm
hole-clearance rule and inside the **0.254 mm hole-to-copper minimum JLCPCB publishes**, so it
required two DRC exclusions and invited an engineering query on a board that was one click
from being ordered. Worse, the exclusions made `kicad-cli pcb drc` report zero violations,
so the board looked clean while carrying a known out-of-spec dimension.

The fix exploits the fact that the closest approach is **diagonal** — hole centre to the
pad's inner corner, 0.5 mm across and 0.4 mm along. Taking 0.05 mm off *each* axis therefore
buys more clearance than taking 0.075 mm off either one alone, and it costs less pad. The
outer pad edges, where the gull-wing toe lands and the fillet forms, did not move at all.
The holes were deliberately **not** shrunk: at Ø0.9 mm they clear the part's 0.8 mm bosses by
only 0.1 mm in total, and a part that seats matters more than a spacing that measures well.
Both exclusions are now deleted, so DRC reporting zero means zero.

The boss holes have **size equal to drill**, so they carry no annular ring and their copper
layer set cannot affect what gets fabricated. It is spelled `*.Cu` rather than `F&B.Cu`
because that is what **all 25** `np_thru_hole` pads in KiCad's `Button_Switch_SMD` library
use, so it is written down here to stop someone "correcting" an inert field back to the
non-standard spelling.

> **`SW1` has to go at a board edge, and the direction is not arbitrary.** The plunger fires
> in **+Y**, drawn on the fab layer as an arrow with the actuator body it pushes through.
> That edge must face the housing wall the button pokes through, and nothing may sit in the
> press path — which is why the courtyard is drawn generously on that side rather than tight
> to the copper. CTS orders actuator length as a variable, so the exact protrusion depends
> on which part arrives.

It has a **3D model built from its dimensions** rather than a vendor STEP — see the 3D-model
section, which also records the one figure (plunger reach) still to caliper.

### The relay contacts, measured — and the schematic was wrong

**Resolved 23 Aug 2026, on the physical part.** With the coil unpowered the meter reads
continuity on **2-3 and 6-7**, and the Omron drawing agrees: **COM = 3/6 (centre pins),
NC = 2/7 (coil-end pins), NO = 4/5.**

The first revision of `design.py` had wired the speaker through 3-4 and 6-5 — through the
**normally-open** contacts. An unpowered or crashed board would have muted the intercom
permanently, the exact inversion of the fail-safe this design promises, and it would have
been discovered only after fab. The earlier text here said the KiCad symbol's geometry
supported the 4/5-as-NC reading; it did, and it was wrong, which is why this check was
gated on a meter rather than on anyone's reading of a drawing.

The fix is in: `SPK_SW` moved to pins 2/7 in `design.py`, pins 4/5 to the no-connect list,
the PCB rerouted through the coil-end row, and the gerbers regenerated. The 2026-08-20 zip
was destroyed; the `2026-08-23-relayfix` zip carried the fix, and has since been superseded
in turn by **`v0.9`** once `R12` was placed — see [Fabrication](#fabrication) for which file
to upload. De-energised now genuinely means speaker connected.

Both poles are wired in parallel on purpose — it halves contact resistance and adds
redundancy on a low-level audio signal. The trade is deliberate: a contact that fails to
open breaks Silent mode, which merely means you hear the ring, whereas a contact that fails
to close would break the intercom.

## Fabrication

**Upload `pcb/gerbers/electra-intercom-gerbers-v0.9-2026-09-01.zip`.** Every earlier zip is
superseded: the 2026-08-20 one predates the relay contact fix, and `2026-08-23-relayfix`
predates `R12`, without which the node can receive but cannot transmit. The board carries
`v0.9` on the front silkscreen so a bare board can be identified later without opening a
gerber viewer.

Board is **54.5 x 47.0 mm**, 2 layers, and the exported set is F.Cu, B.Cu, both masks, both
pastes, both silkscreens, Edge.Cuts, plus separate PTH and NPTH Excellon drills.

| Option | Choose | Why this and not the default |
|---|---|---|
| Layers | **2** | Decided deliberately. `F.Cu` routes and pours, `B.Cu` is a solid ground plane. Nothing on this board runs fast enough to need more |
| Thickness | **1.6 mm** | Not just the default. `SW1` is a *side*-push button, so pressing it loads the board edge-on; a 1.0 mm board would flex and rob the plunger of its few tenths of a millimetre of travel |
| Copper | **1 oz / 35 µm** | Peak draw is ~28 mA average plus a 9 mA relay coil. Heavier copper buys nothing and widens the minimum trace the fab will accept |
| **Surface finish** | **ENIG** | See below. This is the one option worth paying for |
| Solder mask | **green** | Not aesthetics — contrast. Every joint on this board is placed and inspected by hand, including SOT-23-5 and 0.5 mm `J1`/`J3` pads, and black mask makes bridges genuinely hard to see under magnification. The board is sealed inside a wall unit where nobody ever looks at it |
| Silkscreen | white, any process | Minimum stroke width is 0.15 mm and every text item on the board now meets it, including `v0.9`, which was 0.10 mm until it was corrected |
| Confirm production file | **yes** | Worth a day's delay on the first run of a board carrying three hand-drawn footprints and five non-plated holes, so their interpretation of the `SW1` bosses and the `J2` relief holes can be seen before copper is etched |
| Via covering | **tented** | 101 vias sit inside the ground pours, several close to pads. Untented invites solder wicking during hand assembly |
| Electrical test | **flying probe** | Standard, and worth having. It is also one of the things ENIG makes dependable, since probing bare or lightly oxidised copper is what gives false readings |
| Impedance control | **no** | 11,364 bps. The bus's own ~70 nF dwarfs anything the stackup does |
| Castellation, edge plating | **no** | Nothing on the board edge is a contact |
| Process tier | **cheapest standard** | Minimum track is 0.20 mm and every via is a 0.30 mm drill, comfortably inside the low-cost tier. Do not pay for a fine-feature process |

### Why ENIG and not OSP

OSP is usually the free option and it is a perfectly good finish — for a board that is
machine-assembled in one reflow pass shortly after it is fabbed. It is not a metal finish
at all, but a thin organic coating over bare copper that is largely consumed by the first
heat cycle. This board breaks every assumption behind that:

- **Assembly is by hand, in sessions, with hot air.** Every thermal excursion eats coating,
  and reworked areas solder measurably worse the second time. Rework is likely here: the
  relay contacts were already wrong once, and `SW1`'s land pattern is drawn from an
  AliExpress dimension drawing that still needs a caliper against the delivered part.
- **`J2` is wires hand-soldered into plated holes**, plausibly at final install, months
  after the board arrives and after it has been handled. Skin oils degrade OSP, and
  degraded OSP looks exactly like good OSP — both are bare copper.
- **This board gets probed constantly.** The entire transmit investigation ran on meter
  readings: GPIO5-to-`C/D` resistance, rail checks, relay continuity. Lightly oxidised
  copper gives intermittent readings, which is precisely the class of false signal that
  already cost a day on the flying-lead rig.
- **Spares will sit.** OSP's shelf life is roughly six months in the sealed bag and less
  once opened; boards two through five of an order may wait a year or more.

Against that, OSP offers cost and flatness. ENIG matches the flatness — which the 0.5 mm
pads on `J1` and `J3` do care about — and cost is the axis this project has consistently
decided against everywhere else.

The real arguments against ENIG are price and **"black pad"**, a nickel-corrosion defect
that produces joints which pass inspection and fail later. It is a process-control problem,
so order from a fab with a reputation to lose. ENIG's slightly more brittle intermetallic is
irrelevant to something screwed down once behind a wall plate.

**If ENIG is unavailable, fall back to lead-free HASL, not OSP** — robust, shelf-stable and
forgiving to hand-solder, at the cost of pad flatness, which makes `J1` and `J3` fussier but
not unworkable. **Do not take leaded HASL.**

### The stencil

Ordered with the board, 1 Sep 2026. Every option below was chosen against a measured
property of the layout rather than a default, using `pcb/tools/vfy_stencil.py`.

| Option | Choose | Why |
|---|---|---|
| Stencil side | **top only** | All **40** footprints are on the front; nothing is on the back. A bottom stencil would be pure waste |
| Framework | **no** | Frameless suits hand printing one small board. Framed stencils exist for printers, and cost and weigh far more |
| **Dimensions** | **custom, ~150 x 120 mm** | Not a standard size — see the sizing note below. This is the single option that changes what you pay |
| Thickness | **0.10 mm**, or let the fab choose | Release is not the constraint — see the area ratios below. Bridging is, and the binding number is the **0.350 mm** gap between `U1` pins 1 and 2, the tightest different-net spacing on the board. Thinner deposits less paste; hand printing already deposits more than a machine. JLCPCB's no-extra-cost thicknesses are 0.10, 0.12, 0.15, 0.18 and 0.20 mm, so 0.10 is free to ask for |
| Nano-coating | **no** | Only earns its price when area ratios approach the release limit. Ours are nowhere near it |
| Polishing | **sanding** | Same reason. Electropolishing smooths aperture walls to help marginal apertures release |
| Fiducials | **none** | Stencil fiducials align against matching marks in the board's copper, and this board has none. They would be decoration |
| Step stencil, engraved text | **no** | A step stencil varies aperture depth across the board, which nothing here needs. Engraving only helps tell multiple stencils apart |

**The area ratio is what makes most of those answers easy.** It is aperture opening area
divided by aperture wall area, and below roughly **0.66** paste starts staying in the
aperture instead of landing on the pad. The smallest aperture on this board is `U1` at
**0.600 x 1.325 mm**:

| Stencil thickness | Area ratio at `U1` |
|---|---|
| 0.08 mm (surcharged) | 2.58 |
| **0.10 mm** | **2.06** |
| 0.12 mm | 1.72 |
| 0.15 mm | 1.38 |

Three times the margin at every thickness offered, which is why the two upgrades sold to
improve release — nano-coating and electropolishing — buy nothing here.

**One check worth repeating if the layout ever changes.** There are **111** paste apertures
and **none of them sits on a drilled pad**, which is correct: paste over a hole falls
through it. That is what keeps `J2`'s plated wire holes and `SW1`'s boss holes bare, and
both of those are hand-soldered by design.

### Sizing the stencil, which is where the money is

**Do not take a standard size.** The 380 x 280 mm preset is listed at **0.8 kg** for a
54 x 47 mm board, and almost none of that is stencil: 380 x 280 mm of 0.10 mm steel is about
**84 g**. The rest is packaging, because JLCPCB boxes anything over 250 x 250 mm in cardboard
clamped between **wooden boards**, while anything at or under 250 x 250 mm goes in a plastic
bag with a light air-shipping box. A stencil under 280 x 280 mm also ships *with* the PCBs
rather than separately. So the sheet you actually want is a custom outline.

Frameless custom sizes are supported down to very small outlines — JLCPCB's frameless
pricing starts at $3 for 100 x 100 mm and they list "1:1 as PCB" as a valid custom entry — so
the 45 mm border implied by the standard models (380 x 280 has a 290 x 190 valid area) is a
property of those presets, not a constraint to design around.

**~150 x 120 mm is the recommendation**, giving roughly 48 mm of border on the long axis and
36 mm on the short. Border is not waste: it is where the sheet gets taped down, and where the
squeegee starts and stops clear of the apertures, which matters much more when printing by
hand than with a machine. 100 x 100 mm hits the price floor but leaves only ~23 mm of
squeegee run-up. At 150 x 120 mm the steel weighs about 14 g.

Worth checking before ordering: a **new-user stencil coupon** covers the full stencil cost at
any size up to 380 x 280 mm. If it applies the price argument disappears, but the weight
argument does not, so order small regardless.

**Ordering a stencil changed the assembly order**, because a printed board cannot be
populated in stages. See [Assembly order](#assembly-order).

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
| C2 | **TDK CGA3E3X8R1H104K080AB** | **100 nF / 50 V**, X8R, ±10% | 0603, 0.8 mm | Input HF bypass, **closer to the pins than C1**. AEC-Q200, -55/+150 C. Digi-Key `445-12606-1-ND`. Present on the official EVM - see note |
| C3, C4 | **TDK CGA6P1X7R1C226M250AC** | **22 uF / 16 V**, X7R, ±20%, **two of them** | **1210**, 2.5 mm | Output. Datasheet specifies 2 x 22 uF. AEC-Q200, -55/+125 C. Digi-Key `445-5723-1-ND`. **1210, not 1206** - see note |
| C5 | **TDK CGA3E3X8R1H104K080AB** | **100 nF / 50 V**, X8R, ±10% | 0603, 0.8 mm | Bootstrap, BST to SW. Must be ceramic. **Same part as C2**, so order 2 per board - see note |
| R1 | **Panasonic ERJ-3GEY0R00V** | **0 ohm** jumper fitted, 1 A, 100 mW | 0603 | In series with C5. AEC-Q200, -55/+155 C. Digi-Key `P0.0GCT-ND`. An EMI knob - **also buy 10R (`541-10GCT-ND`) and 22R (`P22GCT-ND`)**, see below |
| C6 | **Panasonic EEH-ZA1V470P** | **47 uF / 35 V**, polymer hybrid, **105 C 10000 h**, ESR 60 mohm | SMD V-chip **6.3 x 5.8 mm** | Bulk and LC damping on the feed from `+U`. AEC-Q200, fails **open**. Digi-Key `P15454CT-ND`. See the endurance note |
| F1 | **Littelfuse 0453.250MR** | **250 mA**, 125 V AC/DC, fast, I2t **15.8 mA2s** | **2410**, 6.1 x 2.69 mm | On the `+U` tap. **Protects the intercom from us.** 50 A breaking, -55/+125 C, UL/CSA. Digi-Key `F5688CT-ND`. Not 1206 and not slow-blow - see note |
| D1 | TVS | **SMAJ18A** | SMA (DO-214AC) | Transient clamp on `VIN`, **fitted behind Q1**. V_C 29.2 V max, matched to C6. Digi-Key `SMAJ18ABCT-ND` - see note |
| Q1 | **Diodes DMP4065SQ-7** | **-40 V**, Vgs ±20 V, 100 mohm max, **-20 A pulsed** | SOT-23 | Reverse-polarity ideal-diode. **AEC-Q101 + PPAP.** Digi-Key `DMP4065SQ-7DICT-ND` (`-7` = tape). Drain to F1, source to `VIN` - see note |
| R2, R3 | **Vishay Dale CRCW0603100KJNEA** x2 | **100 k** ±5%, 0.1 W, 75 V | 0603 | Gate divider for Q1. **Not a plain pull-down** - it halves Vgs so a TVS clamp cannot exceed ±20 V. AEC-Q200, -55/+155 C. Digi-Key `541-100KGCT-ND`. See note |

Wiring beyond that is trivial, because the fixed-output variant has its divider inside:

- **`FB` connects straight to `VOUT`.** No divider, no resistors, no tolerance stack.
- **`EN` ties to `VIN`.** The datasheet permits leaving it open, but tying it is
  deterministic and costs nothing. `EN` is rated to 35 V so 13.5 V is fine directly.
- `VIN` -> C2 then C1 then C6 (smallest nearest the pin), `SW` -> L1 -> `VOUT`,
  C5 from `SW` to `BST`, `GND` to plane.
- **Input chain order is fixed: `+U` -> F1 -> Q1 -> D1 -> C6/C1/C2 -> `VIN`.** D1 must sit
  *behind* Q1. In front of it, reversed wiring would forward-bias the unidirectional
  SMAJ18A into a dead short and blow F1 on a mistake Q1 exists to make harmless.

Fourteen components, no unpopulated positions. The regulator core itself — U1, L1, the four
ceramics, R1 and C6 — fits in roughly 10 x 8 mm; F1, D1, Q1 and the gate divider form a
separate input-protection block ahead of it.

**Per-board multiples, since three positions are easy to under-order:** C2 and C5 are the
same part number, so that is **2 per board**; C3 and C4 are **2 per board**; R2 and R3 are
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

The only thing the Bourns wins on is 0.3 mm of height, which is free to give up — C6,
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

### Choosing the input capacitor (C1 / C2)

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

**Add C2, the 100 nF 0603.** Our earlier BOM had only the bulk cap. The official
AP63203WU-EVM fits a 100 nF / 50 V 0603 at the input *in addition* to the 10 uF, and it
is worth copying: a 1206 has too much ESL to snub the fast dI/dt edges that the bulk cap
cannot follow. Place it **closer to VIN/GND than C1**, with C1 just outside it and the
electrolytic C6 furthest away. On a board that lives millimetres from capacitive touch
pads and a WiFi antenna, cents of HF bypass are the cheapest EMI insurance available.

X7R rather than the EVM's "X5R/X7R" for the usual reason: X5R stops at 85 C and this part
sits inside a sealed box next to a switching regulator.

#### C1 substitutes - only the 50 V is non-negotiable

The X7R `CGA5L1X7R1H106K160AC` was first choice but is frequently out of stock, so the
part actually fitted is **`CGA5L3X5R1H106M160AB`** — X5R instead of X7R, otherwise the same
1206 body, 10 uF, 50 V and AEC-Q200. Reasoning below.

Substituting is low risk provided one rule holds: **keep the 50 V rating**, because C1 sits
directly across the SMAJ18A clamp at up to 29.2 V. Everything else has slack, for the
reasons above — the 10 uF figure is sized for a 2 A load against our 0.15 A, and C6 already
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

### Choosing the output capacitors (C3 / C4)

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
`C3` and `C4` see ~13.5 V. That destroys the ESP32 either way, but a 16 V cap survives it while a
10 V cap may fail short and burn — and this box is screwed to a wall in a shared
building. Second, **DC bias derating actually matters on the output**, unlike on the
input: the AP63203 has fixed internal compensation designed around 2 x 22 uF, so loop
behaviour depends on the *effective* capacitance. A 16 V part at 3.3 V bias keeps more of
its nominal value than a 10 V part does, landing closer to what the compensation expects.

The cost is 0.9 mm of extra width each and 2.5 mm of height. Neither binds: C6, the
electrolytic, is 5.8 mm tall and sets the profile on its own.

Stock at the time of writing was 4,044 at Digi-Key and 1,484 at TME, so this is
comfortably sourced, and TME is the EU fallback if Digi-Key runs dry.

### The two 0603 ceramics (C2 input bypass, C5 bootstrap)

**One part number in two positions.** The BOM previously called for 25 V on the bootstrap
cap and 50 V on the input bypass. They are now both the 50 V part, deliberately: 50 V is
required at C2 because it sits behind the TVS clamp, and paying the same few cents at C5
collapses two BOM lines into one, gets a better price break, and removes any chance of
fitting the wrong one. Buy ten of `445-5666-1-ND` and forget about it — 10 cents each at
one, 7.5 cents at ten.

**50 V is genuine overkill at C5, which is fine.** The bootstrap cap sits between `BST`
and `SW`. Its *pin* swings to VIN plus the boot voltage relative to ground, but the
capacitor itself only ever sees the differential boot rail of a few volts, so a 10 V part
would be electrically sufficient. Commonality is worth more than that optimisation.

**One reason not to skimp on it anyway:** the datasheet notes that boot refresh — turning
the low-side switch on for 220 ns to recharge C5 when its voltage falls below 2.3 V —
happens during long periods of non-switching, specifically calling out **PFM at light
load**. That is not an edge case for us, it is our permanent operating point. C5 is the
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
can behave differently. It does not matter at either position — C5 sits at a few volts of
boot rail and C2 is an HF bypass whose exact value is irrelevant — but if this part number
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
24%, so C5 has the remaining 76% of every cycle to recharge. Slowing the high-side turn-on
does eat into the bootstrap refresh window, but at this duty ratio there is plenty to
spare.

### Reliability: what actually decides whether this lasts ten years

This is a permanent install in a sealed plastic box on a wall, wired into shared
building infrastructure. The failure modes that matter are not the obvious ones.

**1. C6 is the only real wear-out item, and this is why it is a hybrid.** Everything else
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
runs warm. So C6 is a **Panasonic EEH-ZA1V470P** polymer hybrid: same 47 uF, same 35 V,
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
**F1's 0.577 ohm**, Q1's ~0.1 ohm, C6's ESR, plus the wiring:

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

So C6 needs no insurance. **If ringing ever did appear**, the fix is ESR, not an RC: fit a
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
property that recommended the hybrid at C6.

**D1, the TVS**, clamps transients picked up by building wiring, which can be
substantial on long runs. About twenty cents.

**Match D1 to C6.** C6 is a **35 V** part, chosen because a 50 V SMD electrolytic at 47 uF
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

**The gate needs R2/R3 as a divider, not a plain pull-down to GND.** With the gate tied
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
| **Recessive assist** | **5** | **out, gated** | via 240 R (`R12`) to `C/D`. Driven high **only** while transmitting; a floating input with pulls disabled otherwise |
| Speaker relay | 6 | out | via transistor |
| Status LED data | 7 | out | via 330 R |
| Mode button | 10 | in | active low, **10 k pull-up to 3V3** (`R11`), 100 nF (`C9`) |
| *spare* | 0, 1, 3, 4 | | available if needed |

Unavailable on the C3: **GPIO11-17** are the SPI flash, **GPIO18/19** are the native
USB, and **GPIO2/8/9** are strapping pins best left alone.

GPIO10 is the right home for a button precisely because it is none of those. Put the
button on GPIO9 and holding it down while the unit powers up drops the ESP32 into
serial download mode instead of booting the firmware — a fault that would look like a
dead device and would be maddening to diagnose behind a wall plate.

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

   ---- RECESSIVE ASSIST (R12) ----
   GPIO5 ---[ 240R ]---> C/D

   Firmware drives GPIO5 high only while a frame is going out, and leaves it a
   floating input with pulls disabled at every other instant. Without this the
   node cannot transmit at all: the open-drain stage above can only sink, so
   recovery to recessive relies on the intercom's own ~1 k pull-up and takes
   ~44 us of an 87 us bit. Do NOT wire this to 3V3 instead - see the R12 section.

   ---- SPEAKER RELAY (Silent) ----
   GPIO6 ---[ 1k ]--- base | BCW65A
                      base ---[ 10k ]--- GND   (holds base down through boot)
                    emitter -> GND
                  collector -> relay coil pin A
                               relay coil pin B ---[ 150R ]--- +U
                                                  (~13.5 V, NOT the 3.3 V rail;
                                                   tap it AFTER F1 and D1)
                               1N4148W across the coil ONLY, cathode to the 150R
                               (put the diode across the coil, not across coil+150R)

   Relay pole 1 contacts, in ONE conductor between the two speaker connectors:
       J2 pin 1 (from intercom J101) -> COM
       NC                            -> J3 pin 1 (to speaker)
       NO                            -> not connected
   J2 pin 2 runs straight to J3 pin 2.
   De-energised = COM-NC closed = speaker connected = rings normally.

   J2 = 1.25 mm housing + crimped terminals (PA-09) at the J101 end; at our end the
        two wires feed through the Ø2.0 mm relief holes, then solder into the plated
        Ø0.7 mm holes 9 mm away. Thread before soldering, not after.
   J3 = 1.25 mm SMD vertical header on our board, the speaker's factory plug goes here
   Route the pair together and away from L1 and SW.

   ---- STATUS LED ----
   3V3 --> WS2812B VDD        (3.3-5.5 V part, so the single rail is in spec)
   GND --> WS2812B VSS
   GPIO7 ---[ 330R ]--> WS2812B DIN
   Threshold is 0.6 x VDD = 2.0 V, so the 3.3 V GPIO drives it with margin.

   (Fallback if a bench check shows weak blue/green - see the LED note:
    GPIO7 ---[ 330R ]---|>|--- GND   red   = Silent armed
    GPIO4 ---[ 330R ]---|>|--- GND   amber = Auto-open armed
    This used to say GPIO5, which is now the recessive assist. Do not reuse it.)

   ---- MODE BUTTON ----
   3V3 ---[ 10k ]---+-------------------> GPIO10
                    |
                    +---[ 100nF ]------- GND
                    |
                    +--> SW1 pad 1 (switch)
                         SW1 pad 2 (switch) -------> GND
                         SW1 both SH pads (frame) -> GND
   Idle high, pressed low. GPIO10 is not a strapping pin on the C3, so a stuck
   or held button cannot stop the module booting.
   Mount at a board edge, plunger facing the housing wall, press path kept clear.
```

**The relay coil runs off raw `+U`, not the regulated rail.** The coil current never
passes through the regulator, so it costs no conversion loss, and it keeps a 10 mA
switching step off the 3.3 V rail feeding the MCU. "Raw" here means *unregulated*, not
*unprotected*: **tap it downstream of F1 and D1**, so the transistor's collector is
behind the TVS rather than exposed to the incoming transient.

Steady-state that collector switches 13.5 V, and the flyback diode keeps the turn-off
spike below ~14.2 V, so the BCW65A's **Vceo of 32 V** is untroubled. The number that
needs a moment's thought is the surge case: with the transistor off the collector floats
up through the coil to whatever the rail is doing, and a full-energy SMAJ18A clamp at
29.2 V would be 91% of Vceo. Thin — except that **Vceo is the base-*open* rating, and
this base is never open.** With it held down the applicable figure is **Vces = 60 V**,
which makes 29.2 V a 49% stress.

**Which is exactly what the 10 k base-to-emitter resistor buys.** The GPIO already pulls
the base low whenever the relay is off, but it goes high-impedance during reset, and the
10 k covers that window so the collector sits in the Vces regime unconditionally. It
diverts 75 uA of the 2.6 mA base drive, which is nothing, and it hardens the base against
injected noise as a side effect. On a 40 V part this would be optional; on a 32 V one it
is the difference between a comfortable margin and a number you have to argue about.

**Why the 150 R dropper.** From the Omron datasheet the 12 V coil is **1315 ohm /
9.1 mA / ~100 mW**, and the "150% maximum" figure is an *instantaneous* rating, not a
continuous one. Straight off 13.5 V the coil would sit at 112% of rated voltage and
**139% of rated power**, which is more than it is specified for continuously. A single
150 R in series makes it 12.1 V and 111 mW — essentially nominal — while leaving plenty
of margin over the **9.6 V must-operate** threshold (80% of rated). It costs one 0603
resistor and 14 mW.

In practice the coil is only energised during a silenced ring, so at most a minute at a
time, and it would very likely survive without the resistor. Fit it anyway: it turns
"probably fine" into "in spec".

**Why an NPN and not a MOSFET.** At 9.2 mA the load is trivial for either, and the 2N7002
that earlier drafts offered as an alternative is in fact the weaker choice: its threshold
runs as high as 3.0 V against only 3.3 V of gate drive. The decisive argument is boot
behaviour. **ESP32-C3 GPIOs are high-impedance during reset**, and a bipolar base with
nothing driving it is *inherently* off, because it needs current rather than voltage to
conduct. A floating MOSFET gate can drift up on leakage and partially enhance, so a
pull-down there is load-bearing; on the BJT the same resistor is belt-and-braces, fitted
for the Vces argument above rather than to stop the relay chattering at power-up.

**Why the BCW65A and not the MMBT2222A** the earlier drafts named. Availability decided
it, but the substitution is a mild upgrade where it counts. The MMBT2222A's gain is
specified at Ic = 150 mA, sixteen times our load, so using it here means extrapolating
down a curve. The BCW65A is characterised at **hFE >= 75 at Ic = 10 mA** — within 8% of
our 9.2 mA — so saturation is guaranteed by the datasheet rather than by inference. With
2.6 mA of base drive we need a gain of only 3.5, so we overdrive roughly 20x and
Vce(sat) lands well under 100 mV. Continuous Ic of 800 mA against 9.2 mA, and 225 mW of
dissipation against about 1 mW, are both irrelevantly generous.

The one genuine regression is Vceo, 32 V against the MMBT2222A's 40 V, handled above. Note
also that neither part is AEC-Q101, unlike U1/Q1/the passives — acceptable for a
low-stress signal transistor that switches a 9 mA coil a few times a week, but it is the
one place the BOM's automotive-grade rule is not held.

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

**`BAT54SLT1G` is not a substitute for the BAT54S — it *is* the BAT54S**, in onsemi's
part numbering, where `LT1` is the SOT-23 tape reel and `G` is Pb-free. Same 30 V / 200 mA
dual series die every other vendor sells. **One thing is worth a second look on the
distributor page: onsemi also lists `SBAT54SLT1G`**, and that *leading* `S` — not the `S`
in `BAT54S`, which just means "series" — marks the **AEC-Q101 qualified, PPAP-capable**
variant, the same convention as the `Q` in the `AP63203QWU`. Identical die, cents apart.
If both are in stock, take the automotive one and the BOM keeps its rule.

**Why a Schottky, and why the number that matters is Vf at 1 mA.** The clamp level *is*
the rail plus Vf, and the ESP32-C3's absolute maximum on a GPIO is only VDD + 0.3 V. A
plain silicon diode at 0.7 V would clamp to 4.0 V and sail straight past that, so the
clamp itself would be the thing that killed the pin. This part is **0.32 V max at 1 mA**
and **0.24 V max at 0.1 mA**, which lands at 3.62 V — inside the rating for all practical
purposes, and the 1 k series resistor is what keeps us down at those low currents rather
than out at the 0.40 V / 10 mA figure.

**Nothing else about it perturbs the bus.** Leakage is 2 uA worst case, and that is
specified at 25 V reverse where we only ever apply 3.3 V, so through the 1 k it is
worth millivolts. Capacitance is 10 pF max per diode, so roughly 20 pF from the node to
AC ground, giving a 20 ns time constant against an **88 us bit time** — five thousand
times too small to matter. And the plausible fault, `C/D` shorted to `+U`, drives about
9.8 mA through the 1 k into the 3.3 V rail: 5% of the diode's DC rating, and a current
the ESP32's own consumption swallows without the rail lifting.

## Four details that will bite if skipped

### 1. The 10 k pull-up on CAN TX is not optional

GPIO21 is a floating input before `setup()` runs, during the listen-only/normal mode
swap, and across every reboot and OTA update. A floating buffer input can drive its
output low, which pulls the bus dominant and **jams the intercom** — no calls, no
door. The pull-up makes "recessive" the default at every instant the firmware is not
in control.

### 2. The status pixel must be a WS2812B, not an SK6812

**Earlier revisions of this document said the `SK6812` was "explicitly rated for 3.3 V"
and that this was the reason to prefer it over a `WS2812B`. Both halves were wrong, and
the truth is the exact reverse.** From the manufacturers' own current figures:

| Part | Supply (VDD) | Internal cap | Reverse prot. | Overvolt. prot. |
|---|---|---|---|---|
| **`WS2812B`** | **3.3 - 5.5 V** | **inside** | **yes** | **yes** |
| `WS2812C` | 3.3 - 5.5 V | no | no | no |
| `WS2812E`, `WS2812S` | **3.8** - 5.5 V | inside | yes | yes |
| `SK6812` (5050) | **3.5** - 5.5 V | - | - | - |
| `SK6812MINI-E` (3228) | **3.7** - 5.5 V | - | - | - |
| Inolux `IN-PI554FCH` | **3.7** - 5.5 V | - | - | - |

So **the `WS2812B` is in spec on our rail and the `SK6812` never was.** World Semi lists
3.3 - 5.5 V across `WS2812A/B/C/D`, in every package including the 3535 `MINI` and the
5050.

**And the headroom worry is exactly what the `V6` revision addresses.** The concern was
real: blue and green dice are InGaN with Vf of 2.8 - 3.4 V, leaving nearly nothing above
them for the driver's current sink at 3.3 V. World Semi's `V6` PCN (30 Sep 2025) claims
precisely that fix — *"Constant-Current Drive at 3.3 V: RGB channel voltage drop
optimization, 3.3 V power supply can achieve the same light emission consistency as 5 V"*
— along with zero power-on flicker, 6 dB less radiated emission, and standby current under
1 uA. `WS2812C-V6` (25 May 2026) carries the same improvement.

**Take the `B`, not the `C`.** They share the 3.3 V rating, and the `C` draws less
(5 mA x 3 against 12 mA x 3), which for an indicator would be welcome. But the `B` has an
**internal capacitor plus reverse-connection and over-voltage protection** and the `C` has
none of the three. On a permanent install inside someone's wall, reverse-connection
protection alone justifies the choice. Avoid `WS2812E` and `WS2812S` outright: 3.8 V
minimum.

**Data levels are a non-issue and the old level-shifter advice is obsolete.** At 3.3 V the
`V6` threshold of 0.6 x VDD is 2.0 V against a 3.3 V drive. Even *at* 5 V, the `V5`
datasheet already specifies VIH as a flat **2.7 V** rather than 0.7 x VDD, so a 3.3 V GPIO
drives a 5 V-powered part directly from `V4` onwards. The widely repeated "you need a
74AHCT125" applies to pre-2019 stock.

**The one real risk is revision, not part number.** `V5` datasheet PDFs still print
3.7 - 5.3 V as the absolute maximum rating, and no AliExpress seller states which revision
is in the bag. The PCN says the inventory switch began immediately and that old and new
batches interoperate, so current stock should be `V6` — but verify rather than assume:
**power one from 3V3 on the bench and check that blue and green are respectable before
committing it to the PCB.** They cost pennies, so buy a handful.

If that test disappoints, the fallback stands: **two discrete low-Vf LEDs, one per
toggle**, red plus amber or GaP yellow-green at ~2.0 - 2.2 V, each with a series resistor.
Fully in spec on 3.3 V with no driver IC at all. Note that a *plain* RGB LED on three PWM
GPIOs is **not** a fallback — same InGaN dice, same dead blue channel, and no clever
current sink to rescue it.

### 3. Check what you are doing to the bus supply

The whole installation — SCU, outdoor panel, every terminal — runs off one supply.
Going straight to 3.3 V keeps our draw on `+U` down to roughly **28 mA average**
(~0.38 W), with brief WiFi peaks. Still measure `+U` before and after fitting it, under
load with the screen on, and confirm it has not sagged. If it has, feed the regulator
from its own supply and take only `C/D` and `GND` from the intercom.

The regulator's 2 ms soft-start helps here: it limits inrush so powering up our node
does not disturb the shared bus.

### 4. `R12` goes to GPIO5, never to 3V3

It is the difference between a node that can transmit and one that only listens, so
it is tempting to tack it to the rail and be done. Do not. A permanent pull-up on
`C/D` turns weak dominant holds into ~58 kHz oscillation on a bus the whole building
shares, and it leaves a low-value path from a dead rail onto that bus. Gated on
GPIO5, the same resistor is active only while we are actually sending a frame. Full
reasoning in [Transmitting on C/D](#transmitting-on-cd-and-why-it-did-not-work-at-first).

## Assembly order

**This order was rewritten on 1 Sep 2026, when a stencil was ordered with the board.**
The previous version populated the circuit in stages — receive path only, then the
transmit buffer, then the assist — and checked after each. That is the right way to build
by hand, and it is impossible from a printed board: paste sits on every pad at once, and
any pad left unpopulated through reflow just grows a solder ball.

Nothing is lost, because staging was never really about population. Its purpose was to
keep a half-built board from disturbing a bus the whole building depends on, and that is
governed by **when `C/D` is connected**, not by when parts are placed. So the gate moves:
one reflow populates everything, then the same checks run in the same order, with the
intercom connection held back until each has passed. Steps 1-4 all happen with `C/D`
disconnected.

Each step still verifies one thing. Do not skip ahead.

1. **Inspect before applying any power.** Under magnification, look for bridges at the
   three tightest places: `U1` pins 1-2, whose 0.35 mm gap is the closest spacing between
   different nets anywhere on the board, then `U2`, then the `J1`/`J3` pin rows. Then meter
   for shorts on `3V3`-to-`GND`, `VIN`-to-`GND`, and `C/D` to either rail. A reflowed board
   is the one moment when a solder bridge is both most likely and cheapest to find.
2. **Confirm the relay fail-safe on the built board.** With the coil unpowered, meter
   continuity from `J2` pin 1 through to `J3` pin 1 — the speaker path must be **closed**.
   This is the check that caught a fail-dangerous error once already, and reflow is a new
   chance to get `K1` rotated 180°.
3. **Power from a bench supply, current-limited — not from the intercom.** The old step
   measured the regulator with its output disconnected, which a populated board no longer
   allows, so limit the current instead: feed `VIN` at about 13.5 V with the supply's limit
   set near 100 mA. Verify the `3V3` rail reads 3.3 V ±4%, confirm the supply is not sitting
   at its limit, and check nothing is getting hot. Verify `+U` polarity before this, at the
   terminal block.
4. **Flash over USB, with the bench supply off.** **Never feed USB 5 V and the regulator
   at once.** Confirm it boots, joins WiFi and appears in Home Assistant. Everything after
   this could in principle go over OTA — but see the OTA note: on this project OTA has
   reported success while continuing to boot the previous image, and USB flashing at
   offset 0 is the path that actually takes.
5. **Exercise everything that does not need the bus, still with `C/D` disconnected.**
   `SW1` is a real button now rather than a jumper across GPIO10, so press it and confirm
   each press advances the state and the status LED follows. Arm Silent and listen for the
   relay. Run **TX path self-test**, which needs no bus and should PASS. Run **Assist
   self-test** too: with `C/D` disconnected it should report **~2000 µs**, which is the
   documented not-connected signature and confirms the test itself is working before you
   rely on it later.
6. **Connect `C/D`. Listen only.** Ring the panel and confirm the log shows `0x0DF`
   `04 03 01 00` and then `04 04`, matching the analyzer captures, with "Bus errors" staying
   at zero — this is the bit-timing test. Then confirm the intercom still works completely
   normally: call, answer, door, screen. That is what proves the node is electrically
   invisible, and it is the check the whole staged approach existed to protect.
7. **Assist self-test on the live bus, before transmitting anything.** OFF should read
   ~44 µs and ON in the single digits of microseconds. Near 22 µs means the assist is too
   weak for this bus and the frame will drive the controller bus-off. Decoder table in
   `docs/perfboard.md`.
8. **Transmit.** Press "Open door", line idle, and only once step 7 passed. **It unlocks
   the building door**, so know who is on the other side of it.
9. **Speaker path last.** Fit the `J2` lead and the `J3` plug, arm Silent, ring, confirm
   silence, then answer and confirm you can hear. This goes last because it is the only
   step that touches the intercom's own wiring.

## Permanent install

There is room behind the main PCB inside the case. Insulate everything with Kapton
before reassembly, keep the regulator's inductor away from the touch pads and the
antenna end of the SuperMini clear of metal, and route the fibre so the LED-to-fibre
junction is shrouded in opaque heat-shrink. Confirm the intercom behaves normally with the case
closed — the touch pads are capacitive and dislike conductive things pressed against
them.

The mode button adds one mechanical constraint to that: `SW1`'s plunger has to line up
with an opening in the housing wall, so **the board's position is now fixed in two axes,
not just tucked in wherever it fits**. Establish where that opening can go before
committing to a board outline, and remember the plunger travel is only a few tenths of a
millimetre — a hole that is a little too deep or slightly misaligned turns the button into
one that never quite actuates.
