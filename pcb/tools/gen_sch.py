"""Generate pcb/board/board.kicad_sch from the declaration in design.py.

Symbol definitions are harvested from the existing schematic where possible, so
the emitted file reuses definitions KiCad itself wrote. Anything missing is
pulled out of the installed KiCad libraries.

Connectivity is expressed entirely with net labels on short stubs: every
connected pin gets a 5.08 mm wire and a label. That keeps the netlist provably
correct without needing to route wires between symbols, and it means all
symbols can be placed unrotated so the library->sheet coordinate transform
stays trivial.

Usage:  python pcb/tools/gen_sch.py [--check]
"""

import argparse
import re
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import design  # noqa: E402
from sexp import loads, kids, kid, val  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SCH = ROOT / 'pcb' / 'board' / 'board.kicad_sch'
KICAD_SYMS = Path(r'C:\Program Files\KiCad\10.0\share\kicad\symbols')
USER_SYMS = Path(r'C:\dev\kicad\libs')

NS = uuid.UUID('1b4e28ba-2fa1-11d2-883f-0016d3cca427')
STUB = 5.08
GRID = 1.27


def uid(*parts):
    """Deterministic UUID so regenerating the sheet does not churn git."""
    return str(uuid.uuid5(NS, '|'.join(str(p) for p in parts)))


def snap(v):
    return round(round(v / GRID) * GRID, 4)


def fmt(v):
    """KiCad writes trailing-zero-free decimals."""
    s = f'{float(v):.4f}'.rstrip('0').rstrip('.')
    return s if s not in ('', '-0') else '0'


# --------------------------------------------------------------------------
# extracting (symbol "...") blocks as raw text
# --------------------------------------------------------------------------

def find_block(text, name):
    """Return the raw text of the top-level (symbol "name" ...) block."""
    needle = f'(symbol "{name}"'
    start = text.find(needle)
    while start != -1:
        # Only accept it when the token really starts the s-expression.
        if text[start - 1] in '\t\n ' or start == 0:
            break
        start = text.find(needle, start + 1)
    if start == -1:
        return None
    depth, i, n, in_str = 0, start, len(text), False
    while i < n:
        c = text[i]
        if in_str:
            if c == '\\':
                i += 2
                continue
            if c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
        i += 1
    return None


def reindent(block, tabs):
    """Re-indent a harvested block to `tabs`, normalising whatever it had.

    find_block slices from the '(' so the first line carries no indentation
    while continuation lines keep the source's absolute indent. Dedenting by the
    closing paren's indent (always equal to the opening line's) before adding the
    target makes this idempotent - otherwise re-harvesting a generated file adds
    another level every run and the sheet grows without bound.
    """
    lines = block.split('\n')
    base = len(lines[-1]) - len(lines[-1].lstrip('\t'))
    pad = '\t' * tabs
    out = [pad + lines[0]]
    for ln in lines[1:]:
        if not ln.strip():
            out.append(ln)
            continue
        depth = len(ln) - len(ln.lstrip('\t'))
        out.append(pad + '\t' * max(0, depth - base) + ln.lstrip('\t'))
    return '\n'.join(out)


def load_lib_symbol(lib_id):
    """Fetch a lib_symbol block from the installed or user symbol libraries."""
    libname, symname = lib_id.split(':', 1)
    for base in (KICAD_SYMS, USER_SYMS):
        p = base / f'{libname}.kicad_sym'
        if p.exists():
            blk = find_block(p.read_text(encoding='utf-8'), symname)
            if blk:
                if '(extends' in blk:
                    raise SystemExit(f'{lib_id} uses (extends ...); not supported')
                # Rename to the fully qualified id used inside a schematic.
                return blk.replace(f'(symbol "{symname}"',
                                   f'(symbol "{lib_id}"', 1)
    return None


# --------------------------------------------------------------------------
# pin geometry
# --------------------------------------------------------------------------

def symbol_pins(block):
    """{pin_number: dict(name, etype, x, y, ang)} for one lib_symbol block."""
    tree = loads(block)
    pins, units = {}, set()
    for sub in kids(tree, 'symbol'):
        m = re.search(r'_(\d+)_(\d+)$', sub[1])
        if m:
            units.add(int(m.group(1)))
        for p in kids(sub, 'pin'):
            at = kid(p, 'at')
            num = val(p, 'number', '?')
            pins[num] = {
                'name': val(p, 'name', ''),
                'etype': p[1] if len(p) > 1 else '?',
                'x': float(at[1]), 'y': float(at[2]),
                'ang': int(float(at[3])) if len(at) > 3 else 0,
            }
    if len(units - {0}) > 1:
        raise SystemExit(f'multi-unit symbol not supported: {block[:60]}')
    return pins


