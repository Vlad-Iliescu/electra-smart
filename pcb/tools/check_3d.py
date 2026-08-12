"""Render the project-local footprints on a scratch board so their 3D models can
be eyeballed for seating and orientation.

Vendor STEP models are frequently exported Y-up, which KiCad interprets as Z-up:
the body then sits half-buried in the board and offset sideways instead of
standing on its pads. That is invisible in the schematic and in DRC, and only
shows up here or in the 3D viewer, so it is worth a look whenever a footprint
gains a model.

Must run under KiCad's own Python, which is the only one with `pcbnew`:

    & "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" pcb\\tools\\check_3d.py

then render the board it writes:

    kicad-cli pcb render --side front --zoom 0.8 -o front.png pcb/board/_3dtest.kicad_pcb
    kicad-cli pcb render --side top   --zoom 0.8 -o top.png   pcb/board/_3dtest.kicad_pcb

A correct model sits *on* the board in the side view and is *centred* on its pads
in the top view.
"""
import pathlib

import pcbnew

ROOT = pathlib.Path(__file__).resolve().parents[1]
LIB = ROOT / 'libs' / 'electra.pretty'
# Lives in pcb/board/ so the models' ${KIPRJMOD} resolves the same way it will
# on the real board.
OUT = ROOT / 'board' / '_3dtest.kicad_pcb'

board = pcbnew.CreateEmptyBoard()
for i, path in enumerate(sorted(LIB.glob('*.kicad_mod'))):
    fp = pcbnew.FootprintLoad(str(LIB), path.stem)
    assert fp is not None, path.stem
    fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(20 + i * 15), pcbnew.FromMM(20)))
    fp.SetReference('X%d' % (i + 1))
    board.Add(fp)
    models = [(m.m_Filename, tuple(m.m_Rotation)) for m in fp.Models()]
    print('X%d  %-45s %s' % (i + 1, path.stem, models or 'NO 3D MODEL'))

pcbnew.SaveBoard(str(OUT), board)
print('wrote', OUT)
