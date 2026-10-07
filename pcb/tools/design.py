"""Declarative definition of the Electra intercom interface board.

This is the single source of truth for the schematic. gen_sch.py turns it into
pcb/board/board.kicad_sch, so edit here rather than hand-patching the .kicad_sch.

Designators are plain integers throughout (KiCad cannot use refs like "C1b").
See docs/wiring.md for the mapping from the older C1b/C2a/C2b/R3..R11 names.
"""

R0603 = 'Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder'
C0603 = 'Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder'
C1206 = 'Capacitor_SMD:C_1206_3216Metric_Pad1.33x1.80mm_HandSolder'
C1210 = 'Capacitor_SMD:C_1210_3225Metric_Pad1.33x2.70mm_HandSolder'
SOT23 = 'Package_TO_SOT_SMD:SOT-23'

# Placeholder for a part whose footprint depends on a measurement not yet taken.
# Empty on purpose: an empty footprint is caught by the netlist/DRC step, whereas
# a plausible-but-wrong one silently produces an unbuildable board. Nothing uses
# it at the moment - every part resolves - but keep it, and keep check_libs.PENDING
# in step with it, so the next unknown part fails loudly instead of guessing.
TODO_FP = ''

# ref -> (lib_id, value, footprint, x, y, text_side)
PARTS = {
    # --- input protection -------------------------------------------------
    # Same connector family as J3, three ways instead of two, so one kit covers
    # both ends of the board. Carries the raw 13.5 V tap, which is the one thing
    # to keep in mind on a 1.25 mm pitch - see the footprint description.
    'J1':  ('Connector:Conn_01x03_Socket', 'Intercom +U/CD/GND',
            'electra:Conn_MicroJST1.25-SHstyle_1x03-1MP_P1.25mm_Vertical_SMD',
            40, 35, 'top'),
    'F1':  ('Device:Fuse_Small', '0453.250MR',
            'electra:Fuse_2410_6125Metric_Littelfuse_453', 75, 32.5, 'top'),
    'Q1':  ('Transistor_FET:DMP3099L', 'DMP4065SQ-7', SOT23, 110, 32.5, 'top'),
    'R2':  ('Device:R', '100k', R0603, 145, 45, 'right'),
    'R3':  ('Device:R', '100k', R0603, 145, 70, 'right'),
    'D1':  ('Device:D_Zener', 'SMAJ18A', 'Diode_SMD:D_SMA', 180, 32.5, 'top'),
    # Pin 1 is the + terminal and sits on the footprint's chamfered side, which
    # is where Panasonic puts the anode. Reversing it on the 13.5 V rail vents
    # the can, so the silkscreen "+" is not decoration.
    'C6':  ('Device:C_Polarized', '47uF',
            'electra:Capacitor_Panasonic_EEH-ZA_6.3x5.8', 215, 40, 'right'),
    # --- AP63203 buck -----------------------------------------------------
    'C1':  ('Device:C', '10uF', C1206, 40, 105, 'right'),
    'C2':  ('Device:C', '100nF', C0603, 65, 105, 'right'),
    'U1':  ('Regulator_Switching:AP63203WU', 'AP63203QWU-7',
            'Package_TO_SOT_SMD:TSOT-23-6', 110, 105, 'top'),
    'C5':  ('Device:C', '100nF', C0603, 150, 105, 'right'),
    'R1':  ('Device:R', '0R', R0603, 175, 105, 'right'),
    # Pin 1 is the marked terminal: Coilcraft wants the high dv/dt node there,
    # so it faces SW and pin 2 faces the 3V3 output. Do not flip in layout.
    'L1':  ('Device:L', '3.3uH',
            'electra:Inductor_Coilcraft_XGL4020', 205, 105, 'right'),
    'C3':  ('Device:C', '22uF', C1210, 235, 105, 'right'),
    'C4':  ('Device:C', '22uF', C1210, 260, 105, 'right'),
    'C8':  ('Device:C', '10uF', C1206, 285, 105, 'right'),
    # --- mode button ------------------------------------------------------
    # Side-actuated switch: the plunger fires parallel to the board, so SW1
    # has to sit at a board edge with its F.Fab arrow pointing off-board. Its
    # two locating bosses drop into the footprint's NPTH holes and take the
    # press force, which is the whole reason for choosing the bossed variant.
    'SW1': ('Switch:SW_Push_Shielded', 'Mode button',
            'electra:SW_Push_Side_CTS_225B_7.8x3.5mm_Boss', 50, 140, 'top'),
    'R11': ('Device:R', '10k', R0603, 95, 140, 'right'),
    'C9':  ('Device:C', '100nF', C0603, 125, 140, 'right'),
    # --- MCU --------------------------------------------------------------
    'U3':  ('electra:ESP32-C3_SUPERMINI_SMD', 'ESP32-C3 SuperMini',
            'electra:MODULE_ESP32-C3_SUPERMINI', 75, 180, 'top'),
    # --- single-wire CAN interface ----------------------------------------
    'U2':  ('74xGxx:74LVC1G07', 'SN74LVC1G07DBVR',
            'Package_TO_SOT_SMD:SOT-23-5', 160, 180, 'top'),
    'C7':  ('Device:C', '100nF', C0603, 195, 180, 'right'),
    'R4':  ('Device:R', '10k', R0603, 220, 180, 'right'),
    'R5':  ('Device:R', '47R', R0603, 245, 180, 'right'),
    'R6':  ('Device:R', '1k', R0603, 270, 180, 'right'),
    'D3':  ('Diode:BAT54S', 'BAT54SLT1G', SOT23, 305, 180, 'top'),
    # Recessive assist, see the CD_ASSIST net. 240 R is measured, not chosen: it
    # is the value that made a door frame legal on this building's bus. It has to
    # be well below the intercom's own ~1 k pull-up, because a comparable value
    # only halves the recovery time - 1 k measured 22 us of an 87 us bit and every
    # frame was rejected, while 240 R measured 8 us and the panel acknowledged us.
    #
    # Do not shrink it further without checking the other end of the trade. While
    # a bit is dominant, this resistor is still sourcing into the line against R5,
    # so it lifts the dominant level off ground: ~0.28 V at 1 k, ~0.65 V at 240 R,
    # ~0.78 V at 180 R, against a threshold around 1.5 V. 240 R keeps ~0.9 V of
    # margin and costs GPIO5 11.5 mA while dominant. 180 R buys a slightly faster
    # edge by spending that margin, so it is not a free "if skew is still fat" step.
    'R12': ('Device:R', '240R', R0603, 335, 180, 'right'),
    # --- speaker-mute relay ----------------------------------------------
    'R7':  ('Device:R', '1k', R0603, 40, 245, 'right'),
    'R8':  ('Device:R', '10k', R0603, 65, 245, 'right'),
    'Q2':  ('Transistor_BJT:BC850', 'BCW65ALT1G', SOT23, 95, 245, 'top'),
    'D2':  ('Diode:1N4148W', '1N4148W', 'Diode_SMD:D_SOD-123', 130, 240, 'top'),
    'R9':  ('Device:R', '150R', R0603, 165, 245, 'right'),
    'K1':  ('Relay:G6K-2', 'G6K-2F-Y DC12',
            'Relay_SMD:Relay_DPDT_Omron_G6K-2F-Y', 205, 245, 'top'),
    # --- status LED -------------------------------------------------------
    'R10': ('Device:R', '330R', R0603, 250, 245, 'right'),
    'LED1': ('LED:WS2812B', 'WS2812B-V6',
             'LED_SMD:LED_WS2812B_PLCC4_5.0x5.0mm_P3.2mm', 280, 245, 'right'),
    # --- speaker pass-through --------------------------------------------
    # The wire ends solder into two plated 0.7 mm holes, and the 2.0 mm holes
    # 9 mm behind them are the strain relief: the wire feeds through those so any
    # pull is taken by the board rather than by the solder joints. Stock KiCad
    # part, dimensioned for a 0.5 mm conductor in 1.5 mm insulation, which is
    # silicone-clad 26 AWG. Genderless symbol because nothing plugs in on this
    # end - it is bare pads, not a socket.
    'J2':  ('Connector_Generic:Conn_01x02', 'To intercom J101',
            'Connector_Wire:SolderWire-0.15sqmm_1x02_P4mm_D0.5mm_OD1.5mm_Relief',
            340, 235, 'top'),
    # Drawn from the vendor sheet, because this is not GH and the GH footprint
    # that used to sit here would have been a dead board. The body scales as pin
    # span + 3.0 mm, which is JST SH's proportion against GH's 4.5, so the part
    # is an SH shape stretched to a 1.25 mm pitch. Two dimensions in the sheet
    # are reasoned rather than stated - see the footprint's own description -
    # so the anchor-tab span still wants a caliper before fab.
    'J3':  ('Connector:Conn_01x02_Socket', 'Speaker',
            'electra:Conn_MicroJST1.25-SHstyle_1x02-1MP_P1.25mm_Vertical_SMD',
            340, 265, 'top'),
    # --- ERC power sources ------------------------------------------------
    '#FLG1': ('power:PWR_FLAG', 'PWR_FLAG', '', 250, 35, 'top'),
    '#FLG2': ('power:PWR_FLAG', 'PWR_FLAG', '', 320, 105, 'top'),
    '#FLG3': ('power:PWR_FLAG', 'PWR_FLAG', '', 355, 105, 'top'),
}

