#!/usr/bin/env python3
"""Test 30 minute duration to see if it works or is capped."""

import asyncio
import json
import time

from hue_controller import BridgeConnector, DeviceManager


async def main():
    connector = BridgeConnector("config.json")
    dm = DeviceManager(connector)

    print("Syncing state from bridge...")
    await dm.sync_state()

    # Find a bedroom light
    bedroom = None
    for room in dm.rooms.values():
        if "bedroom" in room.name.lower():
            bedroom = room
            break

    if not bedroom:
        print("Bedroom not found")
        await connector.close()
        return

    lights = dm.get_lights_for_target(bedroom)
    if not lights:
        print("No lights found")
        await connector.close()
        return

    light = lights[0]
    print(f"Testing on light: {light.name} (ID: {light.id})")

    # First, set to a known state (on, 100% brightness)
    print("\n1. Setting light to 100% brightness, 3000K...")
    await connector.put(f"/resource/light/{light.id}", {
        "on": {"on": True},
        "dimming": {"brightness": 100},
        "color_temperature": {"mirek": 333}  # 3000K
    })
    await asyncio.sleep(2)

    # Get current state
    response = await connector.get(f"/resource/light/{light.id}")
    current = response.get("data", [{}])[0]
    print(f"   Current state: on={current.get('on', {}).get('on')}, "
          f"brightness={current.get('dimming', {}).get('brightness')}")

    # Test with 30 minute duration (1,800,000 ms)
    duration_ms = 30 * 60 * 1000
    print(f"\n2. Testing {duration_ms}ms (30 min) transition to 1% brightness...")

    await connector.put(f"/resource/light/{light.id}", {
        "dimming": {"brightness": 1},
        "dynamics": {"duration": duration_ms}
    })

    print("   Checking brightness every 30 seconds for 3 minutes...")
    print("   If it transitions immediately, the duration is being ignored/capped.")
    print()

    for i in range(6):
        await asyncio.sleep(30)
        response = await connector.get(f"/resource/light/{light.id}")
        current = response.get("data", [{}])[0]
        brightness = current.get("dimming", {}).get("brightness", "unknown")
        elapsed_min = (i + 1) * 0.5
        expected_pct = 100 - (99 * elapsed_min / 30)  # Linear interpolation from 100 to 1 over 30 min
        print(f"   t={elapsed_min:.1f}min: brightness = {brightness:.2f} (expected ~{expected_pct:.1f} if 30min)")

    await connector.close()
    print("\nDone! (You can stop the script now or let it continue)")


if __name__ == "__main__":
    asyncio.run(main())
