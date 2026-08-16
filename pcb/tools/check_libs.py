"""Assert that every symbol and footprint the board uses resolves from either
this repository or a stock KiCad install.

The point is portability. Parts that resolve through a machine-local library
work perfectly on the machine that has it and fail silently everywhere else,
and nothing else in the toolchain notices: gen_sch.py reuses definitions already
embedded in the schematic, and ERC only ever looks at those embedded copies. So
a broken library reference survives a completely clean ERC run and only surfaces
when someone else opens the board.

Usage:  python pcb/tools/check_libs.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import design  # noqa: E402

KICAD = pathlib.Path(r'C:\Program Files\KiCad\10.0\share\kicad')
ROOT = pathlib.Path(__file__).resolve().parents[2]
PROJ = ROOT / 'pcb' / 'libs'

# Footprints deliberately left empty until a real-world measurement is taken.
# gen_sch.py emits them blank on purpose, so they are not failures here.
PENDING = set()


def resolve_fp(fp):
    lib, name = fp.split(':', 1)
    if (PROJ / f'{lib}.pretty' / f'{name}.kicad_mod').exists():
        return 'repo'
    if (KICAD / 'footprints' / f'{lib}.pretty' / f'{name}.kicad_mod').exists():
        return 'kicad'
    return None


def resolve_sym(lib_id):
    lib = lib_id.split(':', 1)[0]
    if (PROJ / f'{lib}.kicad_sym').exists():
        return 'repo'
    if (KICAD / 'symbols' / f'{lib}.kicad_sym').exists():
        return 'kicad'
    return None


def main():
    bad, pending, counts = [], [], {'repo': 0, 'kicad': 0}

    for ref, (lib_id, _value, fp, *_rest) in sorted(design.PARTS.items()):
        if ref.startswith('#'):
            continue
        if not fp:
            (pending if ref in PENDING else bad).append(
                f'{ref}: footprint is empty')
            continue
        where = resolve_fp(fp)
        if where is None:
            bad.append(f'{ref}: footprint {fp} not found')
        else:
            counts[where] += 1

    for lib_id in sorted({p[0] for p in design.PARTS.values()}):
        where = resolve_sym(lib_id)
        if where is None:
            bad.append(f'symbol {lib_id} not found')
        else:
            counts[where] += 1

    for note in pending:
        print(f'PENDING  {note}')
    for note in bad:
        print(f'FAIL     {note}')

    print(f'\n{counts["repo"]} from the repository, '
          f'{counts["kicad"]} from the KiCad install, '
          f'{len(pending)} pending a measurement.')
    if bad:
        print('RESULT: unresolved references above')
        return 1
    print('RESULT: every reference resolves; no machine-local libraries')
    return 0


if __name__ == '__main__':
    sys.exit(main())
