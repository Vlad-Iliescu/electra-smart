"""Diff the netlist KiCad exported against the intent declared in design.py.

ERC only proves a schematic is self-consistent; this proves it matches the
design. Run after gen_sch.py + `kicad-cli sch export netlist`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import design  # noqa: E402
from sexp import loads, kids, kid, val  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
NET = ROOT / 'pcb' / 'board' / 'board.net'


def main():
    tree = loads(NET.read_text(encoding='utf-8'))
    nets_block = kid(tree, 'nets')

    actual = {}
    for net in kids(nets_block, 'net'):
        name = val(net, 'name', '')
        members = {(val(n, 'ref', ''), str(val(n, 'pin', '')))
                   for n in kids(net, 'node')}
        # KiCad prefixes auto-named nets with '/'; ours are all explicit labels.
        actual[name.lstrip('/')] = members

    # PWR_FLAGs exist only to satisfy ERC's power-driven check; KiCad omits
    # '#'-prefixed virtual symbols from the exported netlist by design.
    expected = {net: {(r, p) for r, p, _ in mem if not r.startswith('#')}
                for net, mem in design.NETS.items()}

    bad = False
    for name in sorted(expected):
        exp, act = expected[name], actual.get(name)
        if act is None:
            print(f'MISSING net {name}')
            bad = True
            continue
        if exp != act:
            bad = True
            print(f'MISMATCH {name}')
            for m in sorted(exp - act):
                print(f'    expected but absent: {m[0]}.{m[1]}')
            for m in sorted(act - exp):
                print(f'    present but unexpected: {m[0]}.{m[1]}')
        else:
            pins = ' '.join(f'{r}.{p}' for r, p in sorted(exp))
            print(f'OK  {name:<10} ({len(exp):>2}) {pins}')

    extra = set(actual) - set(expected)
    # Single-pin nets are the no-connects KiCad names automatically.
    extra = {e for e in extra if len(actual[e]) > 1}
    if extra:
        bad = True
        print('\nUNEXPECTED multi-pin nets:')
        for e in sorted(extra):
            print(f'  {e}: {sorted(actual[e])}')

    print('\nRESULT:', 'MISMATCH' if bad else 'netlist matches design.py exactly')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
