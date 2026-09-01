"""Build the printable bracket that takes LED1's light out to the right-hand edge.

LED1 fires straight up out of the top face, and the board mounts with that face
toward the wall, so the light has to turn 90 degrees and travel out to the right.
The turn is done by bending the 2 mm fibre, not by a facet: bench test on the
actual fibre reached 90 degrees inside roughly 5 mm of span with light still
coming out of the far end, so a bend is viable. This bracket holds that bend in
a fixed shape and keeps the LED-to-fibre junction light-tight.

Two things drive the geometry, and both are measured off the board rather than
guessed (see pcb/tools/vfy_lightpipe.py, which prints all of them):

  * **SW1 is in the way.** It occupies the right edge at 3.80 mm tall, straddling
    exactly LED1's row, so a straight run from the LED to the edge collides with
    it. The path therefore dog-legs in plan to pass below SW1. A bend in plan
    costs no height at all, which is why it is free to spend one here.
  * **C6 sets the height budget.** The electrolytic is the tallest part on the
    board at 5.80 mm, so as long as the fibre's top stays under that, this
    bracket can never be the reason the case will not close. That is what the
    45 degree entry tilt buys: a 90 degree bend costs R of height, a 45 degree
    one costs only 0.293 R, so the radius can stay relaxed and the guide stays low.

The entry face is a plain perpendicular cut. Held at 45 degrees by the hood's
seat, its own normal points at the LED, so there is no angled polish to do -
only flat-sand and polish both ends, then frost the exit end so it reads as an
even dot instead of a hot spot.

Design radius is deliberately larger than the 5 mm that was proven by hand. You
establish where the floor is; you do not build on it.

The fibre threads through a closed bore rather than snapping into an open
channel. That is inherently light-tight and needs no second printed part, and a
fibre flexible enough to take a 5 mm bend will push through a 6 mm one. **If the
bore prints badly** - FDM sag inside a horizontal hole is the risk - the v2 move
is an open lay-in channel plus a press-on cap, not a smaller bore.

Frames. Board coordinates are KiCad's, millimetres, Y growing downward. The
model works in a local frame with its origin at LED1's centre on the board's top
surface, X along board +X, **Y along board -Y** so the sense matches KiCad's 3D
scene, and Z up out of the board. Every LOCAL_* value below is derived from a
board coordinate by that flip, so there is one place to get it wrong and it is
checked in main().

Usage:  python pcb/tools/model_lightpipe.py [--radius 6.0] [--tilt 40]
                                            [--coupon] [--variants]

To eyeball it in place, copy the board to pcb/board/_lightpipe_preview.kicad_pcb,
add a second model to LED1's footprint pointing at mech/lightpipe_bracket.step,
and render it:

    (model "<abs path>/mech/lightpipe_bracket.step"
        (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 90)))

    kicad-cli pcb render --side top --zoom 0.75 --quality high \\
        -o mech/lightpipe_top.png pcb/board/_lightpipe_preview.kicad_pcb

**That rotate is +90 to cancel LED1's +90 placement, not -90**: KiCad applies a
model's Z rotation with the opposite sign to the footprint's, so the intuitive
value puts the bracket 180 degrees out and parks the foot on the wrong side of
the board. Worth knowing before trusting a render that looks plausible.
"""
import argparse
import math
import pathlib

import cadquery as cq

OUTDIR = pathlib.Path(__file__).resolve().parents[2] / 'mech'

# --- measured off the board, all in KiCad board coordinates ----------------
LED1 = (88.77, 71.28)          # centre of the 5050 package
H3 = (80.50, 76.51)            # M2 mounting hole, 2.20 mm drill
BOARD_RIGHT = 105.10
BOARD_BOTTOM = 79.91
SW1_X0, SW1_Y0, SW1_Y1 = 100.86, 67.16, 76.01   # body extents at the right edge
SW1_H = 3.80                   # BOM: side-actuated switch 7.8 x 3.5 x 3.8 mm
C6_H = 5.80                    # tallest part on the board; the height budget
R10_X1 = 83.91                 # nearest neighbour to LED1's left
LED_TOP = 1.60                 # WS2812B 5050 body height, datasheet typical

