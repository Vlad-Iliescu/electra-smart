"""Dump placed symbols from a .kicad_sch as Ref / Value / Footprint / lib_id.

Reads the top-level (symbol ...) instances only, skipping the (lib_symbols ...)
block, so the output is the actual placed parts rather than library definitions.
"""

import re
import sys
from pathlib import Path


def tokenize(text):
    """Yield (kind, value) for '(', ')' and quoted strings."""
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == '(':
            yield '(', None
            i += 1
        elif c == ')':
            yield ')', None
            i += 1
        elif c == '"':
            j = i + 1
            buf = []
            while j < n:
                if text[j] == '\\':
                    buf.append(text[j + 1])
                    j += 2
                elif text[j] == '"':
                    break
                else:
                    buf.append(text[j])
                    j += 1
            yield 'str', ''.join(buf)
            i = j + 1
        elif c.isspace():
            i += 1
        else:
            j = i
            while j < n and not text[j].isspace() and text[j] not in '()"':
                j += 1
            yield 'atom', text[i:j]
            i = j


def parse(text):
    stack = [[]]
    for kind, val in tokenize(text):
        if kind == '(':
            new = []
            stack[-1].append(new)
            stack.append(new)
        elif kind == ')':
            stack.pop()
        else:
            stack[-1].append(val)
    return stack[0][0]


def head(node):
    return node[0] if node and isinstance(node[0], str) else None


def children(node, name):
    return [c for c in node if isinstance(c, list) and head(c) == name]


def props(sym):
    out = {}
    for p in children(sym, 'property'):
        if len(p) >= 3 and isinstance(p[1], str) and isinstance(p[2], str):
            out[p[1]] = p[2]
    return out


def main(path):
    tree = parse(Path(path).read_text(encoding='utf-8'))
    rows = []
    for sym in children(tree, 'symbol'):
        lib = children(sym, 'lib_id')
        if not lib:
            continue
        p = props(sym)
        ref = p.get('Reference', '?')
        if ref.startswith('#'):
            continue
        rows.append((ref, p.get('Value', ''), p.get('Footprint', ''), lib[0][1]))

    def key(r):
        m = re.match(r'^([A-Za-z#]+)0*(\d*)', r[0])
        return (m.group(1), int(m.group(2) or 0))

    rows.sort(key=key)
    w = [max(len(r[i]) for r in rows) for i in range(3)] if rows else [0, 0, 0]
    print(f"{'REF'.ljust(w[0])}  {'VALUE'.ljust(w[1])}  {'FOOTPRINT'.ljust(w[2])}  LIB_ID")
    for r in rows:
        print(f"{r[0].ljust(w[0])}  {r[1].ljust(w[1])}  {r[2].ljust(w[2])}  {r[3]}")
    print(f"\n{len(rows)} placed symbols")


if __name__ == '__main__':
    main(sys.argv[1])
