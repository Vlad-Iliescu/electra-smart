"""Analyze an exported Saleae digital.csv from the Electra C/D bus.

Groups edge transitions into bursts, derives the base bit time from the
shortest pulse, and renders each burst as a bit string so command frames
can be compared across button presses.
"""

import csv
import sys
from math import isclose

BURST_GAP_S = 0.001  # gap larger than this starts a new burst


def load_edges(path, channel):
    edges = []
    with open(path, newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        col = header.index(channel)
        for row in reader:
            edges.append((float(row[0]), int(row[col])))
    return edges


def split_bursts(edges):
    bursts, current = [], []
    for i, (t, v) in enumerate(edges):
        if current and (t - current[-1][0]) > BURST_GAP_S:
            bursts.append(current)
            current = []
        current.append((t, v))
    if current:
        bursts.append(current)
    return bursts


def pulse_widths(burst):
    widths = []
    for (t0, v0), (t1, _) in zip(burst, burst[1:]):
        widths.append((v0, t1 - t0))
    return widths


def histogram(all_widths):
    """Cluster pulse widths so the quantization step (bit time) is visible."""
    print("=== pulse width histogram (us) ===")
    buckets = {}
    for w in sorted(all_widths):
        us = w * 1e6
        key = None
        for k in buckets:
            if isclose(k, us, abs_tol=6.0):
                key = k
                break
        if key is None:
            buckets[us] = [us]
        else:
            buckets[key].append(us)
    for k in sorted(buckets):
        vals = buckets[k]
        print(f"  {sum(vals)/len(vals):8.2f} us   count={len(vals):3d}   "
              f"min={min(vals):.2f} max={max(vals):.2f}")
    print()


def main(path):
    edges = load_edges(path, "Channel 0")
    bursts = [b for b in split_bursts(edges) if len(b) > 2]

    all_widths = [w for b in bursts for _, w in pulse_widths(b)]
    unit = min(all_widths)
    print(f"bursts with data: {len(bursts)}")
    print(f"shortest pulse (bit time): {unit*1e6:.2f} us  ->  {1/unit:.0f} bps")
    print()
    histogram(all_widths)

    for i, b in enumerate(bursts):
        start, end = b[0][0], b[-1][0]
        widths = pulse_widths(b)
        bits = []
        for level, w in widths:
            n = round(w / unit)
            bits.append(str(level) * max(n, 1))
        bitstr = "".join(bits)
        print(f"--- burst {i}  t={start:.6f}s  dur={(end-start)*1e3:.3f}ms  edges={len(b)}")
        print(f"    multiples: {[round(w/unit) for _, w in widths]}")
        print(f"    bits({len(bitstr)}): {bitstr}")
        print()

    # compare bursts pairwise by bit string
    print("=== repeatability ===")
    strings = []
    for b in bursts:
        widths = pulse_widths(b)
        strings.append("".join(str(l) * max(round(w / unit), 1) for l, w in widths))
    for i in range(len(strings)):
        for j in range(i + 1, len(strings)):
            if strings[i] == strings[j]:
                print(f"burst {i} == burst {j}  (identical)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "digital.csv")
