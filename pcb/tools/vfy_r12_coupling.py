"""How close does CD_ASSIST run to anything noisy?

GPIO5 is high-Z whenever we are not transmitting, so the assist trace is a
floating 27 mm antenna sitting one 240 R resistor away from a bus the whole
building shares. Anything that couples onto it gets a fairly low-impedance path
to C/D. Worth knowing what its neighbours are, especially the buck's switch node.
"""

import math
import pcbnew

BRD = r"C:\dev\projects\HA\electra-smart\pcb\board\board.kicad_pcb"
NM = 1e6
TARGET = "/CD_ASSIST"


def mm(v):
    return v / NM


def seg_seg_dist(a1, a2, b1, b2):
    """Minimum distance between two 2D segments."""

    def dot(u, v):
        return u[0] * v[0] + u[1] * v[1]

    def sub(u, v):
        return (u[0] - v[0], u[1] - v[1])

    def pt_seg(p, s1, s2):
        d = sub(s2, s1)
        L = dot(d, d)
        if L == 0:
            return math.dist(p, s1)
        t = max(0.0, min(1.0, dot(sub(p, s1), d) / L))
        proj = (s1[0] + t * d[0], s1[1] + t * d[1])
        return math.dist(p, proj)

    r = sub(a2, a1)
    s = sub(b2, b1)
    denom = r[0] * s[1] - r[1] * s[0]
    if denom != 0:
        qp = sub(b1, a1)
        t = (qp[0] * s[1] - qp[1] * s[0]) / denom
        u = (qp[0] * r[1] - qp[1] * r[0]) / denom
        if 0 <= t <= 1 and 0 <= u <= 1:
            return 0.0
    return min(
        pt_seg(a1, b1, b2), pt_seg(a2, b1, b2),
        pt_seg(b1, a1, a2), pt_seg(b2, a1, a2),
    )


def main():
    b = pcbnew.LoadBoard(BRD)

    segs = {}
    for t in b.Tracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            continue
        net = t.GetNetname()
        s = t.GetStart()
        e = t.GetEnd()
        segs.setdefault(net, []).append(
            (t.GetLayer(), (mm(s.x), mm(s.y)), (mm(e.x), mm(e.y)))
        )

    if TARGET not in segs:
        print(f"{TARGET} has no tracks")
        return

    mine = segs[TARGET]
    print(f"{TARGET}: {len(mine)} segments\n")

    results = []
    for net, others in segs.items():
        if net == TARGET or not net:
            continue
        best = 1e9
        where = None
        for ly1, a1, a2 in mine:
            for ly2, b1, b2 in others:
                if ly1 != ly2:
                    continue  # different layer: plane between them, ignore
                d = seg_seg_dist(a1, a2, b1, b2)
                if d < best:
                    best = d
                    where = ((a1[0] + a2[0]) / 2, (a1[1] + a2[1]) / 2)
        if where is not None:
            results.append((best, net, where))

    results.sort()
    print("Nearest same-layer neighbours of the assist trace:")
    for d, net, where in results[:12]:
        flag = "  <-- CHECK" if d < 0.5 else ""
        print(f"  {d:6.3f} mm  {net:14} near ({where[0]:.1f}, {where[1]:.1f}){flag}")

    # The switch node is the one that matters most; name it explicitly if present.
    print("\nSwitching / high-dV-dt nets present on the board:")
    for net in sorted(segs):
        if any(k in net.upper() for k in ("SW", "BOOT", "COIL", "SPK")):
            print(f"  {net}")


main()
