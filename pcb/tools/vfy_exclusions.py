"""Identify what the three DRC exclusions in board.kicad_pro actually are.

An exclusion marked "part design" is fine if it is inherent to a footprint the fab
will build anyway, and not fine if it is a real hole-to-copper spacing problem that
someone waved through. kicad-cli reports these as zero violations either way, so
they have to be looked at by hand.
"""

import pcbnew

BRD = r"C:\dev\projects\HA\electra-smart\pcb\board\board.kicad_pcb"
NM = 1e6

SPOTS = [
    ("hole_clearance", 102.7228, 69.9318),
    ("hole_clearance", 102.7228, 73.2318),
    ("silk_over_copper", 99.190983, 38.8425),
]
RADIUS = 3.0  # mm around the reported point


def mm(v):
    return v / NM


def main():
    b = pcbnew.LoadBoard(BRD)

    for kind, x, y in SPOTS:
        print(f"=== {kind} at ({x:.3f}, {y:.3f}) ===")
        near = []
        for fp in b.Footprints():
            fpos = fp.GetPosition()
            d = ((mm(fpos.x) - x) ** 2 + (mm(fpos.y) - y) ** 2) ** 0.5
            if d <= 8.0:
                near.append((d, fp))
        near.sort(key=lambda e: e[0])
        for d, fp in near[:3]:
            print(f"  {d:5.2f} mm to {fp.GetReference():5} {fp.GetValue():30} "
                  f"{fp.GetFPIDAsString()}")

        # Which pads and holes sit right on the reported point?
        for fp in b.Footprints():
            for p in fp.Pads():
                pp = p.GetPosition()
                d = ((mm(pp.x) - x) ** 2 + (mm(pp.y) - y) ** 2) ** 0.5
                if d > RADIUS:
                    continue
                dr = p.GetDrillSize()
                hole = "none" if (dr.x == 0 and dr.y == 0) else f"{mm(dr.x):.2f} mm"
                kindstr = {
                    pcbnew.PAD_ATTRIB_NPTH: "NPTH",
                    pcbnew.PAD_ATTRIB_PTH: "PTH",
                    pcbnew.PAD_ATTRIB_SMD: "SMD",
                    pcbnew.PAD_ATTRIB_CONN: "CONN",
                }.get(p.GetAttribute(), "?")
                print(f"    {d:5.2f} mm  {fp.GetReference()}.{p.GetNumber():4} "
                      f"{kindstr:5} hole={hole:8} net={p.GetNetname()!r}")
        print()


main()
