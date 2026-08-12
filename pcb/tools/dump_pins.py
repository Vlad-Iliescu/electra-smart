"""Dump pin tables for every lib_symbol embedded in a .kicad_sch."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sexp import loads, kids, kid, head, val  # noqa: E402


def unit_pins(sym):
    """Pins live in child (symbol "NAME_u_v") blocks; gather them all."""
    out = []
    for sub in kids(sym, 'symbol'):
        for p in kids(sub, 'pin'):
            etype = p[1] if len(p) > 1 else '?'
            at = kid(p, 'at')
            out.append({
                'num': val(p, 'number', '?'),
                'name': val(p, 'name', ''),
                'etype': etype,
                'x': float(at[1]) if at else 0.0,
                'y': float(at[2]) if at else 0.0,
                'ang': float(at[3]) if at and len(at) > 3 else 0.0,
                'unit': sub[1],
            })
    return out


def main(path, only=None):
    tree = loads(Path(path).read_text(encoding='utf-8'))
    libs = kid(tree, 'lib_symbols')
    for sym in kids(libs, 'symbol'):
        name = sym[1]
        if only and only.lower() not in name.lower():
            continue
        pins = unit_pins(sym)
        print(f'\n=== {name}  ({len(pins)} pins) ===')
        for p in sorted(pins, key=lambda d: (len(d['num']), d['num'])):
            print(f"  {p['num']:>4}  {p['name'][:24]:<24} {p['etype']:<14} "
                  f"at({p['x']:>8.2f},{p['y']:>8.2f}) rot{int(p['ang']):>4}")


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
