"""Report R12's placement and the CD / CD_ASSIST routing.

The transmit failure was an edge-speed problem, so this checks the things that
affect it: where R12 sits relative to where C/D enters the board, how long the
assist and bus nets are, and whether the assist trace is wide enough for the
~11.5 mA it carries while a bit is dominant.
"""

import pcbnew

BRD = r"C:\dev\projects\HA\electra-smart\pcb\board\board.kicad_pcb"
NM = 1e6  # nm per mm


def mm(v):
    return v / NM


def main():
    b = pcbnew.LoadBoard(BRD)

    print("=== R12 placement ===")
    r12 = b.FindFootprintByReference("R12")
    if r12 is None:
        print("R12 NOT FOUND")
        return
    pos = r12.GetPosition()
    print(f"  footprint : {r12.GetFPIDAsString()}")
    print(f"  position  : ({mm(pos.x):.3f}, {mm(pos.y):.3f}) mm")
    print(f"  rotation  : {r12.GetOrientationDegrees():.1f} deg")
    print(f"  side      : {'BACK' if r12.IsFlipped() else 'FRONT'}")
    for p in r12.Pads():
        pp = p.GetPosition()
        print(f"  pad {p.GetNumber()}: net={p.GetNetname()!r:14} at ({mm(pp.x):.3f}, {mm(pp.y):.3f})")

    # Where does C/D actually enter the board, and what else is on that net?
    # Net names are hierarchical, so they carry a leading slash.
    print("\n=== members of CD and CD_ASSIST ===")
    for net in ("/CD", "/CD_ASSIST"):
        pads = []
        for fp in b.Footprints():
            for p in fp.Pads():
                if p.GetNetname() == net:
                    q = p.GetPosition()
                    pads.append((f"{fp.GetReference()}.{p.GetNumber()}", mm(q.x), mm(q.y)))
        joined = ", ".join(f"{n} ({x:.2f},{y:.2f})" for n, x, y in pads)
        print(f"  {net:10}: {joined}")

    # Track length and width per net, which is the signal-integrity number here.
    print("\n=== routing ===")
    for net in ("/CD", "/CD_ASSIST", "/CAN_TX_OD", "/CAN_RX", "/CAN_TX"):
        total = 0.0
        widths = set()
        layers = set()
        vias = 0
        for t in b.Tracks():
            if t.GetNetname() != net:
                continue
            if t.Type() == pcbnew.PCB_VIA_T:
                vias += 1
                continue
            total += mm(t.GetLength())
            widths.add(round(mm(t.GetWidth()), 3))
            layers.add(b.GetLayerName(t.GetLayer()))
        print(
            f"  {net:10}: {total:6.2f} mm  widths={sorted(widths)}  "
            f"layers={sorted(layers)}  vias={vias}"
        )

    # Distance from R12 to the connector pin that brings C/D onto the board, and
    # to the buffer output, because both sit on the same node.
    print("\n=== distances from R12 ===")
    anchors = [("J1.2 (C/D in)", "J1", "2"), ("R5.2 (buffer out)", "R5", "2"),
               ("R6.1 (RX tap)", "R6", "1"), ("U3.5 (GPIO5)", "U3", "5")]
    p1 = None
    for p in r12.Pads():
        if p.GetNetname() == "/CD":
            p1 = p.GetPosition()
    if p1 is None:
        print("  R12 has no pad on /CD - cannot measure")
        return
    for label, ref, padnum in anchors:
        fp = b.FindFootprintByReference(ref)
        if fp is None:
            print(f"  {label:20}: {ref} not found")
            continue
        for p in fp.Pads():
            if p.GetNumber() == padnum:
                q = p.GetPosition()
                d = ((mm(q.x) - mm(p1.x)) ** 2 + (mm(q.y) - mm(p1.y)) ** 2) ** 0.5
                print(f"  {label:20}: {d:6.2f} mm")

    # Keepout check: the module antenna zone bans copper, so confirm we are clear.
    print("\n=== antenna keepout ===")
    for i in range(b.GetAreaCount()):
        z = b.GetArea(i)
        if not z.GetIsRuleArea():
            continue
        bb = z.GetBoundingBox()
        x0, x1 = mm(bb.GetLeft()), mm(bb.GetRight())
        y0, y1 = mm(bb.GetTop()), mm(bb.GetBottom())
        inside = x0 <= mm(pos.x) <= x1 and y0 <= mm(pos.y) <= y1
        print(f"  zone x {x0:.1f}..{x1:.1f}  y {y0:.1f}..{y1:.1f}  "
              f"R12 inside: {'YES - PROBLEM' if inside else 'no'}")


main()
