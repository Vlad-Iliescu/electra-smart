"""Build the 3D model for the 1.25 mm vertical SMD headers, J1 and J3.

One script for both, because the two differ only in pin count: the vendor sheet
gives pin span A = (N-1) x 1.25, plastic body C = A + 1.95 and overall width
B = A + 3.00, and every other dimension is shared. Run with a pin count:

    python pcb/tools/model_jst125.py 3     # J1, the intercom tap
    python pcb/tools/model_jst125.py 2     # J3, the speaker

The height is the number worth having and the one the footprint never needed:
**4.75 mm**, off the front elevation on page 2 of docs/datasheets/JST 1.25.pdf.
These are top-entry, so the plug comes down from above and the clearance question
is not the body but the headroom over it - the mating crimp housing on page 1 is
4.0 mm tall, and fingers or pliers need room above that again.

Reading that sheet takes care, because its views are unlabelled and **its letters
disagree with its own table**: in the plan view the wider span is marked A and the
narrower C, while the table has A as the smallest column. The table is the one to
trust, which is also what the physical proportions confirm - C = 4.45 on a 3-way
part is the only one of the three that can be the plastic body.

Coordinates are KiCad's model frame: millimetres, Z up from the board, and Y
negated relative to the footprint, so the pin row that sits at footprint +Y is at
-Y here and the anchor tabs are at +Y. Verify with pcb/tools/check_3d.py.
"""
import pathlib
import sys

import cadquery as cq

OUTDIR = pathlib.Path(__file__).resolve().parents[1] / 'libs' / 'electra.3dshapes'

PITCH = 1.25
DEPTH_Y = 3.70        # plan view, and it matches the footprint's F.Fab
HEIGHT_Z = 4.75       # front elevation
PLUG_Z = 4.0          # the mating crimp housing, page 1 - for the headroom note

# The body straddles the origin unevenly: the footprint's F.Fab runs from -2.40 to
# +1.30 in its own frame, which negates to -1.30 .. +2.40 here.
BODY_Y_FRONT = -1.30
BODY_Y_BACK = 2.40

WALL = 0.40           # cavity wall, not dimensioned - inferred from the section
FLOOR = 1.10          # cavity floor height, likewise
TAB_T = 0.20          # anchor tab foot thickness
TAB_UP = 1.60         # how far the tab climbs the housing end
TAB_IN = 1.00         # how far the foot reaches back under the housing end, so it
                      # covers its 2.00 x 3.00 mm pad instead of perching on a sliver
# The anchor pads sit at footprint y -2.60..+0.40, which negates to this.
ANCHOR_Y_FRONT = -0.40
ANCHOR_Y_BACK = 2.60
TOE_T = 0.15
TOE_W = 0.30
# Reaches from the body's front face to the far end of the signal pads, which sit at
# footprint y +1.00..+2.60, i.e. -1.00 .. -2.60 here. Any longer and the toe hangs
# off its own pad, which looks like a footprint error in the 3D view.
TOE_LEN = 1.30

BEIGE = cq.Color(0.87, 0.79, 0.62)
STEEL = cq.Color(0.78, 0.78, 0.81)


def dims(n):
    a = (n - 1) * PITCH
    return a, a + 1.95, a + 3.00       # pin span, plastic body C, overall B


def build(n):
    _a, body_x, overall_x = dims(n)
    cy = (BODY_Y_FRONT + BODY_Y_BACK) / 2

    housing = (cq.Workplane('XY')
               .box(body_x, DEPTH_Y, HEIGHT_Z, centered=(True, True, False))
               .translate((0, cy, 0))
               .edges('|Z').fillet(0.2))
    # Top-entry cavity: cut straight through the top face.
    cavity = (cq.Workplane('XY')
              .box(body_x - 2 * WALL, DEPTH_Y - 2 * WALL, HEIGHT_Z,
                   centered=(True, True, False))
              .translate((0, cy, FLOOR)))
    housing = housing.cut(cavity)

    # Anchor tabs: the metal ends that take the insertion and extraction load, and
    # the reason the footprint gives them 2.00 x 3.00 mm of copper each.
    tab_w = overall_x / 2 - body_x / 2
    anchor_len = ANCHOR_Y_BACK - ANCHOR_Y_FRONT
    anchor_cy = (ANCHOR_Y_FRONT + ANCHOR_Y_BACK) / 2
    metal = None
    for sx in (-1, 1):
        # The foot runs in under the housing so it lands on its pad; the overlap is
        # buried inside the plastic and never shows.
        foot = (cq.Workplane('XY')
                .box(tab_w + TAB_IN, anchor_len, TAB_T, centered=(False, True, False))
                .translate((body_x / 2 - TAB_IN if sx > 0 else -overall_x / 2,
                            anchor_cy, 0)))
        wall = (cq.Workplane('XY')
                .box(tab_w, DEPTH_Y, TAB_UP, centered=(False, True, False))
                .translate((body_x / 2 if sx > 0 else -overall_x / 2, cy, TAB_T)))
        metal = foot.union(wall) if metal is None else metal.union(foot).union(wall)

    # Contact toes reaching forward under the pin row, plus the blades standing in
    # the cavity so the top view shows something recognisable.
    first = -(n - 1) * PITCH / 2
    for i in range(n):
        x = first + i * PITCH
        toe = (cq.Workplane('XY')
               .box(TOE_W, TOE_LEN, TOE_T, centered=(True, False, False))
               .translate((x, BODY_Y_FRONT - TOE_LEN, 0)))
        blade = (cq.Workplane('XY')
                 .box(TOE_W, 0.30, HEIGHT_Z - FLOOR - 0.6, centered=(True, True, False))
                 .translate((x, BODY_Y_FRONT + WALL + 0.25, FLOOR)))
        metal = metal.union(toe).union(blade)

    asm = cq.Assembly(name='Conn_MicroJST1.25-SHstyle_1x%02d' % n)
    asm.add(housing, name='housing', color=BEIGE)
    asm.add(metal, name='contacts', color=STEEL)
    return asm


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    a, body_x, overall_x = dims(n)
    asm = build(n)
    out = OUTDIR / ('Conn_MicroJST1.25-SHstyle_1x%02d-1MP_P1.25mm_Vertical_SMD.step' % n)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    asm.save(str(out))

    bb = asm.toCompound().BoundingBox()
    print(f'wrote {out.name}   ({n} way: A={a:.2f} C={body_x:.2f} B={overall_x:.2f})')
    print(f'  X {bb.xmin:+.3f} .. {bb.xmax:+.3f}   ({bb.xlen:.3f} wide, '
          f'expect {overall_x:.2f})')
    print(f'  Y {bb.ymin:+.3f} .. {bb.ymax:+.3f}   ({bb.ylen:.3f} over the toes; '
          f'body {DEPTH_Y})')
    print(f'  Z {bb.zmin:+.3f} .. {bb.zmax:+.3f}   (expect {HEIGHT_Z})')
    print(f'  headroom: {HEIGHT_Z} mm of header, mating plug {PLUG_Z} mm tall, '
          f'and it is top-entry - leave room above for fingers')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
