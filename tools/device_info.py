"""Print which build is actually running on the node.

An OTA that reports success only proves the image was accepted, not that the node
came up on it - a rollback or a missed reboot looks identical from the host. The
compilation time settles it.

Usage: python tools/device_info.py [host]
"""

import asyncio
import sys

import yaml
from aioesphomeapi import APIClient

DEFAULT_HOST = "electra-intercom.local"

FIELDS = (
    "name",
    "esphome_version",
    "compilation_time",
    "model",
    "manufacturer",
    "friendly_name",
)


async def run(host):
    with open("esphome/secrets.yaml", encoding="utf-8") as f:
        key = yaml.safe_load(f)["api_key"]

    cli = APIClient(host, 6053, None, noise_psk=key)
    await cli.connect(login=True)
    try:
        info = await cli.device_info()
        for field in FIELDS:
            print("%-18s %s" % (field, getattr(info, field, "(absent)")))

        entities = (await cli.list_entities_services())[0]
        names = sorted(e.name for e in entities)
        print("%-18s %d" % ("entities", len(names)))
        for name in names:
            print("    %s" % name)
    finally:
        await cli.disconnect()


def main(argv):
    asyncio.run(run(argv[0] if argv else DEFAULT_HOST))


if __name__ == "__main__":
    main(sys.argv[1:])
