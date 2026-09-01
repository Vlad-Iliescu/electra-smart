"""Is the v0.9 silk marking readable on a populated board?

DRC catches silk over pads and mask, but not silk printed underneath a component
body, which is the way a version marking usually becomes useless.
"""

import pcbnew

BRD = r"C:\dev\projects\HA\electra-smart\pcb\board\board.kicad_pcb"
NM = 1e6


def mm(v):
    return v / NM


def main():
    b = pcbnew.LoadBoard(BRD)

    target = None
    for d in b.GetDrawings():
        if d.Type() == pcbnew.PCB_TEXT_T and d.GetText().startswith("v0"):
            target = d
    if target is None:
        print("no version text found")
        return

    bb = target.GetBoundingBox()
    tx0, tx1 = mm(bb.GetLeft()), mm(bb.GetRight())
    ty0, ty1 = mm(bb.GetTop()), mm(bb.GetBottom())
    print(f"text {target.GetText()!r} on {b.GetLayerName(target.GetLayer())}")
    print(f"  bbox x {tx0:.2f}..{tx1:.2f}  y {ty0:.2f}..{ty1:.2f}\n")

    # Board outline, to confirm it is actually on the board and not off the edge.
    ebb = b.GetBoardEdgesBoundingBox()
    ex0, ex1 = mm(ebb.GetLeft()), mm(ebb.GetRight())
    ey0, ey1 = mm(ebb.GetTop()), mm(ebb.GetBottom())
    print(f"board outline x {ex0:.2f}..{ex1:.2f}  y {ey0:.2f}..{ey1:.2f}")
    inside = ex0 <= tx0 and tx1 <= ex1 and ey0 <= ty0 and ty1 <= ey1
    print(f"  text fully inside outline: {'yes' if inside else 'NO - hangs off the edge'}")
    print(f"  clearance to nearest edge: "
          f"{min(tx0 - ex0, ex1 - tx1, ty0 - ey0, ey1 - ty1):.2f} mm\n")

    print("Footprints whose body overlaps the text:")
    hits = 0
    for fp in b.Footprints():
        fbb = fp.GetBoundingBox(False, False)  # pads+graphics, no text
        fx0, fx1 = mm(fbb.GetLeft()), mm(fbb.GetRight())
        fy0, fy1 = mm(fbb.GetTop()), mm(fbb.GetBottom())
        if tx1 < fx0 or fx1 < tx0 or ty1 < fy0 or fy1 < ty0:
            continue
        hits += 1
        print(f"  {fp.GetReference():5} {fp.GetValue():28} "
              f"x {fx0:.2f}..{fx1:.2f}  y {fy0:.2f}..{fy1:.2f}")
    if hits == 0:
        print("  none - the marking stays visible after assembly")


main()
