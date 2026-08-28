"""Print ESPHome logs for a few seconds, including boot lines.

Usage: python tools/watch_logs.py [host] [seconds]
"""

import asyncio
import inspect
import re
import sys

import yaml
from aioesphomeapi import APIClient, LogLevel

DEFAULT_HOST = "electra-intercom.local"
ANSI = re.compile(r"\x1b\[[0-9;]*m")


async def run(host, watch_s):
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
        result = cli.subscribe_logs(on_log, log_level=LogLevel.LOG_LEVEL_INFO)
        if inspect.isawaitable(result):
            await result
        await asyncio.sleep(watch_s)
    finally:
        await cli.disconnect()

    interesting = re.compile(
        r"boot|reset|restart|panic|brownout|safe.mode|wifi|ota|electra_can",
        re.I,
    )
    print("--- all %d lines, interesting ones first ---" % len(lines))
    for line in lines:
        if interesting.search(line):
            print(line)
    print("--- full ---")
    for line in lines:
        print(line)


def main(argv):
    host = argv[0] if argv else DEFAULT_HOST
    watch_s = float(argv[1]) if len(argv) > 1 else 20.0
    asyncio.run(run(host, watch_s))


if __name__ == "__main__":
    main(sys.argv[1:])