# net -> [(ref, pin, expected_pin_name_or_None)]
# The third element is asserted against the library symbol so that a polarity
# or pinout mistake fails generation loudly instead of shipping a bad netlist.
NETS = {
    # Raw intercom feed, ahead of the fuse.
    '+U': [('J1', '1', 'Pin_1'), ('F1', '1', None)],

    # Fused, ahead of the reverse-polarity FET.
    '+U_F': [('F1', '2', None), ('Q1', '3', 'D')],

    # Protected input rail. Q1 conducts drain->source in normal polarity and
    # blocks when the feed is reversed. Relay coil taps here, downstream of
    # both F1 and D1, as docs/wiring.md requires.
    'VIN': [
        ('Q1', '2', 'S'), ('R2', '1', None), ('D1', '1', 'K'),
        ('C6', '1', None), ('C1', '1', None), ('C2', '1', None),
        ('U1', '3', 'IN'), ('U1', '2', 'EN'), ('R9', '1', None),
        ('#FLG1', '1', None),
    ],

    # Q1 gate divider: halves VIN onto the gate so Vgs stays inside +/-20 V
    # even when D1 is clamping at ~29 V.
    'Q1_G': [('Q1', '1', 'G'), ('R2', '2', None), ('R3', '1', None)],

    'SW': [('U1', '5', 'SW'), ('L1', '1', '1'), ('R1', '2', None)],
    'BST': [('U1', '6', 'BST'), ('C5', '1', None)],
    'BST_C': [('C5', '2', None), ('R1', '1', None)],

    # AP63203 is the fixed 3.3 V version, so FB ties straight to the output.
    '3V3': [
        ('L1', '2', '2'), ('U1', '1', 'FB'), ('C3', '1', None), ('C4', '1', None),
        ('C8', '1', None), ('U3', '3.3', '3V3'), ('U2', '5', 'VCC'),
        ('C7', '1', None), ('LED1', '1', 'VDD'), ('R4', '1', None),
        ('D3', '2', 'K'), ('R11', '1', None), ('#FLG2', '1', None),
    ],

    'GND': [
        ('J1', '3', 'Pin_3'), ('R3', '2', None), ('D1', '2', 'A'),
        ('C6', '2', None), ('C1', '2', None), ('C2', '2', None),
        ('U1', '4', 'GND'), ('C3', '2', None), ('C4', '2', None),
        ('C8', '2', None), ('U2', '3', 'GND'), ('C7', '2', None),
        ('U3', 'G', 'GND'), ('LED1', '3', 'VSS'), ('D3', '1', 'A'),
        ('Q2', '2', 'E'), ('R8', '2', None), ('C9', '2', None),
        ('SW1', '2', '2'), ('SW1', 'SH', 'B'), ('#FLG3', '1', None),
    ],

    # TWAI TX out of the ESP32 into the open-drain buffer. R4 holds the line
    # recessive while the ESP32 boots with its GPIOs floating.
    'CAN_TX': [('U3', '21', 'GPIO21'), ('U2', '2', None), ('R4', '2', None)],
    'CAN_TX_OD': [('U2', '4', None), ('R5', '1', None)],

    # The intercom's single-wire CAN bus.
    'CD': [('J1', '2', 'Pin_2'), ('R5', '2', None), ('R6', '1', None),
           ('R12', '2', None)],

    # Recessive assist, and the reason transmitting did not work at all until it
    # existed. U2 is open-drain, so it can only sink; nothing on this board pulled
    # C/D back up, leaving that to the intercom's own pull-up. Measured on the
    # wall, releasing the line takes ~44 us of an 87 us bit while the terminal is
    # active, and ~600 us when it is at rest (7 Oct 2026). Every dominant bit we
    # sent overran its slot, so other nodes mis-sampled the frame and answered
    # with an error flag - which reads as "never acknowledged" from our side and
    # drove the controller bus-off on all 32 retries.
    #
    # The bus pull-up is about 1 k: adding 1 k in parallel halved the recovery to
    # 22 us, and only an equal resistor does that. Hence R12 at 240 R, which took
    # it to 8 us and produced the first frame the panel acknowledged.
    #
    # R12 pulls the line up, but only while a frame is going out. Driven
    # permanently it fights whatever holds the bus dominant weakly - that showed
    # up as bursts of ~58 kHz relaxation oscillation - and it would leave a
    # low-value path to a dead rail on shared building wiring. GPIO5 is an input
    # at every other instant, including before setup() runs and while the board is
    # unpowered, which preserves the fail-safe the rest of this design is built on.
    #
    # This is roughly how a single-wire CAN transceiver behaves: recessive is
    # driven, but only by the node that is talking. A transceiver does it better,
    # by following the transmitted bit so it stops sourcing during dominant bits.
    # A 74LVC1G125 with its input on CAN_TX and /OE gated by GPIO5 would reproduce
    # that and let R12 grow again; it was considered and set aside to keep the
    # proven circuit. Revisit only if the dominant margin above becomes a problem.
    'CD_ASSIST': [('U3', '5', 'GPIO5'), ('R12', '1', None)],

    # RX with a series resistor and a BAT54S clamping to the 3V3 rail / GND.
    'CAN_RX': [('R6', '2', None), ('U3', '20', 'GPIO20'), ('D3', '3', 'COM')],

    'RELAY_EN': [('U3', '6', 'GPIO6'), ('R7', '1', None)],
    # R8 holds the base down so the relay cannot chatter while the ESP32 boots.
    'Q2_B': [('R7', '2', None), ('Q2', '1', 'B'), ('R8', '1', None)],
    # Coil polarity MEASURED on a loose part (2 Oct 2026) and on board 1: the
    # G6K is a polarised relay and the Omron drawing (G6K.pdf p.6) marks the
    # coil + on pin 1 and - on pin 8. v0.9 had them the other way round, Q2
    # saturated and ~8 mA flowed, and the relay never moved; the same part on
    # the bench operated with + on pin 1. COIL_HI (+U via R9) is pin 1,
    # COIL_LO (Q2 collector) is pin 8. D2 stays cathode-to-COIL_HI. The symbol
    # has no polarity on its coil pins, so this comment and the assertion
    # below are the only guard.
    'COIL_LO': [('Q2', '3', 'C'), ('K1', '8', None), ('D2', '2', 'A')],
    'COIL_HI': [('K1', '1', None), ('D2', '1', 'K'), ('R9', '2', None)],

    'LED_DATA': [('U3', '7', 'GPIO7'), ('R10', '1', None)],
    'LED_DIN': [('R10', '2', None), ('LED1', '4', 'DIN')],

    # Mode button, active low. GPIO10 has no strapping function on the C3, so
    # holding the button down at power-up cannot put the chip into download
    # mode the way GPIO9 would. R11 defines the pin while the ESP32 boots with
    # its GPIOs floating, and C9 absorbs contact bounce plus whatever ESD comes
    # in through the housing opening the plunger pokes out of.
    'BTN': [
        ('U3', '10', 'GPIO10'), ('R11', '2', None),
        ('SW1', '1', '1'), ('C9', '1', None),
    ],

    # Speaker path. Both relay poles are paralleled: de-energised the speaker
    # is connected (fail-safe), and two contacts in parallel lower contact
    # resistance and add redundancy on a low-level audio signal.
    # Contact roles MEASURED on the actual part (23 Aug 2026), agreeing with the
    # Omron drawing: COM = 3/6 (centre pins), NC = 2/7 (coil-end pins),
    # NO = 4/5. The first revision had NC and NO swapped - an unpowered board
    # would have muted the intercom - which is exactly what the pre-fab meter
    # check exists to catch. Do not "tidy" this back to 4/5.
    'SPK_HOT': [('J2', '1', 'Pin_1'), ('K1', '3', None), ('K1', '6', None)],
    'SPK_SW': [('K1', '2', None), ('K1', '7', None), ('J3', '1', 'Pin_1')],
    'SPK_RET': [('J2', '2', 'Pin_2'), ('J3', '2', 'Pin_2')],
}

