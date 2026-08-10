"""Decode the Electra C/D bus as CAN 2.0A and verify every frame's CRC-15.

Recomputing CRC-15 over the de-stuffed bit stream is the definitive test that the
bit timing and framing are right: the CRC covers the identifier, so a match also
proves the decoded ID is correct.

Handles multiple frames per burst (back-to-back frames separated by less than the
burst gap) and reports long dominant holds, which on this bus mean an active
call/audio session rather than data.

Usage: python tools/can_decode.py <digital.csv> [bit_time_us]
"""

import csv
import sys

BURST_GAP_S = 0.001      # gap larger than this starts a new burst
DEFAULT_BIT_US = 87.9
CRC_POLY = 0x4599
HOLD_BITS = 20           # dominant run longer than this = line held, not data


def load_edges(path, channel="Channel 0"):
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
    for t, v in edges:
        if current and (t - current[-1][0]) > BURST_GAP_S:
            bursts.append(current)
            current = []
        current.append((t, v))
    if current:
        bursts.append(current)
    return bursts


def burst_to_bits(burst, unit_s, tail=16):
    """Expand edges into raw (still bit-stuffed) bits.

    Wire levels map straight onto CAN logic: low = dominant = 0, high = recessive = 1.
    """
    bits = []
    for (t0, v0), (t1, _) in zip(burst, burst[1:]):
        n = max(round((t1 - t0) / unit_s), 1)
        bits.extend([v0] * n)
    bits.extend([burst[-1][1]] * tail)
    return bits


class StuffReader:
    """Reads de-stuffed bits from a raw bit list, tracking raw consumption.

    Stuffing applies from SOF through the CRC field only; the CRC delimiter, ACK
    and EOF are transmitted unstuffed, so those are read with read_raw().
    """

    def __init__(self, raw, pos):
        self.raw = raw
        self.pos = pos
        self.run_val = None
        self.run_len = 0
        self.stuffed = 0

    def read(self, n):
        out = []
        for _ in range(n):
            if self.run_len == 5:
                if self.pos >= len(self.raw):
                    return None
                self.run_val = self.raw[self.pos]
                self.run_len = 1
                self.stuffed += 1
                self.pos += 1
            if self.pos >= len(self.raw):
                return None
            b = self.raw[self.pos]
            self.pos += 1
            if b == self.run_val:
                self.run_len += 1
            else:
                self.run_val, self.run_len = b, 1
            out.append(b)
        return out

    def read_raw(self, n):
        out = self.raw[self.pos:self.pos + n]
        self.pos += n
        return out


def crc15(bits):
    crc = 0
    for b in bits:
        nxt = b ^ ((crc >> 14) & 1)
        crc = (crc << 1) & 0x7FFF
        if nxt:
            crc ^= CRC_POLY
    return crc


def to_int(bits):
    v = 0
    for b in bits:
        v = (v << 1) | b
    return v


def parse_frame(raw, pos):
    """Parse one CAN 2.0A data frame starting at a dominant SOF at raw[pos]."""
    r = StuffReader(raw, pos)
    head = r.read(19)                      # SOF + ID(11) + RTR + IDE + r0 + DLC(4)
    if head is None or head[0] != 0:
        return None
    ident = to_int(head[1:12])
    rtr, ide, r0 = head[12], head[13], head[14]
    dlc = to_int(head[15:19])
    n = min(dlc, 8)
    data_bits = r.read(n * 8)
    if data_bits is None:
        return None
    crc_bits = r.read(15)
    if crc_bits is None:
        return None
    crc_rx = to_int(crc_bits)
    crc_calc = crc15(head + data_bits)
    tail = r.read_raw(3)                   # CRC delim, ACK slot, ACK delim
    r.read_raw(7)                          # EOF
    return {
        "id": ident, "rtr": rtr, "ide": ide, "r0": r0, "dlc": dlc,
        "data": [to_int(data_bits[i * 8:(i + 1) * 8]) for i in range(n)],
        "crc_rx": crc_rx, "crc_calc": crc_calc, "crc_ok": crc_rx == crc_calc,
        "ack": "ACK" if len(tail) > 1 and tail[1] == 0 else "no-ack",
        "stuff": r.stuffed, "end": r.pos,
    }


def decode_burst(raw):
    """Parse as many frames as the burst contains."""
    frames, pos = [], 0
    while pos < len(raw):
        while pos < len(raw) and raw[pos] != 0:   # skip recessive to next SOF
            pos += 1
        if pos >= len(raw):
            break
        f = parse_frame(raw, pos)
        if f is None:
            frames.append({"error": "unparsable", "at": pos})
            break
        frames.append(f)
        pos = max(f["end"], pos + 1)
    return frames


def find_holds(edges, unit_s, min_bits=HOLD_BITS):
    """Intervals where the line sits dominant far longer than any frame field.

    On this bus that means an active call/audio session, not data.
    """
    holds = []
    for (t0, v0), (t1, _) in zip(edges, edges[1:]):
        if v0 == 0 and (t1 - t0) / unit_s > min_bits:
            holds.append((t0, t1 - t0))
    return holds


def main(path, bit_us=DEFAULT_BIT_US):
    unit = bit_us * 1e-6
    edges = load_edges(path)
    bursts = split_bursts(edges)
    holds = find_holds(edges, unit)
    print(f"{path}\nbit time {bit_us} us ({1/unit:.0f} bps)   "
          f"bursts: {len(bursts)}   dominant holds: {len(holds)}\n")

    events = []
    for t, dur in holds:
        events.append((t, "hold", dur))

    ok = total = 0
    for b in bursts:
        if len(b) <= 2:
            continue
        raw = burst_to_bits(b, unit)
        for f in decode_burst(raw):
            total += 1
            if "error" in f:
                print(f"--- t={b[0][0]:.6f}s  UNPARSABLE at bit {f['at']} of {len(raw)}")
                continue
            ok += f["crc_ok"]
            data_hex = " ".join(f"{d:02X}" for d in f["data"])
            status = "MATCH" if f["crc_ok"] else "MISMATCH"
            print(f"--- t={b[0][0]:.6f}s  ID=0x{f['id']:03X}  DLC={f['dlc']}  "
                  f"data: {data_hex}   CRC {status}  {f['ack']}")
            events.append((b[0][0], "frame", (f["id"], f["dlc"], data_hex)))

    print(f"\n=== {ok}/{total} frames with valid CRC-15 ===\n")
    print("timeline:")
    events.sort(key=lambda e: e[0])
    t0 = events[0][0] if events else 0
    for t, kind, payload in events:
        if kind == "hold":
            print(f"  t={t:9.4f}s  (+{t-t0:7.3f})  *** LINE HELD DOMINANT "
                  f"{payload:.3f} s ({payload/unit:.0f} bits) ***")
        else:
            i, d, h = payload
            print(f"  t={t:9.4f}s  (+{t-t0:7.3f})  ID=0x{i:03X}  DLC={d}  {h}")


if __name__ == "__main__":
    main(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_BIT_US)
