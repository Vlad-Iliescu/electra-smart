"""Print the live state of the node's entities over the ESPHome API.

Useful for confirming a diagnostic toggle actually went back off, which is not
something the compile or the upload can tell you.

Usage: python tools/device_state.py [host] [name ...]
"""

import asyncio
import inspect
import sys

import yaml
from aioesphomeapi import APIClient

DEFAULT_HOST = "electra-intercom.local"
# The ones worth eyeballing after a debugging session.
DEFAULT_NAMES = (
    "Transmit without ACK",
    "Silent",
    "Auto-open on call",
    "Ring",
    "Monitoring",
    "Bus idle",
)


async def run(host, names):
    with open("esphome/secrets.yaml", encoding="utf-8") as f:
        key = yaml.safe_load(f)["api_key"]

    cli = APIClient(host, 6053, None, noise_psk=key)
    await cli.connect(login=True)
    try:
        entities = (await cli.list_entities_services())[0]
        by_key = {e.key: e for e in entities}
        seen = {}

        def on_state(state):
            info = by_key.get(state.key)
            if info is not None:
                seen[info.name] = getattr(state, "state", None)

        # subscribe_states is sync in some releases and a coroutine in others.
        result = cli.subscribe_states(on_state)
        if inspect.isawaitable(result):
            await result
        await asyncio.sleep(4)
    finally:
        await cli.disconnect()

    for name in names:
        print("%-24s %s" % (name, seen[name] if name in seen else "(not reported)"))


def main(argv):
    host = argv[0] if argv else DEFAULT_HOST
    names = argv[1:] if len(argv) > 1 else DEFAULT_NAMES
    asyncio.run(run(host, names))


if __name__ == "__main__":
    main(sys.argv[1:])
