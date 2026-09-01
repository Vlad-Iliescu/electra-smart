"""Check the board against the stencil order options.

Two things decide those options: whether any component sits on the back (which
would need a second stencil), and the smallest paste aperture's area ratio, which
decides thickness and whether nano-coating buys anything.

Area ratio = aperture opening area / aperture wall area. Below about 0.66 paste
starts sticking in the aperture instead of releasing onto the pad.
"""

import pcbnew

BRD = r"C:\dev\projects\HA\electra-smart\pcb\board\board.kicad_pcb"
NM = 1e6
THICKNESSES = (0.08, 0.10, 0.12, 0.15)


def mm(v):
    return v / NM


def main():
    b = pcbnew.LoadBoard(BRD)

    front, back = [], []
    for fp in b.Footprints():
        (back if fp.IsFlipped() else front).append(fp.GetReference())
    print(f"footprints on FRONT ({len(front)}): {' '.join(sorted(front))}")
    print(f"footprints on BACK  ({len(back)}): {' '.join(sorted(back)) or 'none'}")
    print(f"  -> stencil side needed: {'TOP + BOTTOM' if back else 'TOP ONLY'}\n")

    # Every pad that will get a stencil aperture.
    apertures = []
    pth_with_paste = []
    for fp in b.Footprints():
        for p in fp.Pads():
            lset = p.GetLayerSet()
            on_fpaste = lset.Contains(pcbnew.F_Paste)
            on_bpaste = lset.Contains(pcbnew.B_Paste)
            if not (on_fpaste or on_bpaste):
                continue
            sz = p.GetSize()
            w, h = sorted((mm(sz.x), mm(sz.y)))
            apertures.append((w, h, f"{fp.GetReference()}.{p.GetNumber()}",
                              p.GetShape()))
            d = p.GetDrillSize()
            if d.x > 0:
                pth_with_paste.append(f"{fp.GetReference()}.{p.GetNumber()}")

    print(f"paste apertures: {len(apertures)}")
    if pth_with_paste:
        print(f"  WARNING: drilled pads carrying paste: {' '.join(pth_with_paste)}")
        print("  paste on a hole just falls through - check these are meant to be there")
    else:
        print("  no drilled pad carries paste, which is correct")

    apertures.sort(key=lambda a: a[0] * a[1])
    print("\nsmallest apertures by area:")
    for w, h, ref, shape in apertures[:6]:
        print(f"  {ref:10} {w:.3f} x {h:.3f} mm")

    print("\narea ratio of the smallest aperture at each stencil thickness:")
    w, h, ref, _ = apertures[0]
    for t in THICKNESSES:
        ar = (w * h) / (2.0 * (w + h) * t)
        verdict = "good" if ar >= 0.66 else "TOO LOW - paste will stick"
        print(f"  {t:.2f} mm : AR {ar:.2f}  {verdict}   ({ref})")

    # Narrowest single dimension matters for bridging, separately from area.
    print("\nnarrowest aperture dimension and tightest pad gap:")
    print(f"  narrowest aperture side : {apertures[0][0]:.3f} mm")

    best = (1e9, None)
    for fp in b.Footprints():
        pads = [p for p in fp.Pads() if p.GetLayerSet().Contains(pcbnew.F_Paste)]
        for i in range(len(pads)):
            for j in range(i + 1, len(pads)):
                if pads[i].GetNetname() == pads[j].GetNetname():
                    continue
                a = pads[i].GetBoundingBox()
                c = pads[j].GetBoundingBox()
                dx = max(mm(c.GetLeft()) - mm(a.GetRight()),
                         mm(a.GetLeft()) - mm(c.GetRight()), 0.0)
                dy = max(mm(c.GetTop()) - mm(a.GetBottom()),
                         mm(a.GetTop()) - mm(c.GetBottom()), 0.0)
                gap = (dx * dx + dy * dy) ** 0.5
                if gap < best[0]:
                    best = (gap, f"{fp.GetReference()} pads "
                                 f"{pads[i].GetNumber()}-{pads[j].GetNumber()}")
    print(f"  tightest gap between pads of different nets : {best[0]:.3f} mm  ({best[1]})")


main()
