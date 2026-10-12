"""Open the building door from this PC.

Presses the node's Open door button over the ESPHome API and waits for the
transmit result. The frame unlocks the entrance, so run it only when someone
is there to use the door.

    .venv\\Scripts\\python.exe tools\\open_door.py
    .venv\\Scripts\\python.exe tools\\open_door.py 192.168.50.138

tools\\open_door.bat does the same and keeps the window open.
"""

import asyncio
import inspect
import re
import sys
from pathlib import Path

import yaml
from aioesphomeapi import APIClient, LogLevel

ROOT = Path(__file__).resolve().parents[1]
SECRETS = ROOT / "esphome" / "secrets.yaml"
DEFAULT_HOST = "192.168.50.138"
ANSI = re.compile(r"\x1b\[[0-9;]*m")
# The node waits up to 5 s for a quiet line, then spends ~300 ms probing.
WATCH_S = 8.0


def load_key():
    with SECRETS.open(encoding="utf-8") as f:
        return yaml.safe_load(f)["api_key"]


def interesting(line):
    return any(
        token in line
        for token in (
            "queued 0x",
            "tx begin",
            "tx done",
            "tx aborted",
            "tx pending",
            "tx probe",
            "twai_transmit failed",
            "line never went quiet",
            "bus-off",
        )
    )


def verdict(lines):
    done = next((line for line in reversed(lines) if "tx done:" in line), None)
    if done:
        if "state=running" in done and "tec=0" in done:
            return "opened: frame went out and was acknowledged (tx done, tec=0)"
        return "sent, but the controller was not clean: " + done.split("]: ", 1)[-1]
    if any("line never went quiet" in line or "tx aborted" in line for line in lines):
        return "not sent: the line stayed busy (a call or monitoring session)"
    if any("bus-off" in line or "twai_transmit failed" in line for line in lines):
        return "failed: the frame was rejected on the bus"
    return "no transmit result within %.0f s — the node may still be waiting" % WATCH_S


async def run(host):
    cli = APIClient(host, 6053, None, noise_psk=load_key())
    await cli.connect(login=True)
    lines = []

    def on_log(msg):
        raw = getattr(msg, "message", msg)
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8", "replace")
        line = ANSI.sub("", str(raw)).rstrip()
        if interesting(line):
            lines.append(line)
            print(line, flush=True)

    try:
        result = cli.subscribe_logs(on_log, log_level=LogLevel.LOG_LEVEL_DEBUG)
        if inspect.isawaitable(result):
            await result
        await asyncio.sleep(0.4)

        entities = (await cli.list_entities_services())[0]
        button = next(
            (e for e in entities if type(e).__name__ == "ButtonInfo" and e.name == "Open door"),
            None,
        )
        if button is None:
            print("Open door button is not on this node")
            return 1

        result = cli.button_command(button.key)
        if inspect.isawaitable(result):
            await result
        print("pressed Open door on %s" % host, flush=True)

        loop = asyncio.get_running_loop()
        deadline = loop.time() + WATCH_S
        while loop.time() < deadline:
            if any("tx done:" in line or "tx aborted" in line or "line never went quiet" in line for line in lines):
                break
            await asyncio.sleep(0.1)
    finally:
        await cli.disconnect()

    print(verdict(lines))
    return 0 if any("tx done:" in line and "tec=0" in line for line in lines) else 1


def main(argv):
    host = argv[0] if argv else DEFAULT_HOST
    raise SystemExit(asyncio.run(run(host)))


if __name__ == "__main__":
    main(sys.argv[1:])