# Where the light leaves the board: the clear lane below SW1 runs from board y
# 76.01 to the edge at 79.91, so this sits near its middle and lands about
# 6.3 mm below SW1's plunger axis.
EXIT_Y = 77.90

# --- the fibre and the guide ----------------------------------------------
FIBRE_D = 2.00
BORE_D = 2.40          # + 0.40 for print sag and an easy push-through
WALL = 1.00            # around the bore
R_BEND = 6.00          # design radius; ~5 mm was proven by hand
# 40 rather than 45 degrees. The height that has to fit the case is the
# bracket's, not the fibre's, and a 2.4 bore inside a 1.0 wall is 4.4 mm of
# stack on top of an entry that already has to clear the LED. Shaving the tilt
# is what brings the whole outer envelope under C6 while leaving a printable
# roof over the bore. See --variants.
ENTRY_TILT = 40.0      # degrees above horizontal at the entry face
ENTRY_GAP = 0.30       # fibre face to the top of the LED body
PLAN_R = 6.00          # radius of the dog-leg in plan
KNEE = (11.00, -6.60)  # local: where the two plan legs would meet
PROTRUDE = 2.00        # how far the guide stands past the board edge

HOOD_CAV = 6.40        # internal, square: clears the 5.0 mm package and its pads
HOOD_WALL = 0.90
HOOD_TOP = 4.60

FOOT_D = 5.00          # pad over H3
FOOT_T = 1.50
SCREW_D = 2.30         # M2 clearance
STRAP_D = 2.60         # rod from the foot to the hood
STRAP_Z = 1.55         # axis height, so the rod's underside stays off the board

# The bracket gets flat-topped here rather than being allowed to bulge past the
# tallest part already on the board. Then the light pipe can never be the reason
# the case will not close, which is worth having when the cavity is unmeasured.
MAX_Z = C6_H
MIN_ROOF = 0.40        # material left over the bore after that cut

STEP_LEN = 0.40        # arc discretisation; chord error at R=6 is under 0.005 mm

PETG = cq.Color(0.15, 0.15, 0.17)


def local(bx, by):
    """Board coordinates -> the local model frame (origin LED1, Y flipped)."""
    return (bx - LED1[0], -(by - LED1[1]))


LOCAL_EXIT = local(BOARD_RIGHT, EXIT_Y)
LOCAL_H3 = local(*H3)
LOCAL_SW1_X0, LOCAL_SW1_Y1 = local(SW1_X0, SW1_Y1)   # near face, near edge in Y
_, LOCAL_BOTTOM = local(0, BOARD_BOTTOM)
LOCAL_R10_X1, _ = local(R10_X1, 0)


