"""Build the 3D model for SW1, the side-push mode button.

Parametric on purpose. The vendor drawing (docs/datasheets/Side Switch button.pdf)
is a raster scan of a projection whose views are not labelled, and two of its
numbers are genuinely ambiguous, so the dimensions below are a reading of it
rather than a transcription. Keeping them as named constants means correcting one
is a one-line edit and a re-run, not a remodelling job.

Why this part earns a model at all, when a switch is electrically trivial: it is
the only part on the board whose position is constrained by something off the
board. The plunger has to line up with a hole in the housing wall and protrude far
enough to be pressed. That is a 3D question, and nothing in ERC or DRC can answer it.

Coordinates are KiCad's model frame: millimetres, Z up from the board surface, and
**Y negated relative to the footprint**, because a footprint's Y grows downward
while the 3D scene's grows up. So the plunger, which points at footprint +Y, is
built pointing at -Y here. That flip is the single easiest thing to get wrong -
it is what left the vendor STEP models buried in the board earlier - so verify the
result with pcb/tools/check_3d.py rather than trusting it.

Usage:  python pcb/tools/model_sw1.py
"""
import pathlib

import cadquery as cq

OUT = (pathlib.Path(__file__).resolve().parents[1] / 'libs' /
       'electra.3dshapes' / 'SW_Push_Side_3.5x7.8x3.8_Boss.step')

# --- dimensions, mm -------------------------------------------------------
# Confident: the title block reads 3.5 x 7.8 x 3.8, and 7.0 is dimensioned on
# the body in the elevation.
BODY_X = 7.0          # plastic body width. The footprint's F.Fab says 6.9,
                      # taken from the CTS 225B sheet; this clone's own drawing
                      # says 7.0, so the model uses the larger, safer figure.
OVERALL_X = 7.8       # across the frame lead toes
TOTAL_Z = 3.8         # the drawing offers H = 3.5 or 3.8; ours is the 3.8 variant

# Inferred: 3.5 is the overall depth, and the body is 3.0 with the plunger making
# up the remaining 0.5. That split matches the footprint's F.Fab body of 3.0 and
# the CTS sheet, and it is the reading that makes the title's 3.5 come out right.
# ** Caliper this on arrival - see the note in docs/wiring.md. **
BODY_Y = 3.0
PLUNGER_OUT = 0.5     # how far the plunger stands proud of the body face

PLUNGER_X = 3.0       # the drawing's lone '3' dimension
PLUNGER_Z = 2.0       # measured off the face-on view of the actuator

LEAD_T = 0.15         # foot thickness; the drawing caps it at 0.3
FRAME_LEAD_Y = 0.9    # frame lead width, along Y
FRAME_LEAD_CY = -0.95  # its centre, mirroring the SH pads at footprint +0.95
SWITCH_LEAD_X = 0.6   # switch terminal width, along X
SWITCH_LEAD_CX = 2.1  # +/- , matching pads 1 and 2 at footprint +/-2.1
SWITCH_LEAD_CY = 0.9  # mirroring pads 1 and 2 at footprint -0.9
SWITCH_LEAD_Y = 1.3

BOSS_D = 0.7          # '2-o0.7' on the drawing, into 0.9 mm holes
BOSS_LEN = 0.7
BOSS_PITCH = 2.3
BOSS_CY = -0.15       # mirroring the NPTH pads at footprint +0.15

IVORY = cq.Color(0.93, 0.91, 0.84)
BLACK = cq.Color(0.13, 0.13, 0.14)
STEEL = cq.Color(0.76, 0.76, 0.79)


def build():
    body_z = TOTAL_Z - LEAD_T
    body = (cq.Workplane('XY')
            .box(BODY_X, BODY_Y, body_z, centered=(True, True, False))
            .translate((0, 0, LEAD_T))
            .edges('|Z').fillet(0.2))

    # Plunger: stands proud of the -Y face, centred in X, centred on the body height.
    plunger = (cq.Workplane('XY')
               .box(PLUNGER_X, PLUNGER_OUT, PLUNGER_Z, centered=(True, False, False))
               .translate((0, -BODY_Y / 2 - PLUNGER_OUT, LEAD_T + (body_z - PLUNGER_Z) / 2)))

    # Frame leads: gull-wing toes reaching out past the body in X, load-bearing on
    # a side-push, which is why the footprint ties them to GND as SH.
    tab = OVERALL_X / 2 - BODY_X / 2 + 0.1
    leads = cq.Workplane('XY')
    for sx in (-1, 1):
        leads = leads.union(
            cq.Workplane('XY')
            .box(tab, FRAME_LEAD_Y, LEAD_T, centered=(False, True, False))
            .translate((sx * (BODY_X / 2 - 0.1) if sx > 0 else -OVERALL_X / 2,
                        FRAME_LEAD_CY, 0)))
    # Switch terminals: flat pads on the underside rather than gull-wings.
    for sx in (-1, 1):
        leads = leads.union(
            cq.Workplane('XY')
            .box(SWITCH_LEAD_X, SWITCH_LEAD_Y, LEAD_T, centered=(True, True, False))
            .translate((sx * SWITCH_LEAD_CX, SWITCH_LEAD_CY, 0)))

    # Locating bosses, pointing down into the board's NPTH holes. Invisible in the
    # assembled view, but they are the check that the model sits on its own holes.
    bosses = cq.Workplane('XY')
    for sx in (-1, 1):
        bosses = bosses.union(
            cq.Workplane('XY').cylinder(BOSS_LEN, BOSS_D / 2, centered=(True, True, False))
            .translate((sx * BOSS_PITCH / 2, BOSS_CY, -BOSS_LEN)))

    asm = cq.Assembly(name='SW_Push_Side_3.5x7.8x3.8_Boss')
    asm.add(body, name='body', color=IVORY)
    asm.add(plunger, name='plunger', color=BLACK)
    asm.add(leads, name='leads', color=STEEL)
    asm.add(bosses, name='bosses', color=IVORY)
    return asm


def main():
    asm = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    asm.save(str(OUT))

    shape = asm.toCompound()
    (x0, y0, z0), (x1, y1, z1) = ((shape.BoundingBox().xmin,
                                  shape.BoundingBox().ymin,
                                  shape.BoundingBox().zmin),
                                 (shape.BoundingBox().xmax,
                                  shape.BoundingBox().ymax,
                                  shape.BoundingBox().zmax))
    print(f'wrote {OUT.name}')
    print(f'  X {x0:+.3f} .. {x1:+.3f}   ({x1 - x0:.3f} wide, expect {OVERALL_X})')
    print(f'  Y {y0:+.3f} .. {y1:+.3f}   ({y1 - y0:.3f} deep, '
          f'expect {BODY_Y + PLUNGER_OUT} incl. plunger)')
    print(f'  Z {z0:+.3f} .. {z1:+.3f}   (top at {z1:.3f}, expect {TOTAL_Z}; '
          f'bosses reach {z0:+.3f})')
    print(f'  plunger tip at Y {-BODY_Y / 2 - PLUNGER_OUT:+.3f} '
          f'(footprint +{BODY_Y / 2 + PLUNGER_OUT:.3f})')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
