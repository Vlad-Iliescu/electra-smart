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

Pass a substring to place only the footprints whose name matches, which is what you
want when checking one new model - the whole library rendered in a row leaves each
part too small to judge:

    & "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" pcb\\tools\\check_3d.py SW_Push
"""
import pathlib
import sys

import pcbnew

ROOT = pathlib.Path(__file__).resolve().parents[1]
LIB = ROOT / 'libs' / 'electra.pretty'
# Lives in pcb/board/ so the models' ${KIPRJMOD} resolves the same way it will
# on the real board.
OUT = ROOT / 'board' / '_3dtest.kicad_pcb'

match = sys.argv[1] if len(sys.argv) > 1 else ''
paths = [p for p in sorted(LIB.glob('*.kicad_mod')) if match.lower() in p.stem.lower()]
assert paths, 'nothing matches %r' % match

board = pcbnew.CreateEmptyBoard()
for i, path in enumerate(paths):
    fp = pcbnew.FootprintLoad(str(LIB), path.stem)
    assert fp is not None, path.stem
    # Spacing has to clear the largest part, which is the 18 x 22.7 mm module.
    fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(25 + i * 30), pcbnew.FromMM(25)))
    fp.SetReference('X%d' % (i + 1))
    board.Add(fp)
    models = [(m.m_Filename, tuple(m.m_Rotation)) for m in fp.Models()]
    print('X%d  %-45s %s' % (i + 1, path.stem, models or 'NO 3D MODEL'))

# Without an Edge.Cuts outline KiCad renders a board it cannot frame, and the camera
# ends up pointing at empty space rather than at the parts. Wrap whatever was placed.
box = board.GetBoardEdgesBoundingBox()
if not box.GetWidth():
    box = board.ComputeBoundingBox(False)
m = pcbnew.FromMM(5)
x0, y0 = box.GetLeft() - m, box.GetTop() - m
x1, y1 = box.GetRight() + m, box.GetBottom() + m
for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)),
             ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
    seg = pcbnew.PCB_SHAPE(board)
    seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
    seg.SetStart(pcbnew.VECTOR2I(*a))
    seg.SetEnd(pcbnew.VECTOR2I(*b))
    seg.SetLayer(pcbnew.Edge_Cuts)
    seg.SetWidth(pcbnew.FromMM(0.1))
    board.Add(seg)

pcbnew.SaveBoard(str(OUT), board)
print('wrote', OUT, '(outline %.1f x %.1f mm)'
      % (pcbnew.ToMM(x1 - x0), pcbnew.ToMM(y1 - y0)))