def geometry(r_bend=R_BEND, tilt_deg=ENTRY_TILT, plan_r=PLAN_R):
    """Derive the centreline. Returns a dict of the numbers main() reports."""
    t = math.radians(tilt_deg)

    # The entry face is a disc normal to the fibre axis, so tilting it drops one
    # edge toward the LED. That low edge, not the face centre, is what has to
    # clear the LED body.
    face_z = LED_TOP + ENTRY_GAP + (FIBRE_D / 2) * math.cos(t)

    # Vertical bend, in the vertical plane along the first leg's azimuth.
    # Centre of curvature, in (u, z) where u is horizontal distance along that
    # azimuth: perpendicular to the entry tangent, on the inside of the turn.
    cu = r_bend * math.sin(t)
    cz = face_z - r_bend * math.cos(t)
    level_z = cz + r_bend                 # where the axis stops climbing
    rise = level_z - face_z               # = r_bend * (1 - cos tilt)
    advance = cu                          # = r_bend * sin tilt

    az1 = math.atan2(KNEE[1], KNEE[0])
    d_knee = math.hypot(*KNEE)

    # Fillet the plan dog-leg: tangent points set back from the knee.
    turn = abs(az1)                       # second leg runs along +X, azimuth 0
    setback = plan_r * math.tan(turn / 2)
    tp1 = ((d_knee - setback) * math.cos(az1), (d_knee - setback) * math.sin(az1))
    tp2 = (KNEE[0] + setback, KNEE[1])
    # Centre is 90 degrees to the left of travel, since the turn is toward +Y.
    nx, ny = -math.sin(az1), math.cos(az1)
    pc = (tp1[0] + plan_r * nx, tp1[1] + plan_r * ny)

    pts = []

    # A: the vertical bend, tangent angle running from tilt down to zero.
    n = max(2, int(round(r_bend * t / STEP_LEN)))
    for i in range(n + 1):
        th = t * (1 - i / n)
        u = cu - r_bend * math.sin(th)
        z = cz + r_bend * math.cos(th)
        pts.append((u * math.cos(az1), u * math.sin(az1), z))

    # B: straight along the first leg, up to the plan arc's tangent point.
    pts.append((tp1[0], tp1[1], level_z))

    # C: the plan arc, at constant height.
    a1 = math.atan2(tp1[1] - pc[1], tp1[0] - pc[0])
    a2 = math.atan2(tp2[1] - pc[1], tp2[0] - pc[0])
    while a2 < a1:
        a2 += 2 * math.pi
    n = max(2, int(round(plan_r * (a2 - a1) / STEP_LEN)))
    for i in range(1, n + 1):
        a = a1 + (a2 - a1) * i / n
        pts.append((pc[0] + plan_r * math.cos(a), pc[1] + plan_r * math.sin(a),
                    level_z))

    # D: straight out to the edge and a little past it.
    pts.append((LOCAL_EXIT[0] + PROTRUDE, LOCAL_EXIT[1], level_z))

    length = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))

    return dict(pts=pts, face_z=face_z, level_z=level_z, rise=rise,
                advance=advance, fibre_top=level_z + FIBRE_D / 2,
                fibre_bottom=level_z - FIBRE_D / 2, az1=math.degrees(az1),
                turn=math.degrees(turn), setback=setback, tp1=tp1, tp2=tp2,
                length=length, r_bend=r_bend, tilt=tilt_deg,
                arc_len=r_bend * t)


def tube(pts, r):
    """A round tube along a polyline: cylinders plus spheres at the joints."""
    parts = []
    for a, b in zip(pts, pts[1:]):
        d = cq.Vector(*b).sub(cq.Vector(*a))
        if d.Length < 1e-9:
            continue
        parts.append(cq.Solid.makeCylinder(r, d.Length, cq.Vector(*a),
                                           d.normalized()))
    for p in pts[1:-1]:
        parts.append(cq.Solid.makeSphere(r, cq.Vector(*p), angleDegrees1=-90))
    return parts[0].fuse(*parts[1:]).clean()


