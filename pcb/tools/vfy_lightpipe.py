"""What room is there to take LED1's light sideways?

LED1 emits along +Z, out of the top face. The board mounts with that face toward
the wall, so the light has to be turned 90 degrees and taken out to the right in
board coordinates. This reports what sits in that corridor and how much clear
space there is, since the layout is fixed and the guide has to fit around it.

Component heights are not in the board file, so they are listed here from the
datasheets and the notes in docs/wiring.md.
"""

import pcbnew

BRD = r"C:\dev\projects\HA\electra-smart\pcb\board\board.kicad_pcb"
NM = 1e6

# Above-board height in mm. Only the entries traceable to docs/wiring.md are
# listed; everything else is an 0603/SOT-23 flat part under ~1 mm that no guide
# routed above 2 mm can collide with.
#   C6  5.8 mm  "sets the profile on its own" - the tallest part on the board
#   J1/J3 4.75  front elevation, vendor sheet page 2
#   SW1 3.8 mm  BOM line: side-actuated switch 7.8 x 3.5 x 3.8 mm
#   L1  2.1 mm  inductor comparison table
HEIGHTS = {"C6": 5.8, "J1": 4.75, "J3": 4.75, "SW1": 3.8, "L1": 2.1}
TALLEST = 5.8  # C6, the electrolytic


def mm(v):
    return v / NM