# Pins deliberately left open.
NO_CONNECT = (
    [('U3', p) for p in ('0', '1', '2', '3', '4', '8', '9', '5V')]
    + [('U2', '1'), ('LED1', '2'), ('K1', '4'), ('K1', '5')]
)


def _pins(net):
    return {(r, p) for r, p, _ in NETS[net]}


# K1 is polarised: + on pin 1, - on pin 8 (Omron G6K.pdf p.6). Measured wrong
# on v0.9, so this is checked, not trusted. COIL_HI is the +U side.
assert ('K1', '1') in _pins('COIL_HI') and ('K1', '8') in _pins('COIL_LO'), \
    'K1 coil polarity: +U side (COIL_HI) must be pin 1, Q2 side (COIL_LO) pin 8'
assert ('D2', '1') in _pins('COIL_HI') and ('D2', '2') in _pins('COIL_LO'), \
    'D2 flyback: cathode (pin 1) on COIL_HI, anode (pin 2) on COIL_LO'
# Contacts, measured 23 Aug 2026: NC = 2/7, COM = 3/6, NO = 4/5 open.
assert {('K1', '2'), ('K1', '7')} <= _pins('SPK_SW'), 'K1 NC contacts are 2/7'
assert {('K1', '3'), ('K1', '6')} <= _pins('SPK_HOT'), 'K1 COM contacts are 3/6'
assert {('K1', '4'), ('K1', '5')} <= set(NO_CONNECT), 'K1 NO contacts 4/5 stay open'

PAPER = 'A3'
