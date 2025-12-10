#!/usr/bin/env python3
"""Quick check of current brightness."""

import asyncio
from hue_controller import BridgeConnector, DeviceManager


async def main():
    connector = BridgeConnector("config.json")
    dm = DeviceManager(connector)
    await dm.sync_state()

    for room in dm.rooms.values():
        if "bedroom" in room.name.lower():
            lights = dm.get_lights_for_target(room)
            for light in lights:
                response = await connector.get(f"/resource/light/{light.id}")
                data = response.get("data", [{}])[0]
                brightness = data.get("dimming", {}).get("brightness", "?")
                on_state = data.get("on", {}).get("on", "?")
                print(f"{light.name}: on={on_state}, brightness={brightness}")
            break

    await connector.close()


if __name__ == "__main__":
    asyncio.run(main())
