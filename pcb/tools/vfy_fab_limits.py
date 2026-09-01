"""Check the board against the cheap-tier fab limits selected at the quote page.

Everything here is a number a fab either accepts silently or raises an engineering
query about. Cheaper to find out now.
"""

import pcbnew

BRD = r"C:\dev\projects\HA\electra-smart\pcb\board\board.kicad_pcb"
NM = 1e6


def mm(v):
    return v / NM


def main():
    b = pcbnew.LoadBoard(BRD)

    bb = b.GetBoardEdgesBoundingBox()
    print(f"outline incl. edge line width : {mm(bb.GetWidth()):.2f} x {mm(bb.GetHeight()):.2f} mm")

    # Vias: drill plus finished pad, which is what the "min via hole size" tier means.
    vias = [t for t in b.Tracks() if t.Type() == pcbnew.PCB_VIA_T]
    drills = sorted({round(mm(v.GetDrill()), 3) for v in vias})
    pads = sorted({round(mm(v.GetWidth(pcbnew.F_Cu)), 3) for v in vias})
    print(f"\nvias                          : {len(vias)}")
    print(f"  drill sizes                 : {drills}")
    print(f"  pad diameters               : {pads}")
    if drills and pads:
        print(f"  annular ring                : {(min(pads) - max(drills)) / 2:.3f} mm per side")

    # Through-hole pads, plated and not. NPTH minimums differ from PTH.
    pth, npth = [], []
    for fp in b.Footprints():
        for p in fp.Pads():
            d = p.GetDrillSize()
            if d.x == 0 and d.y == 0:
                continue
            entry = (f"{fp.GetReference()}.{p.GetNumber()}", round(mm(d.x), 3), round(mm(d.y), 3))
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                npth.append(entry)
            else:
                pth.append(entry)

    print(f"\nplated holes ({len(pth)}):")
    for ref, dx, dy in sorted(pth, key=lambda e: e[1]):
        shape = "round" if abs(dx - dy) < 1e-6 else f"SLOT {dx} x {dy}"
        print(f"  {ref:10} {dx:5.2f} mm  {shape}")

    print(f"\nnon-plated holes ({len(npth)}):")
    for ref, dx, dy in sorted(npth, key=lambda e: e[1]):
        shape = "round" if abs(dx - dy) < 1e-6 else f"SLOT {dx} x {dy}"
        print(f"  {ref:10} {dx:5.2f} mm  {shape}")

    # Track width and clearance are the other two tier-defining numbers.
    ts = [t for t in b.Tracks() if t.Type() != pcbnew.PCB_VIA_T]
    print(f"\nmin track width               : {mm(min(t.GetWidth() for t in ts)):.3f} mm")

    ds = b.GetDesignSettings()
    print(f"design rule min clearance     : {mm(ds.m_MinClearance):.3f} mm")
    print(f"design rule min track         : {mm(ds.m_TrackMinWidth):.3f} mm")
    print(f"design rule min annular ring  : {mm(ds.m_ViasMinAnnularWidth):.3f} mm")
    print(f"design rule min via diameter  : {mm(ds.m_ViasMinSize):.3f} mm")


main()
