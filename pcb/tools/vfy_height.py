"""How tall is the assembled board, and which part sets the profile?

Several claims in docs/wiring.md rest on C6 being the tallest part ("sets the
profile on its own"), and the light pipe bracket was deliberately flat-topped at
C6's height on the strength of that. So it is worth measuring rather than
repeating.

Everything here is read out of the STEP assembly that KiCad exports, not out of
the individual model files. That is deliberate. Walking the footprints and
loading each `.step` yourself means reapplying each model's own offset and
rotation, and **KiCad applies model rotations with the opposite sign to the
intuitive one** - the same trap that puts a preview bracket 180 degrees out. Get
that wrong and the numbers are quietly nonsense: an early version of this script
stood the ESP32 module on its end and reported 11.35 mm, which is half its
length, while laying C6 on its side and reporting 3.3 mm for a 5.8 mm part.
Letting KiCad do the transforms removes the whole class of error.

Parts are identified by matching each solid back to the nearest footprint
origin, since the STEP export does not carry references through into the shapes.

Run the export first:

    kicad-cli pcb export step --subst-models --no-dnp --force \\
        -o board_asm.step pcb/board/board.kicad_pcb

Usage:  python pcb/tools/vfy_height.py
"""
import math
import pathlib
import re

import cadquery as cq

ROOT = pathlib.Path(__file__).resolve().parents[2]
BRD = ROOT / 'pcb' / 'board' / 'board.kicad_pcb'
ASM = ROOT / 'board_asm.step'
THICKNESS = 1.6        # (thickness 1.6) in the board's stackup
BOARD_TOP = THICKNESS  # KiCad exports with the board's bottom face on z = 0
FUZZ = 0.02            # anything not clearing this is board, copper or mask


def footprints():
    """(ref, x, y) per footprint, in the STEP's coordinates.

    The export negates Y relative to the layout, which is why the assembly's
    bounding box comes back with a negative Y range.
    """
    text = BRD.read_text(encoding='utf-8')
    out = []
    for chunk in text.split('\n\t(footprint ')[1:]:
        ref = re.search(r'\(property "Reference" "([^"]+)"', chunk)
        at = re.search(r'\(at ([-\d.]+) ([-\d.]+)', chunk)
        if ref and at:
            out.append((ref.group(1), float(at.group(1)), -float(at.group(2))))
    return out


def main():
    if not ASM.is_file():
        print(f"{ASM.name} not found - run the kicad-cli export first")
        return 1

    asm = cq.importers.importStep(str(ASM))
    bb = asm.val().BoundingBox()

    fps = footprints()
    tops, orphans = {}, 0
    for solid in asm.val().Solids():
        sb = solid.BoundingBox()
        if sb.zmax <= BOARD_TOP + FUZZ:
            continue                       # the board itself, copper, mask
        cx = (sb.xmin + sb.xmax) / 2
        cy = (sb.ymin + sb.ymax) / 2
        best, bestd = None, 1e9
        for ref, fx, fy in fps:
            d = math.hypot(cx - fx, cy - fy)
            if d < bestd:
                best, bestd = ref, d
        if bestd > 8.0:                    # too far to attribute with confidence
            orphans += 1
            continue
        tops[best] = max(tops.get(best, 0.0), sb.zmax - BOARD_TOP)

    rows = sorted(((z, r) for r, z in tops.items()), reverse=True)
    print("=== how far each part stands above the board's top face ===")
    for z, ref in rows[:12]:
        print(f"  {ref:5} {z:6.3f} mm")

    print(f"\n=== the total ===")
    print(f"  X {bb.xmin:8.3f} .. {bb.xmax:8.3f}   ({bb.xlen:.3f} mm)")
    print(f"  Y {bb.ymin:8.3f} .. {bb.ymax:8.3f}   ({bb.ylen:.3f} mm)")
    print(f"  Z {bb.zmin:8.3f} .. {bb.zmax:8.3f}   ({bb.zlen:.3f} mm)")
    print(f"\n  board {THICKNESS:.1f} mm + tallest part "
          f"{bb.zmax - BOARD_TOP:.3f} mm = {bb.zlen:.3f} mm over all")

    if rows:
        z, ref = rows[0]
        print(f"  {ref} sets the profile at {z:.3f} mm", end='')
        if len(rows) > 1:
            print(f", {z - rows[1][0]:.3f} mm clear of {rows[1][1]} "
                  f"at {rows[1][0]:.3f} mm")
        else:
            print()
        if abs(z - (bb.zmax - BOARD_TOP)) > 0.05:
            print(f"  ! per-part max {z:.3f} disagrees with the assembly's "
                  f"{bb.zmax - BOARD_TOP:.3f} - something went unattributed")
    if orphans:
        print(f"  {orphans} solid(s) too far from any footprint to attribute")

    # J2 is wires soldered into plated holes and has no model, so it is absent
    # from the export. Nothing else on this board is missing a model.
    print("\n  not represented: J2 (bare wires, no 3D model), H1/H2/H3 "
          "(mounting holes)")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
