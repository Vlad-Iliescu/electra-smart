"""Measure SW1's NPTH boss holes against nearby copper.

Both hole_clearance exclusions are here. The number that matters is the gap from
the drilled hole edge to the nearest copper edge: a fab quotes a minimum for it,
and below that the drill can break out into the pad.
"""

import pcbnew

BRD = r"C:\dev\projects\HA\electra-smart\pcb\board\board.kicad_pcb"
NM = 1e6


def mm(v):
    return v / NM


def rect_of(pad):
    """Axis-aligned copper extent of a pad, in mm."""
    bb = pad.GetBoundingBox()
    return mm(bb.GetLeft()), mm(bb.GetRight()), mm(bb.GetTop()), mm(bb.GetBottom())


def point_to_rect(px, py, r):
    x0, x1, y0, y1 = r
    dx = max(x0 - px, 0.0, px - x1)
    dy = max(y0 - py, 0.0, py - y1)
    return (dx * dx + dy * dy) ** 0.5


def main():
    b = pcbnew.LoadBoard(BRD)
    sw1 = b.FindFootprintByReference("SW1")

    holes = []
    coppers = []
    for p in sw1.Pads():
        d = p.GetDrillSize()
        if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH and d.x > 0:
            pos = p.GetPosition()
            holes.append((mm(pos.x), mm(pos.y), mm(d.x) / 2.0))
        else:
            coppers.append((p.GetNumber(), p.GetNetname(), rect_of(p)))

    print(f"SW1 has {len(holes)} NPTH boss holes and {len(coppers)} copper pads\n")

    worst = 1e9
    for i, (hx, hy, hr) in enumerate(holes, 1):
        print(f"boss hole {i}: centre ({hx:.3f}, {hy:.3f}), diameter {hr * 2:.2f} mm")
        for num, net, r in coppers:
            centre_gap = point_to_rect(hx, hy, r)
            edge_gap = centre_gap - hr
            worst = min(worst, edge_gap)
            flag = ""
            if edge_gap < 0:
                flag = "  <-- HOLE OVERLAPS COPPER"
            elif edge_gap < 0.25:
                flag = "  <-- below the 0.25 mm rule"
            print(f"    pad {num:4} ({net or 'no net':8}): hole edge to copper "
                  f"{edge_gap:6.3f} mm{flag}")
        print()

    print(f"worst hole-edge-to-copper gap: {worst:.3f} mm")
    print("\nAlso check the boss holes against each other and against the board:")
    if len(holes) == 2:
        (ax, ay, ar), (bx, by, br) = holes
        centre = ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5
        print(f"  hole-to-hole centre pitch : {centre:.3f} mm")
        print(f"  hole-to-hole edge gap     : {centre - ar - br:.3f} mm")


main()
