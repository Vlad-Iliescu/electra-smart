"""Report which parts on the board have no 3D model behind them.

A missing model is not an electrical fault, so nothing else in the toolchain
complains: ERC, the netlist check and check_libs all pass with an empty 3D view.
It matters at layout time instead, because the 3D view is the cheapest way to
catch a part fouling the enclosure, an electrolytic taller than the lid clears,
or a connector whose plug needs room to be inserted.

Two failure modes are worth separating. A footprint can carry no (model ...)
line at all, which is ours to fix; or it can reference a file that is not on
disk, which usually means a stock footprint pointing at a model package that was
not installed. The second kind renders as an empty space and is easy to mistake
for the first.

Usage:  python pcb/tools/check_models.py
"""
import collections
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import design  # noqa: E402

KICAD = pathlib.Path(r'C:\Program Files\KiCad\10.0\share\kicad')
ROOT = pathlib.Path(__file__).resolve().parents[2]
PROJ = ROOT / 'pcb' / 'libs'
# KIPRJMOD is the directory holding the .kicad_pro, which is where the relative
# ../libs/electra.3dshapes paths in our own footprints are anchored.
PRJMOD = ROOT / 'pcb' / 'board'

# Parts that will never have a 3D model, and why. These are not gaps waiting to be
# filled, so they are reported apart from the real ones and do not count against
# the total. Keep the reason with the entry: a bare exclusion list rots into
# something nobody dares delete.
WAIVED = {
    'J2': 'bare wire soldered through a hole - there is no body to draw, so empty '
          'space is the honest representation and there is nothing to collide with. '
          'The stock footprint does name a model, but KiCad ships no Connector_Wire '
          'models at all, so this would stay empty even if we wanted it.',
}

MODEL_RE = re.compile(r'\(model\s+"([^"]+)"')
VAR_RE = re.compile(r'\$\{([^}]+)\}')
# KiCad ships .wrl for rendering and .step for MCAD export; a footprint names one
# and the other usually sits beside it. Either proves a model exists.
ALT_SUFFIXES = ('.wrl', '.step', '.stp', '.STEP')


def fp_path(fp):
    """Locate a footprint file and say which library it came from."""
    lib, name = fp.split(':', 1)
    for where, base in (('repo', PROJ), ('kicad', KICAD / 'footprints')):
        p = base / f'{lib}.pretty' / f'{name}.kicad_mod'
        if p.exists():
            return where, p
    return None, None


def expand(raw):
    """Resolve KiCad path variables. Returns None if a variable is unknown."""
    unknown = []

    def sub(m):
        var = m.group(1)
        if var == 'KIPRJMOD':
            return PRJMOD.as_posix()
        if '3DMODEL' in var.upper():
            return (KICAD / '3dmodels').as_posix()
        unknown.append(var)
        return ''

    out = VAR_RE.sub(sub, raw.replace('\\', '/'))
    return None if unknown else pathlib.Path(out)


def model_state(fp):
    """-> (state, detail) where state is 'ok', 'missing_file' or 'no_model'."""
    where, path = fp_path(fp)
    if path is None:
        return 'no_footprint', fp
    refs = MODEL_RE.findall(path.read_text(encoding='utf-8', errors='replace'))
    if not refs:
        return 'no_model', where
    for raw in refs:
        p = expand(raw)
        if p is None:
            continue
        if p.exists() or any(p.with_suffix(s).exists() for s in ALT_SUFFIXES):
            return 'ok', where
    return 'missing_file', refs[0]


def main():
    buckets = collections.defaultdict(list)
    by_fp = {}

    for ref, (_lib_id, value, fp, *_rest) in design.PARTS.items():
        if ref.startswith('#') or not fp:
            continue
        if fp not in by_fp:
            by_fp[fp] = model_state(fp)
        state, detail = by_fp[fp]
        if ref in WAIVED and state != 'ok':
            state, detail = 'waived', WAIVED[ref]
        buckets[state].append((ref, value, fp, detail))

    def show(state, title):
        rows = sorted(buckets[state], key=lambda r: (r[2], r[0]))
        if not rows:
            return
        print(f'\n{title} ({len(rows)} part(s), '
              f'{len({r[2] for r in rows})} distinct footprint(s))')
        for ref, value, fp, detail in rows:
            note = f'   [{detail}]' if state == 'missing_file' else ''
            print(f'  {ref:<5} {value:<34} {fp}{note}')

    show('no_model', 'NO 3D MODEL AT ALL')
    show('missing_file', 'MODEL REFERENCED BUT FILE NOT ON DISK')
    show('no_footprint', 'FOOTPRINT NOT FOUND')

    for ref, _value, _fp, reason in sorted(buckets['waived']):
        print(f'\nNO MODEL NEEDED\n  {ref}: {reason}')

    total = sum(len(v) for v in buckets.values())
    ok, waived = len(buckets['ok']), len(buckets['waived'])
    gaps = total - ok - waived
    print(f'\n{ok}/{total} parts have a 3D model, {waived} need none, '
          f'{gaps} still to draw.')
    print('RESULT: nothing left to draw' if not gaps
          else f'RESULT: {gaps} part(s) would render as empty space')
    return 0


if __name__ == '__main__':
    sys.exit(main())