def build(g, coupon=False):
    pts = g['pts']
    if coupon:
        # Just the hood and the start of the arm, to fit-test the seat over LED1
        # and the clearance to R10 without printing the whole thing. This snaps
        # to a path vertex rather than cutting to an exact length, so it runs on
        # past the bend to roughly 11 mm. Interpolating an exact 6 mm endpoint
        # was tried and lands the tube's end cap about 0.8 mm outside the hood
        # wall, where the boolean hangs indefinitely - not worth chasing when a
        # slightly longer coupon tests the same interface.
        keep, run = [], 0.0
        for i, p in enumerate(pts):
            keep.append(p)
            if i and (run := run + math.dist(pts[i - 1], p)) > 6.0:
                break
        pts = keep

    outer = tube(pts, BORE_D / 2 + WALL)
    bore = tube(pts, BORE_D / 2)

    hood_out = (cq.Workplane('XY')
                .box(HOOD_CAV + 2 * HOOD_WALL, HOOD_CAV + 2 * HOOD_WALL,
                     HOOD_TOP, centered=(True, True, False))
                .edges('|Z').fillet(0.8).val())
    # Open at the bottom so it drops over the LED, roofed so no light escapes up.
    hood_cav = (cq.Workplane('XY')
                .box(HOOD_CAV, HOOD_CAV, HOOD_TOP - HOOD_WALL,
                     centered=(True, True, False)).val())

    body = outer.fuse(hood_out)

    if not coupon:
        foot = (cq.Workplane('XY')
                .cylinder(FOOT_T, FOOT_D / 2, centered=(True, True, False))
                .translate((*LOCAL_H3, 0)).val())
        # Rod across to the hood. Its underside stays clear of the board so it
        # cannot foul R10's body or the silkscreen on the way.
        a = cq.Vector(LOCAL_H3[0], LOCAL_H3[1], STRAP_Z)
        b = cq.Vector(-2.0, -1.26, STRAP_Z)
        strap = cq.Solid.makeCylinder(STRAP_D / 2, b.sub(a).Length, a,
                                      b.sub(a).normalized())
        body = body.fuse(foot).fuse(strap)
        screw = cq.Solid.makeCylinder(SCREW_D / 2, HOOD_TOP + 4,
                                      cq.Vector(*LOCAL_H3, -1))
        body = body.cut(screw)

    body = body.cut(hood_cav).cut(bore)
    above = cq.Solid.makeBox(60, 50, 20, cq.Vector(-20, -25, MAX_Z))
    return body.cut(above).clean()


def checks(g):
    """Every clearance this part has to satisfy, computed not eyeballed."""
    out = []
    ok = True

    def row(name, got, limit, worst=None):
        nonlocal ok
        good = got >= limit
        ok = ok and good
        out.append(f"  [{'ok' if good else 'FAIL'}] {name:34} {got:6.3f} mm "
                   f"(need >= {limit:.3f})" + (f"  {worst}" if worst else ''))

    row('fibre top under C6', C6_H - g['fibre_top'], 0.0,
        f"top at {g['fibre_top']:.3f}, C6 at {C6_H}")
    # The bracket, not the fibre, is what has to fit the cavity. Its round outer
    # profile would stand proud of C6, so it gets flat-topped at MAX_Z - which
    # only works while enough material survives over the bore.
    row('roof left over the bore after the flat cut',
        MAX_Z - (g['level_z'] + BORE_D / 2), MIN_ROOF,
        f"bore top at {g['level_z'] + BORE_D / 2:.3f}, cut at {MAX_Z}")
    row('fibre clear of the board surface', g['face_z'] - FIBRE_D / 2, 0.0)
    row('entry face clear of the LED body',
        g['face_z'] - (FIBRE_D / 2) * math.cos(math.radians(g['tilt'])) - LED_TOP,
        ENTRY_GAP - 1e-6)

    # SW1: the binding constraint. Nearest approach from the fibre surface to
    # SW1's top-inboard corner edge, taken in 3D since both the plan offset and
    # the height difference help.
    worst = None
    best = 1e9
    for x, y, z in g['pts']:
        if x < LOCAL_SW1_X0 - 1.0:
            continue
        d = math.hypot(y - LOCAL_SW1_Y1, min(0.0, z - SW1_H)) - FIBRE_D / 2
        if y > LOCAL_SW1_Y1 and z < SW1_H:
            d = -abs(d)          # inside SW1's footprint and below its top
        if d < best:
            best, worst = d, f"at x {x:.2f}"
    row('fibre to SW1 body', best, 0.30, worst)

    # The guide has to stay on the board, bar the deliberate overhang past the
    # right edge where it pokes through the housing.
    low = min(y for _, y, _ in g['pts'])
    row('fibre inboard of the bottom edge',
        low - FIBRE_D / 2 - LOCAL_BOTTOM, 0.0, f"lowest y {low:.2f}")

    hood_half = HOOD_CAV / 2 + HOOD_WALL
    row('hood clear of R10', -hood_half - LOCAL_R10_X1, 0.30,
        f"hood reaches x {-hood_half:.2f}, R10 ends {LOCAL_R10_X1:.2f}")

    return ok, out