def main():
    b = pcbnew.LoadBoard(BRD)

    led = b.FindFootprintByReference("LED1")
    lp = led.GetPosition()
    lx, ly = mm(lp.x), mm(lp.y)
    lbb = led.GetBoundingBox(False, False)

    ebb = b.GetBoardEdgesBoundingBox()
    ex0, ex1 = mm(ebb.GetLeft()), mm(ebb.GetRight())
    ey0, ey1 = mm(ebb.GetTop()), mm(ebb.GetBottom())

    print(f"board edges      : x {ex0:.2f}..{ex1:.2f}   y {ey0:.2f}..{ey1:.2f}")
    print(f"LED1 centre      : ({lx:.2f}, {ly:.2f})")
    print(f"LED1 body        : x {mm(lbb.GetLeft()):.2f}..{mm(lbb.GetRight()):.2f}  "
          f"y {mm(lbb.GetTop()):.2f}..{mm(lbb.GetBottom()):.2f}")
    print(f"LED1 to right edge : {ex1 - lx:.2f} mm")
    print(f"LED1 to left edge  : {lx - ex0:.2f} mm")
    print(f"LED1 to top edge   : {ly - ey0:.2f} mm")
    print(f"LED1 to bottom edge: {ey1 - ly:.2f} mm")

    # Anything whose body overlaps a horizontal corridor through LED1.
    for half in (2.5, 5.0):
        y0, y1 = ly - half, ly + half
        print(f"\n=== corridor +/-{half:.1f} mm in y, to the RIGHT of LED1 ===")
        hits = []
        for fp in b.Footprints():
            ref = fp.GetReference()
            if ref == "LED1":
                continue
            fbb = fp.GetBoundingBox(False, False)
            fx0, fx1 = mm(fbb.GetLeft()), mm(fbb.GetRight())
            fy0, fy1 = mm(fbb.GetTop()), mm(fbb.GetBottom())
            if fx1 < lx:
                continue  # entirely left of the LED
            if fy1 < y0 or fy0 > y1:
                continue  # outside the corridor
            hits.append((fx0, ref, fx0 - lx, fy0, fy1, HEIGHTS.get(ref)))
        hits.sort()
        if not hits:
            print("  clear all the way to the edge")
        for fx0, ref, gap, fy0, fy1, h in hits:
            hs = f"{h:.2f} mm tall" if h else "flat part, under ~1 mm"
            print(f"  {ref:5} starts {gap:5.2f} mm right of LED1  "
                  f"y {fy0:.2f}..{fy1:.2f}  {hs}")

    # A guide is not laid on the board, it flies above it, so only parts taller
    # than the guide's underside can actually block it.
    print("\n=== parts that a guide with a 2.0 mm underside must dodge ===")
    for ref, h in sorted(HEIGHTS.items(), key=lambda kv: -kv[1]):
        fp = b.FindFootprintByReference(ref)
        if fp is None:
            continue
        fbb = fp.GetBoundingBox(False, False)
        side = "right of" if mm(fbb.GetLeft()) >= lx else "left of / under"
        print(f"  {ref:5} {h:.2f} mm tall  x {mm(fbb.GetLeft()):.2f}.."
              f"{mm(fbb.GetRight()):.2f}  y {mm(fbb.GetTop()):.2f}.."
              f"{mm(fbb.GetBottom()):.2f}  ({side} LED1)")
    print(f"  tallest part on the board is C6 at {TALLEST} mm - a guide staying")
    print(f"  under that adds no height to the assembly at all")

    # The bracket's hood has to drop over LED1 and reach the board, so anything
    # close by sets how wide it can be.
    print("\n=== neighbours within 8 mm of LED1, sizing the hood ===")
    near = []
    for fp in b.Footprints():
        ref = fp.GetReference()
        if ref == "LED1":
            continue
        fbb = fp.GetBoundingBox(False, False)
        fx0, fx1 = mm(fbb.GetLeft()), mm(fbb.GetRight())
        fy0, fy1 = mm(fbb.GetTop()), mm(fbb.GetBottom())
        # Edge-to-edge gap from LED1's 5.0 mm package, not its courtyard.
        gx = max(fx0 - (lx + 2.5), (lx - 2.5) - fx1, 0.0)
        gy = max(fy0 - (ly + 2.5), (ly - 2.5) - fy1, 0.0)
        gap = (gx ** 2 + gy ** 2) ** 0.5
        if gap <= 8.0:
            near.append((gap, ref, fx0, fx1, fy0, fy1))
    for gap, ref, fx0, fx1, fy0, fy1 in sorted(near):
        h = HEIGHTS.get(ref)
        hs = f"{h:.2f} mm tall" if h else "flat"
        print(f"  {ref:5} {gap:5.2f} mm clear of the 5050 package   "
              f"x {fx0:.2f}..{fx1:.2f}  y {fy0:.2f}..{fy1:.2f}  {hs}")

    print("\n=== mounting holes, as possible bracket anchors ===")
    for fp in b.Footprints():
        ref = fp.GetReference()
        is_hole = "ountingHole" in fp.GetFPIDAsString() or ref.startswith("H")
        if not is_hole:
            continue
        p = fp.GetPosition()
        hx, hy = mm(p.x), mm(p.y)
        d = ((hx - lx) ** 2 + (hy - ly) ** 2) ** 0.5
        drills = {mm(pad.GetDrillSizeX()) for pad in fp.Pads()}
        ds = ", ".join(f"{v:.2f}" for v in sorted(drills)) or "none"
        print(f"  {ref:5} at ({hx:.2f}, {hy:.2f})  {d:5.2f} mm from LED1  "
              f"drill {ds} mm  [{fp.GetFPIDAsString()}]")

    print("\n=== clear straight run to the right, by y offset ===")
    for off in (-8, -6, -4, -2, 0, 2, 4, 6, 8):
        yy = ly + off
        nearest = ex1
        who = "board edge"
        for fp in b.Footprints():
            if fp.GetReference() == "LED1":
                continue
            fbb = fp.GetBoundingBox(False, False)
            fx0 = mm(fbb.GetLeft())
            if fx0 < lx:
                continue
            if mm(fbb.GetTop()) <= yy <= mm(fbb.GetBottom()) and fx0 < nearest:
                nearest = fx0
                who = fp.GetReference()
        print(f"  y = {ly + off:6.2f} (offset {off:+3d}) : clear to x {nearest:.2f}"
              f"  = {nearest - lx:5.2f} mm of run, blocked by {who}")


main()
