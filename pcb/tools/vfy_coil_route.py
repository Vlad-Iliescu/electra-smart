"""Print how the K1 coil nets are routed, to plan the v0.9 polarity bodge.

Omron's G6K-2F-Y drawing marks the coil + on pin 1 and - on pin 8; design.py
drives pin 8 from +U (COIL_HI) and pulls pin 1 to ground (COIL_LO), which is
the other way round. On the fabricated v0.9 boards that is a cut-and-jumper
fix, and where the cuts can go depends on where the copper runs, so this lists
every track, via and pad on the two coil nets with its layer and endpoints.

Usage:  "C:/Program Files/KiCad/10.0/bin/python.exe" pcb/tools/vfy_coil_route.py
"""
import pathlib

import pcbnew

BOARD = pathlib.Path(__file__).resolve().parents[1] / 'board' / 'board.kicad_pcb'
NETS = ('/COIL_LO', '/COIL_HI')


def mm(v):
    return v / 1e6


def main():
    b = pcbnew.LoadBoard(str(BOARD))
    k1 = b.FindFootprintByReference('K1')
    kb = k1.GetBoundingBox(False, False)
    print('K1 body box x %.2f..%.2f  y %.2f..%.2f'
          % (mm(kb.GetLeft()), mm(kb.GetRight()), mm(kb.GetTop()), mm(kb.GetBottom())))
    for net in NETS:
        print('\n== %s ==' % net)
        for fp in b.GetFootprints():
            for pad in fp.Pads():
                if pad.GetNetname() == net:
                    p = pad.GetPosition()
                    print('  pad  %s.%s  (%.2f, %.2f)' % (fp.GetReference(), pad.GetNumber(), mm(p.x), mm(p.y)))
        for t in b.GetTracks():
            if t.GetNetname() != net:
                continue
            if t.GetClass() == 'PCB_VIA':
                p = t.GetPosition()
                print('  via  (%.2f, %.2f)' % (mm(p.x), mm(p.y)))
            else:
                s, e = t.GetStart(), t.GetEnd()
                under = (kb.Contains(s) or kb.Contains(e))
                print('  trk  %-5s w=%.2f  (%.2f, %.2f)-(%.2f, %.2f)%s'
                      % (t.GetLayerName(), mm(t.GetWidth()), mm(s.x), mm(s.y), mm(e.x), mm(e.y),
                         '   [touches K1 body box]' if under else ''))


if __name__ == '__main__':
    main()
