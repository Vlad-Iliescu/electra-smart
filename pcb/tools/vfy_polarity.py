"""Print a placement checklist for every part that can go down the wrong way.

Only a handful of parts on this board can be placed rotated and still land on
their pads: anything with a symmetric pad pattern - two-terminal polarised
parts, the 3+3 TSOT-23-6, the 4+4 relay, the 2+2 LED. SOT-23 and SC-70 cannot
be misplaced without visibly missing their pads, so they are listed only for
completeness. For each part this prints where every pad sits in board
coordinates and which net it carries, plus any pin-1 silk mark the footprint
draws, so a photo of the placed board can be checked pad by pad against the
design instead of by memory.

Board coordinates: x grows to the right, y grows DOWN, as in pcbnew. The board
edge nearest each pad is named so the output reads as "the pad toward the top
edge" rather than as raw numbers.

Usage:  "C:/Program Files/KiCad/10.0/bin/python.exe" pcb/tools/vfy_polarity.py
"""
import pathlib

import pcbnew

BOARD = pathlib.Path(__file__).resolve().parents[1] / 'board' / 'board.kicad_pcb'
NM = 1e6

# (reference, can it be misplaced onto its own pads?, what to look for on the part)
TARGETS = [
    ('C6', True, 'black band on the can = NEGATIVE, must sit over the GND pad'),
    ('D1', True, 'SMA cathode band toward the VIN-side pad'),
    ('D2', True, 'SOD-123 cathode band toward the +U/150R side (K1 coil B)'),
    ('L1', True, 'printed bar = start lead, over the SW pad'),
    ('U1', True, 'TSOT-23-6: pin-1 dot; 3+3 pads so 180 deg is possible'),
    ('K1', True, 'G6K: pin-1 mark on the body; 4+4 pins so 180 deg is possible'),
    ('LED1', True, 'WS2812B: cut corner marks pin 1 (VDD on B-V6? check sheet)'),
    ('D3', False, 'SOT-23, 2+1 pads, only one way fits'),
    ('Q1', False, 'SOT-23, 2+1 pads, only one way fits'),
    ('Q2', False, 'SOT-23, 2+1 pads, only one way fits'),
    ('U2', False, 'SC-70-5, 3+2 pads, only one way fits'),
]


def mm(v):
    return v / NM


def edge_word(bb, x, y):
    """Which board edge is a point nearest to, in words."""
    d = {
        'left edge': x - mm(bb.GetLeft()),
        'right edge': mm(bb.GetRight()) - x,
        'top edge': y - mm(bb.GetTop()),
        'bottom edge': mm(bb.GetBottom()) - y,
    }
    return min(d, key=d.get)


def main():
    b = pcbnew.LoadBoard(str(BOARD))
    bb = b.GetBoardEdgesBoundingBox()
    print('board x %.2f..%.2f  y %.2f..%.2f  (y grows downward)\n'
          % (mm(bb.GetLeft()), mm(bb.GetRight()), mm(bb.GetTop()), mm(bb.GetBottom())))
    for ref, risky, hint in TARGETS:
        fp = b.FindFootprintByReference(ref)
        if fp is None:
            print('%s: not on board' % ref)
            continue
        p = fp.GetPosition()
        tag = 'CHECK' if risky else 'self-keying'
        print('%-5s %-11s centre (%.2f, %.2f) rot %4.0f   %s'
              % (ref, tag, mm(p.x), mm(p.y), fp.GetOrientationDegrees(), fp.GetFPIDAsString()))
        print('      look for: %s' % hint)
        pads = sorted(fp.Pads(), key=lambda q: (q.GetNumber().rjust(3)))
        for pad in pads:
            q = pad.GetPosition()
            x, y = mm(q.x), mm(q.y)
            print('      pad %-3s (%6.2f, %6.2f)  %-9s  toward %s'
                  % (pad.GetNumber(), x, y, pad.GetNetname(), edge_word(bb, x, y)))
        for g in fp.GraphicalItems():
            if g.GetLayerName() != 'F.SilkS':
                continue
            shp = g.GetShapeStr() if hasattr(g, 'GetShapeStr') else ''
            if shp == 'Circle':
                c = g.GetCenter()
                print('      silk circle at (%.2f, %.2f)' % (mm(c.x), mm(c.y)))
        print()


if __name__ == '__main__':
    main()
