"""Apply the SW1 pad trim to the board's copy of the footprint.

The board embeds its own copy of every footprint, so editing the .kicad_mod alone
leaves the layout unchanged. Sets pads 1 and 2 to the trimmed geometry using
footprint-relative coordinates, so it works whatever rotation SW1 sits at.
"""

import pcbnew

BRD = r"C:\dev\projects\HA\electra-smart\pcb\board\board.kicad_pcb"
NM = 1e6

# Footprint-local geometry, matching the .kicad_mod.
TRIM = {
    "1": ((-2.125, -0.925), (0.85, 1.25)),
    "2": ((2.125, -0.925), (0.85, 1.25)),
}


def mm(v):
    return v / NM


def show(sw1):
    for p in sw1.Pads():
        if p.GetNumber() not in TRIM:
            continue
        rp = p.GetFPRelativePosition()
        sz = p.GetSize()
        print(f"  pad {p.GetNumber()}: local ({mm(rp.x):+.3f}, {mm(rp.y):+.3f})  "
              f"size {mm(sz.x):.3f} x {mm(sz.y):.3f}")


def main():
    b = pcbnew.LoadBoard(BRD)
    sw1 = b.FindFootprintByReference("SW1")
    if sw1 is None:
        print("SW1 not found")
        return

    print(f"SW1 at ({mm(sw1.GetPosition().x):.3f}, {mm(sw1.GetPosition().y):.3f}), "
          f"rotation {sw1.GetOrientationDegrees():.1f} deg\n")
    print("before:")
    show(sw1)

    for p in sw1.Pads():
        num = p.GetNumber()
        if num not in TRIM:
            continue
        (lx, ly), (sx, sy) = TRIM[num]
        p.SetFPRelativePosition(pcbnew.VECTOR2I(int(lx * NM), int(ly * NM)))
        p.SetSize(pcbnew.VECTOR2I(int(sx * NM), int(sy * NM)))

    print("\nafter:")
    show(sw1)

    b.Save(BRD)
    print(f"\nsaved {BRD}")


main()
