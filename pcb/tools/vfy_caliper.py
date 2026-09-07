"""Turn the hand-drawn footprints into a caliper checklist.

Three of this board's footprints were drawn from readings rather than
transcriptions - the two JST-style headers came off a vendor sheet whose
dimension letters were jumbled, and SW1's body/plunger split is inferred - so
the parts need checking against them now that they have arrived. A land pattern
error is cheap to find with a caliper and expensive to find at reflow.

What a caliper can actually reach is a *span between two like features*, not a
pad centre, so this prints centre-to-centre distances and feature sizes rather
than raw pad coordinates. Expected values come from the footprint files
themselves, so this cannot drift out of step with the board.

Tolerance rule of thumb: a pad is oversized relative to its lead, so a part
whose span differs by less than about a quarter of the pad's length in that
direction will still solder. Anything beyond that gets flagged.

Usage:  python pcb/tools/vfy_caliper.py       (needs KiCad's bundled python)
"""
import math
import pathlib

import pcbnew

LIB = str(pathlib.Path(__file__).resolve().parents[1] / 'libs' / 'electra.pretty')
NM = 1e6

# Footprints worth checking, and why each one is on the list.
TARGETS = [
    ('Conn_MicroJST1.25-SHstyle_1x03-1MP_P1.25mm_Vertical_SMD', 'J1',
     'drawn from a vendor sheet with jumbled dimension letters'),
    ('Conn_MicroJST1.25-SHstyle_1x02-1MP_P1.25mm_Vertical_SMD', 'J3',
     'same sheet, same risk'),
    ('SW_Push_Side_CTS_225B_7.8x3.5mm_Boss', 'SW1',
     'body/plunger split inferred; plunger reach never dimensioned'),
]


def mm(v):
    return v / NM


def pad_rows(fp):
    """Pads grouped by name, with centre, size, drill and whether plated."""
    rows = []
    for p in fp.Pads():
        pos = p.GetPosition()
        sz = p.GetSize()
        rows.append(dict(
            name=p.GetNumber() or '-',
            x=mm(pos.x - fp.GetPosition().x),
            y=mm(pos.y - fp.GetPosition().y),
            w=mm(sz.x), h=mm(sz.y),
            drill=mm(p.GetDrillSizeX()) if p.GetDrillSizeX() else 0.0,
            smd=p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD,
        ))
    return rows


def span(a, b):
    return math.hypot(a['x'] - b['x'], a['y'] - b['y'])


def main():
    for fpname, ref, why in TARGETS:
        fp = pcbnew.FootprintLoad(LIB, fpname)
        if fp is None:
            print(f"!! could not load {fpname}")
            continue
        rows = pad_rows(fp)
        print(f"\n{'=' * 72}")
        print(f"{ref}  {fpname}")
        print(f"     on the list because: {why}")
        print(f"{'=' * 72}")

        print("  pads, relative to the footprint origin:")
        for r in sorted(rows, key=lambda r: (r['name'], r['x'])):
            kind = 'SMD' if r['smd'] else f"hole {r['drill']:.2f}"
            print(f"    pad {r['name']:3} at ({r['x']:+6.3f}, {r['y']:+6.3f})  "
                  f"{r['w']:.3f} x {r['h']:.3f} mm   {kind}")

        # Electrical pins: the pitch and the full row span are both measurable
        # on the part with a caliper across the outer two pins.
        pins = sorted([r for r in rows if r['name'].isdigit()],
                      key=lambda r: (r['x'], r['y']))
        if len(pins) >= 2:
            print("\n  MEASURE on the part - pin row:")
            d = span(pins[0], pins[1])
            print(f"    adjacent pin centres      expect {d:.3f} mm"
                  f"   (tol +/-{max(0.10, pins[0]['w'] / 4):.2f})")
            if len(pins) > 2:
                full = span(pins[0], pins[-1])
                print(f"    outer pin centres         expect {full:.3f} mm"
                      f"   across {len(pins)} pins")

        # Anything non-numeric is a mechanical feature: anchor tabs on the
        # headers, frame pads and bosses on the switch.
        mech = [r for r in rows if not r['name'].isdigit()]
        holes = [r for r in rows if r['drill'] > 0]
        if mech:
            print("\n  MEASURE on the part - mechanical features:")
            byname = {}
            for r in mech:
                byname.setdefault(r['name'], []).append(r)
            for name, group in byname.items():
                if len(group) == 2:
                    d = span(group[0], group[1])
                    print(f"    '{name}' pair centres        expect {d:.3f} mm"
                          f"   (tol +/-{max(0.10, group[0]['w'] / 4):.2f})")
                for r in group:
                    print(f"      '{name}' land is {r['w']:.3f} x {r['h']:.3f} mm"
                          f" - the part's tab must sit inside this")
            # Gap from the mechanical row to the pin row, measured as a
            # perpendicular offset in Y, which is what the vendor sheet calls out.
            if pins and mech:
                gap = min(abs(m['y'] - p['y']) for m in mech for p in pins)
                print(f"    mech row to pin row (Y)   expect {gap:.3f} mm centre "
                      f"to centre")
        if holes:
            print("\n  MEASURE on the part - things that go into holes:")
            for r in holes:
                print(f"    pad '{r['name']}' hole is {r['drill']:.2f} mm"
                      f" - the part's post must be smaller than this")
            hpair = sorted(holes, key=lambda r: r['x'])
            if len(hpair) >= 2:
                print(f"    hole centre pitch         expect "
                      f"{span(hpair[0], hpair[-1]):.3f} mm")

        bb = fp.GetBoundingBox(False, False)
        print(f"\n  land pattern envelope: {mm(bb.GetWidth()):.3f} x "
              f"{mm(bb.GetHeight()):.3f} mm")

    print(f"\n{'=' * 72}")
    print("Not covered here, but on the list:")
    print("  SW1 plunger reach - caliper body depth and how far the plunger")
    print("    stands proud. The model assumes 3.0 mm body + 0.5 mm proud to")
    print("    make the 3.5 mm total; if the plunger is shorter than that the")
    print("    housing wall will stop the press.")
    print("  SW1 height - expect 3.80 mm, which the light pipe bracket routes")
    print("    around and the assembly height calc uses.")
    print("  J2 wire OD - the fitted footprint is the OD1.5mm relief variant.")
    print("    Caliper the insulation of whichever wire lands there; if it is")
    print("    nearer 1.0 mm the OD1mm variant was the right pick.")
    print("  Relay K1 energised - 3-4 and 6-5 should close. The NC assignment")
    print("    was wrong once already, in the fail-dangerous direction.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
