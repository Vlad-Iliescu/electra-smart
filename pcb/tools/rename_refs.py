"""One-shot atomic renumber of C/R designators in the docs to match KiCad.

The old scheme used refs KiCad cannot represent (C1b, C2a, C2b). Collapsing them
to plain integers is a permutation with overlaps - old C3 becomes C5 while the
new C3 is the old C2a - so every token must be rewritten in a single pass.

Designators that did not exist as real parts (R2, C5 were a removed snubber, and
a bare C2 was shorthand for the 22 uF pair) are mapped to sentinels so they can
be reviewed by hand afterwards.

Usage: python pcb/tools/rename_refs.py [--apply]
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# esphome/README.md is deliberately excluded: its only C/R-shaped tokens are
# "C3 SuperMini" and the C3's TWAI bitrate, i.e. the chip, not designators.
TARGETS = [ROOT / 'docs' / 'wiring.md']

MAP = {
    'C1': 'C1', 'C1b': 'C2', 'C2a': 'C3', 'C2b': 'C4',
    'C3': 'C5', 'C4': 'C6', 'C6': 'C7', 'C7': 'C8',
    'R1': 'R1', 'R3': 'R2', 'R4': 'R3', 'R5': 'R4', 'R6': 'R5',
    'R7': 'R6', 'R8': 'R7', 'R9': 'R8', 'R10': 'R9', 'R11': 'R10',
    # Not real parts in the old scheme - flagged for manual review.
    'R2': '<<R2-SNUBBER>>', 'C5': '<<C5-SNUBBER>>', 'C2': '<<C2-PAIR>>',
}

# Longest alternatives first so C1b wins over C1 and R11 over R1. A leading
# hyphen is excluded so part names are not treated as designators.
TOKENS = sorted(MAP, key=len, reverse=True)
PAT = re.compile(r'(?<!-)\b(' + '|'.join(re.escape(t) for t in TOKENS) + r')\b')

# Chip names embed things that look exactly like designators: the C3 in
# "ESP32-C3" would otherwise be renumbered into "ESP32-C5". Mask them out.
MASK = re.compile(r'ESP32-[A-Z]\d+')
SENTINEL = '\u0000MASK%d\u0000'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()

    total = 0
    for path in TARGETS:
        if not path.exists():
            print(f'skip (missing): {path}')
            continue
        text = path.read_text(encoding='utf-8')
        counts = {}

        masked = []

        def hide(m):
            masked.append(m.group(0))
            return SENTINEL % (len(masked) - 1)

        def sub(m):
            old = m.group(1)
            new = MAP[old]
            if old != new:
                counts[old] = counts.get(old, 0) + 1
            return new

        out = MASK.sub(hide, text)
        out = PAT.sub(sub, out)
        for i, original in enumerate(masked):
            out = out.replace(SENTINEL % i, original)
        print(f'  (masked {len(masked)} chip names)')
        n = sum(counts.values())
        total += n
        print(f'\n{path.relative_to(ROOT)}: {n} replacements')
        for old in sorted(counts, key=lambda k: -counts[k]):
            print(f'    {old:>4} -> {MAP[old]:<16} x{counts[old]}')
        if args.apply and out != text:
            path.write_text(out, encoding='utf-8')

    print(f'\ntotal {total}', '(written)' if args.apply else '(dry run)')


if __name__ == '__main__':
    sys.exit(main())
