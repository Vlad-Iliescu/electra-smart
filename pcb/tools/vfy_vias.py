"""List every via, so new ones showing up in a drill diff can be identified."""

import pcbnew

BRD = r"C:\dev\projects\HA\electra-smart\pcb\board\board.kicad_pcb"
NM = 1e6

# The four holes that appeared in the drill file after R12 was placed.
NEW = [(55.12, 50.46), (57.15, 48.08), (58.2, 48.19), (58.54, 49.89)]


def mm(v):
    return v / NM


def main():
    b = pcbnew.LoadBoard(BRD)
    vias = []
    for t in b.Tracks():
        if t.Type() != pcbnew.PCB_VIA_T:
            continue
        p = t.GetPosition()
        # GetWidth() on a via asserts without a layer argument in KiCad 10, and the
        # assert opens a modal dialog that hangs a headless run. Drill is enough.
        vias.append((mm(p.x), mm(p.y), t.GetNetname(), mm(t.GetDrill())))

    print(f"{len(vias)} vias on the board\n")
    print("The four new drill hits:")
    for nx, ny in NEW:
        match = None
        for x, y, net, d in vias:
            if abs(x - nx) < 0.02 and abs(y - ny) < 0.02:
                match = (net, d)
                break
        if match:
            print(f"  ({nx:6.2f}, {ny:6.2f})  net={match[0]:12} drill {match[1]:.2f} mm")
        else:
            print(f"  ({nx:6.2f}, {ny:6.2f})  NOT A VIA - check whether it is a through-hole pad")

    print("\nVia count by net:")
    counts = {}
    for _, _, net, _ in vias:
        counts[net] = counts.get(net, 0) + 1
    for net in sorted(counts, key=lambda n: -counts[n]):
        print(f"  {net or '(none)':14} {counts[net]}")


main()