# Outward direction in *schematic* coordinates for a pin drawn at each angle.
# A library pin's (x, y) is its electrical endpoint and the body extends along
# `ang`, so outward is the opposite. Library +y is schematic -y.
OUTWARD = {0: (-1.0, 0.0), 90: (0.0, 1.0), 180: (1.0, 0.0), 270: (0.0, -1.0)}
LABEL_ANGLE = {(-1.0, 0.0): 180, (1.0, 0.0): 0, (0.0, -1.0): 90, (0.0, 1.0): 270}


def pin_at(px, py, sx, sy):
    """Library pin coords -> schematic coords for an unrotated, unmirrored symbol."""
    return snap(sx + px), snap(sy - py)


# --------------------------------------------------------------------------
# emitters
# --------------------------------------------------------------------------

def emit_wire(x1, y1, x2, y2, key):
    return (f'\t(wire\n\t\t(pts\n\t\t\t(xy {fmt(x1)} {fmt(y1)}) (xy {fmt(x2)} {fmt(y2)})\n\t\t)\n'
            f'\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n'
            f'\t\t(uuid "{uid("wire", key)}")\n\t)')


def emit_label(name, x, y, ang, key):
    just = 'left bottom' if ang in (0, 90) else 'right bottom'
    return (f'\t(label "{name}"\n\t\t(at {fmt(x)} {fmt(y)} {ang})\n'
            f'\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n'
            f'\t\t\t(justify {just})\n\t\t)\n'
            f'\t\t(uuid "{uid("label", key)}")\n\t)')


def emit_no_connect(x, y, key):
    return (f'\t(no_connect\n\t\t(at {fmt(x)} {fmt(y)})\n'
            f'\t\t(uuid "{uid("nc", key)}")\n\t)')


def emit_property(name, value, x, y, ang, hide, justify=None):
    out = [f'\t\t(property "{name}" "{value}"',
           f'\t\t\t(at {fmt(x)} {fmt(y)} {ang})']
    if hide:
        out.append('\t\t\t(hide yes)')
    out += ['\t\t\t(show_name no)', '\t\t\t(do_not_autoplace no)',
            '\t\t\t(effects', '\t\t\t\t(font', '\t\t\t\t\t(size 1.27 1.27)',
            '\t\t\t\t)']
    if justify:
        out.append(f'\t\t\t\t(justify {justify})')
    out += ['\t\t\t)', '\t\t)']
    return '\n'.join(out)


