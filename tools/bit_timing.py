"""Measure how truthfully each bit is rendered on the C/D line.

Written to answer one question: our node transmits a complete, well-formed frame
and other nodes reject it, so the levels must be right at our own sample point
while the edges are not where a receiver expects them.

An open-drain driver is asymmetric by construction. It sinks hard through a
series resistor, but recessive is a release, so the rise is only as fast as the
bus pull-up. Dominant runs then measure long and recessive runs short. Our own
controller can tolerate a skew that still walks another node's resynchronisation
far enough to mis-sample a bit, and one mis-sampled bit is a CRC mismatch.

So this ignores frame content and reports pulse widths: every run of constant
level as a multiple of the bit time, and how far it strays. Point it at a window
holding one of our frames and at one holding a frame from the terminal, and
compare. A driver that renders bits honestly shows the same small error on both
levels; ours should show dominant long and recessive short by a matching amount.

Usage: python tools/bit_timing.py <digital.csv> [bit_us] [t_start] [t_end]
"""

import sys

from can_decode import BURST_GAP_S, DEFAULT_BIT_US, load_edges, split_bursts

LEVELS = {0: "dominant", 1: "recessive"}


def runs(burst, bit_us):
    """Every constant-level interval, as (level, bits, error_us)."""
    out = []
    for (t0, v0), (t1, _) in zip(burst, burst[1:]):
        dur_us = (t1 - t0) * 1e6
        n = max(round(dur_us / bit_us), 1)
        out.append((v0, n, dur_us - n * bit_us))
    return out


def summarise(all_runs, bit_us):
    """Mean and worst error per level, and the same excluding long holds.

    Long dominant holds are the audio session, not data, and would otherwise
    swamp the average.
    """
    print(f"{'level':<10} {'runs':>5} {'mean err':>10} {'worst err':>10} {'as % of bit':>12}")
    for level in (0, 1):
        sel = [r for r in all_runs if r[0] == level and r[1] <= 8]
        if not sel:
            continue
        errs = [r[2] for r in sel]
        mean = sum(errs) / len(errs)
        worst = max(errs, key=abs)
        print(f"{LEVELS[level]:<10} {len(sel):>5} {mean:>9.2f}u {worst:>9.2f}u {100*mean/bit_us:>11.1f}%")

    dom = [r[2] for r in all_runs if r[0] == 0 and r[1] <= 8]
    rec = [r[2] for r in all_runs if r[0] == 1 and r[1] <= 8]
    if dom and rec:
        skew = sum(dom) / len(dom) - sum(rec) / len(rec)
        print(
            f"\nskew (dominant minus recessive): {skew:+.2f} us = {100*skew/bit_us:+.1f}% of a bit"
        )
        print("A driver that renders both levels alike sits near zero. A large positive")
        print("skew means dominant is being stretched at the cost of recessive, which is")
        print("what a passive recessive recovery looks like.")


def main(path, bit_us=DEFAULT_BIT_US, t_start=None, t_end=None):
    edges = load_edges(path)
    if t_start is not None:
        edges = [e for e in edges if e[0] >= t_start]
    if t_end is not None:
        edges = [e for e in edges if e[0] <= t_end]
    if len(edges) < 3:
        print("not enough edges in that window")
        return

    print(f"{path}\nbit time {bit_us} us, gap {BURST_GAP_S*1e3:.0f} ms starts a new burst\n")

    every = []
    for b in split_bursts(edges):
        if len(b) <= 2:
            continue
        r = runs(b, bit_us)
        every.extend(r)
        widths = ", ".join(f"{n}" for _, n, _ in r[:24])
        print(f"--- burst at t={b[0][0]:.6f}s  {len(r)} runs  widths in bits: {widths}")
        odd = [(lvl, n, e) for lvl, n, e in r if abs(e) > 0.25 * bit_us and n <= 8]
        for lvl, n, e in odd[:8]:
            print(f"      {LEVELS[lvl]:<10} {n} bit(s) off by {e:+.1f} us ({100*e/bit_us:+.0f}% of a bit)")

    print()
    summarise(every, bit_us)


if __name__ == "__main__":
    args = sys.argv[1:]
    main(
        args[0],
        float(args[1]) if len(args) > 1 else DEFAULT_BIT_US,
        float(args[2]) if len(args) > 2 else None,
        float(args[3]) if len(args) > 3 else None,
    )
