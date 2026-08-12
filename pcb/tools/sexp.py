"""Minimal S-expression reader/writer for KiCad files.

Lists become python lists; atoms and quoted strings become str, with quoted
strings wrapped in Q() so round-tripping preserves quoting.
"""


class Q(str):
    """A string that was quoted in the source and must be re-quoted on output."""
    __slots__ = ()


def tokenize(text):
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c in '()':
            yield c, None
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


def loads(text):
    stack = [[]]
    for kind, val in tokenize(text):
        if kind == '(':
            new = []
            stack[-1].append(new)
            stack.append(new)
        elif kind == ')':
            stack.pop()
        elif kind == 'str':
            stack[-1].append(Q(val))
        else:
            stack[-1].append(val)
    return stack[0][0]


def esc(s):
    return s.replace('\\', '\\\\').replace('"', '\\"')


def dumps(node, indent=0):
    """Serialise back to KiCad-style text with tab indentation."""
    pad = '\t' * indent
    if not isinstance(node, list):
        return f'"{esc(node)}"' if isinstance(node, Q) else str(node)

    # Leaf-ish list: head plus only scalars -> keep on one line.
    if all(not isinstance(c, list) for c in node):
        inner = ' '.join(dumps(c) for c in node)
        return f'{pad}({inner})'

    out = [f'{pad}({dumps(node[0]) if not isinstance(node[0], list) else ""}']
    if isinstance(node[0], list):
        out = [f'{pad}(']
        rest = node
    else:
        rest = node[1:]
        # Trailing scalars directly after the head stay on the head line.
        k = 0
        while k < len(rest) and not isinstance(rest[k], list):
            out[0] += ' ' + dumps(rest[k])
            k += 1
        rest = rest[k:]
    for c in rest:
        out.append(dumps(c, indent + 1))
    out.append(f'{pad})')
    return '\n'.join(out)


def head(node):
    return node[0] if isinstance(node, list) and node and isinstance(node[0], str) else None


def kids(node, name):
    return [c for c in node if isinstance(c, list) and head(c) == name]


def kid(node, name):
    got = kids(node, name)
    return got[0] if got else None


def val(node, name, default=None):
    """First scalar argument of the named child."""
    c = kid(node, name)
    return c[1] if c and len(c) > 1 else default