def emit_symbol(ref, lib_id, value, footprint, x, y, side, pins, root_uuid):
    ext_x = max([abs(p['x']) for p in pins.values()] or [0])
    ext_y = max([abs(p['y']) for p in pins.values()] or [0])
    if side == 'right':
        tx, ty, just = snap(x + ext_x + 2.54), snap(y - 1.27), 'left'
        vy = snap(y + 1.27)
    else:
        tx, ty, just = x, snap(y - ext_y - 5.08), None
        vy = snap(y - ext_y - 2.54)

    virtual = ref.startswith('#')
    out = ['\t(symbol', f'\t\t(lib_id "{lib_id}")',
           f'\t\t(at {fmt(x)} {fmt(y)} 0)', '\t\t(unit 1)', '\t\t(body_style 1)',
           '\t\t(exclude_from_sim no)',
           f'\t\t(in_bom {"no" if virtual else "yes"})',
           '\t\t(on_board yes)',
           f'\t\t(in_pos_files {"no" if virtual else "yes"})',
           '\t\t(dnp no)', f'\t\t(uuid "{uid("sym", ref)}")',
           emit_property('Reference', ref, tx, ty, 0, False, just),
           emit_property('Value', value, tx, vy, 0, False, just),
           emit_property('Footprint', footprint, x, y, 0, True),
           emit_property('Datasheet', '', x, y, 0, True)]
    for num in sorted(pins, key=lambda s: (len(s), s)):
        out.append(f'\t\t(pin "{num}"\n\t\t\t(uuid "{uid("pin", ref, num)}")\n\t\t)')
    out += ['\t\t(instances', '\t\t\t(project "board"',
            f'\t\t\t\t(path "/{root_uuid}"', f'\t\t\t\t\t(reference "{ref}")',
            '\t\t\t\t\t(unit 1)', '\t\t\t\t)', '\t\t\t)', '\t\t)', '\t)']
    return '\n'.join(out)


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def build():
    original = SCH.read_text(encoding='utf-8')
    root_uuid = re.search(r'\(uuid "([^"]+)"\)', original).group(1)

    # Harvest definitions from the existing sheet, then fill gaps from the libs.
    lib_blocks, pin_maps = {}, {}
    needed = sorted({p[0] for p in design.PARTS.values()})
    for lib_id in needed:
        blk = find_block(original, lib_id)
        source = 'sheet'
        if blk is None:
            blk = load_lib_symbol(lib_id)
            source = 'library'
        if blk is None:
            raise SystemExit(f'cannot find symbol {lib_id}')
        lib_blocks[lib_id] = blk
        pin_maps[lib_id] = symbol_pins(blk)
        print(f'  symbol {lib_id:<52} <- {source} '
              f'({len(pin_maps[lib_id])} pins)')

    # Validate the declaration against the real pinouts before emitting.
    problems = []
    seen = set()
    for net, members in design.NETS.items():
        for ref, pin, expect in members:
            if ref not in design.PARTS:
                problems.append(f'{net}: unknown part {ref}')
                continue
            pins = pin_maps[design.PARTS[ref][0]]
            if pin not in pins:
                problems.append(f'{net}: {ref} has no pin {pin} '
                                f'(has {sorted(pins)})')
                continue
            actual = pins[pin]['name']
            if expect is not None and actual != expect:
                problems.append(f'{net}: {ref}.{pin} is named "{actual}", '
                                f'declaration expected "{expect}"')
            if (ref, pin) in seen:
                problems.append(f'{ref}.{pin} appears on more than one net')
            seen.add((ref, pin))
    for ref, pin in design.NO_CONNECT:
        if (ref, pin) in seen:
            problems.append(f'{ref}.{pin} is both wired and no-connect')
        pins = pin_maps[design.PARTS[ref][0]]
        if pin not in pins:
            problems.append(f'no-connect {ref}.{pin} does not exist')
        seen.add((ref, pin))
    # Every pin of every part must be accounted for.
    for ref, (lib_id, *_rest) in design.PARTS.items():
        for pin in pin_maps[lib_id]:
            if (ref, pin) not in seen:
                problems.append(f'{ref}.{pin} '
                                f'({pin_maps[lib_id][pin]["name"] or "unnamed"}) '
                                f'is neither wired nor marked no-connect')
    if problems:
        print('\nDECLARATION ERRORS:')
        for p in problems:
            print(f'  - {p}')
        raise SystemExit(1)

    # Symbol origins are snapped to the connectivity grid up front. Library pin
    # offsets are all multiples of 1.27 mm, so an on-grid origin guarantees
    # on-grid pins and lets the stubs actually land on them.
    pos = {ref: (snap(p[3]), snap(p[4])) for ref, p in design.PARTS.items()}

    # ---- emit -----------------------------------------------------------
    body = []
    for ref, (lib_id, value, fp, _x, _y, side) in design.PARTS.items():
        x, y = pos[ref]
        body.append(emit_symbol(ref, lib_id, value, fp, x, y, side,
                                pin_maps[lib_id], root_uuid))

    conn = []
    for net, members in design.NETS.items():
        for ref, pin, _ in members:
            lib_id = design.PARTS[ref][0]
            sx, sy = pos[ref]
            p = pin_maps[lib_id][pin]
            px, py = pin_at(p['x'], p['y'], sx, sy)
            dx, dy = OUTWARD[p['ang'] % 360]
            ex, ey = snap(px + dx * STUB), snap(py + dy * STUB)
            key = f'{ref}.{pin}'
            conn.append(emit_wire(px, py, ex, ey, key))
            conn.append(emit_label(net, ex, ey, LABEL_ANGLE[(dx, dy)], key))

    for ref, pin in design.NO_CONNECT:
        lib_id = design.PARTS[ref][0]
        sx, sy = pos[ref]
        p = pin_maps[lib_id][pin]
        px, py = pin_at(p['x'], p['y'], sx, sy)
        conn.append(emit_no_connect(px, py, f'{ref}.{pin}'))

    libs = '\n'.join(reindent(lib_blocks[k], 2) for k in needed)
    return '\n'.join([
        '(kicad_sch',
        '\t(version 20260306)',
        '\t(generator "eeschema")',
        '\t(generator_version "10.0")',
        f'\t(uuid "{root_uuid}")',
        f'\t(paper "{design.PAPER}")',
        '\t(lib_symbols',
        libs,
        '\t)',
        '\n'.join(conn),
        '\n'.join(body),
        '\t(sheet_instances',
        '\t\t(path "/"',
        '\t\t\t(page "1")',
        '\t\t)',
        '\t)',
        '\t(embedded_fonts no)',
        ')',
        '',
    ])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true',
                    help='validate and report only, do not write')
    args = ap.parse_args()

    print('Resolving symbols:')
    text = build()

    nets = len(design.NETS)
    pins = sum(len(v) for v in design.NETS.values())
    print(f'\nOK: {len(design.PARTS)} symbols, {nets} nets, {pins} wired pins, '
          f'{len(design.NO_CONNECT)} no-connects')

    if args.check:
        print('--check: not written')
        return
    # LF, matching what KiCad itself writes. Letting Python translate to CRLF on
    # Windows would show every line as changed on the next diff.
    SCH.write_text(text, encoding='utf-8', newline='\n')
    print(f'wrote {SCH} ({len(text)} bytes)')


if __name__ == '__main__':
    main()
