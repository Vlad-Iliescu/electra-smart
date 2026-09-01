"""Nudge C8's reference text off R12's pad.

Placing R12 put its CD_ASSIST pad under C8's reference designator, which DRC
flags as silkscreen clipped by solder mask. Cosmetic, but it means the board
would come back with a half-printed 'C8'. Moves the text only; no copper changes.
"""

import pcbnew

BRD = r"C:\dev\projects\HA\electra-smart\pcb\board\board.kicad_pcb"
NM = 1e6


def mm(v):
    return v / NM


def report(b):
    c8 = b.FindFootprintByReference("C8")
    r12 = b.FindFootprintByReference("R12")
    ref = c8.Reference()
    print(f"  C8 body at ({mm(c8.GetPosition().x):.3f}, {mm(c8.GetPosition().y):.3f})")
    print(f"  C8 ref  at ({mm(ref.GetPosition().x):.3f}, {mm(ref.GetPosition().y):.3f})"
          f"  layer={b.GetLayerName(ref.GetLayer())}")
    bb = ref.GetBoundingBox()
    print(f"  C8 ref bbox x {mm(bb.GetLeft()):.3f}..{mm(bb.GetRight()):.3f}"
          f"  y {mm(bb.GetTop()):.3f}..{mm(bb.GetBottom()):.3f}")
    for p in r12.Pads():
        pb = p.GetBoundingBox()
        print(f"  R12 pad {p.GetNumber()} bbox x {mm(pb.GetLeft()):.3f}..{mm(pb.GetRight()):.3f}"
              f"  y {mm(pb.GetTop()):.3f}..{mm(pb.GetBottom()):.3f}")


def main():
    b = pcbnew.LoadBoard(BRD)
    print("before:")
    report(b)

    c8 = b.FindFootprintByReference("C8")
    ref = c8.Reference()

    # Absolute, because this is boxed in on three sides: R12's pad 1 to the right
    # (left edge 58.880), C8's own pad 2 to the left, and C8's outline below. Keep
    # the original Y, which DRC already accepted, and shift left only far enough to
    # leave ~0.33 mm to the pad. Moving down as well runs into C8's own outline.
    TARGET_X, TARGET_Y = 57.45, 48.09
    ref.SetPosition(pcbnew.VECTOR2I(int(TARGET_X * NM), int(TARGET_Y * NM)))

    print("\nafter:")
    report(b)
    b.Save(BRD)
    print(f"\nsaved {BRD}")


main()