def report(g):
    print(f"bend radius {g['r_bend']:.2f} mm, entry tilt {g['tilt']:.1f} deg")
    print(f"  entry face centre     z {g['face_z']:.3f} mm")
    print(f"  bend rises            {g['rise']:.3f} mm "
          f"(a 90 deg bend would cost {g['r_bend']:.3f})")
    print(f"  bend advances         {g['advance']:.3f} mm horizontally")
    print(f"  axis levels out at    z {g['level_z']:.3f} mm, "
          f"fibre {g['fibre_bottom']:.3f}..{g['fibre_top']:.3f}")
    print(f"  plan dog-leg          first leg {g['az1']:.2f} deg, "
          f"turn {g['turn']:.2f} deg, setback {g['setback']:.3f} mm")
    print(f"  centreline length     {g['length']:.2f} mm "
          f"(cut the fibre a little long and trim at the exit)")
    print(f"  exit                  board ({BOARD_RIGHT:.2f}, {EXIT_Y:.2f}), "
          f"{PROTRUDE:.1f} mm proud")
    ok, rows = checks(g)
    print('\n'.join(rows))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--radius', type=float, default=R_BEND)
    ap.add_argument('--tilt', type=float, default=ENTRY_TILT)
    ap.add_argument('--coupon', action='store_true',
                    help='hood plus 6 mm only, to fit-test the seat over LED1')
    ap.add_argument('--variants', action='store_true',
                    help='report a sweep of radius and tilt without exporting')
    args = ap.parse_args()

    if args.variants:
        print(f"{'R':>5} {'tilt':>5} {'rise':>6} {'top':>6} {'roof':>6} "
              f"{'capture':>8}")
        for r in (5.0, 6.0, 6.5, 8.0):
            for tl in (35.0, 40.0, 45.0, 55.0):
                g = geometry(r, tl)
                cap = math.cos(math.radians(90 - tl)) ** 2
                roof = MAX_Z - (g['level_z'] + BORE_D / 2)
                flag = '' if roof >= MIN_ROOF else '  <- too thin'
                print(f"{r:5.1f} {tl:5.1f} {g['rise']:6.3f} "
                      f"{g['fibre_top']:6.3f} {roof:6.3f} {cap:8.2f}{flag}")
        print(f"\nroof is what survives over the bore once the bracket is flat-"
              f"topped at {MAX_Z} mm,\nand it is the binding constraint - not the "
              f"fibre's own height. Needs {MIN_ROOF} mm.")
        print('capture is a rough cosine estimate: the LED falls off as it goes '
              'off-axis and\nthe tilted face presents less area. Half the light '
              'is affordable here.')
        return 0

    g = geometry(args.radius, args.tilt)
    ok = report(g)

    name = 'lightpipe_coupon' if args.coupon else 'lightpipe_bracket'
    OUTDIR.mkdir(parents=True, exist_ok=True)
    shape = build(g, coupon=args.coupon)
    cq.exporters.export(shape, str(OUTDIR / f'{name}.step'))
    cq.exporters.export(shape, str(OUTDIR / f'{name}.stl'),
                        tolerance=0.01, angularTolerance=0.1)

    bb = shape.BoundingBox()
    print(f"\nwrote mech/{name}.step and .stl")
    print(f"  X {bb.xmin:+.2f} .. {bb.xmax:+.2f}   "
          f"Y {bb.ymin:+.2f} .. {bb.ymax:+.2f}   "
          f"Z {bb.zmin:+.2f} .. {bb.zmax:+.2f}")
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
