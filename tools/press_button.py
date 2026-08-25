"""Press one of the node's buttons over the ESPHome API and print what it logged.

Exists because the interesting buttons on this node act on a live intercom bus,
so a press has to be correlated with logs and with an analyzer capture rather
than just fired and forgotten.

Usage: python tools/press_button.py "Open door" [host] [seconds_to_watch]
"""

import asyncio
import inspect
import re
import sys

import yaml
from aioesphomeapi import APIClient, LogLevel

DEFAULT_HOST = "electra-intercom.local"
ANSI = re.compile(r"\x1b\[[0-9;]*m")


async def run(name, host, watch_s):
    with open("esphome/secrets.yaml", encoding="utf-8") as f:
        key = yaml.safe_load(f)["api_key"]

    cli = APIClient(host, 6053, None, noise_psk=key)
    await cli.connect(login=True)
    lines = []

    def on_log(msg):
        raw = getattr(msg, "message", msg)
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8", "replace")
        lines.append(ANSI.sub("", str(raw)).rstrip())

    try:
        # subscribe_logs is sync in some releases and a coroutine in others.
        result = cli.subscribe_logs(on_log, log_level=LogLevel.LOG_LEVEL_VERY_VERBOSE)
        if inspect.isawaitable(result):
            await result
        await asyncio.sleep(2)

        entities = (await cli.list_entities_services())[0]
        buttons = {e.name: e for e in entities if type(e).__name__ == "ButtonInfo"}
        if name not in buttons:
            print("no such button. available: %s" % ", ".join(sorted(buttons)))
            return
        result = cli.button_command(buttons[name].key)
        if inspect.isawaitable(result):
            await result
        print("pressed %r" % name)
        await asyncio.sleep(watch_s)
    finally:
        await cli.disconnect()

    for line in lines:
        print(line)


def main(argv):
    name = argv[0] if argv else "Open door"
    host = argv[1] if len(argv) > 1 else DEFAULT_HOST
    watch_s = float(argv[2]) if len(argv) > 2 else 8.0
    asyncio.run(run(name, host, watch_s))


if __name__ == "__main__":
    main(sys.argv[1:])
