#!/usr/bin/env python3
"""Test different duration values to find the actual limit."""

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
    print("\n1. Setting light to 100% brightness...")
    await connector.put(f"/resource/light/{light.id}", {
        "on": {"on": True},
        "dimming": {"brightness": 100}
    })
    await asyncio.sleep(2)

    # Test with 10 second duration (should be visible)
    print("\n2. Testing 10 second transition to 20% brightness...")
    start = time.time()
    await connector.put(f"/resource/light/{light.id}", {
        "dimming": {"brightness": 20},
        "dynamics": {"duration": 10000}  # 10 seconds
    })

    print("   Waiting 12 seconds to observe...")
    await asyncio.sleep(12)
    elapsed = time.time() - start
    print(f"   Elapsed: {elapsed:.1f}s")

    # Check current state
    response = await connector.get(f"/resource/light/{light.id}")
    current = response.get("data", [{}])[0]
    brightness = current.get("dimming", {}).get("brightness", "unknown")
    print(f"   Current brightness: {brightness}")

    # Reset to 100%
    print("\n3. Resetting to 100%...")
    await connector.put(f"/resource/light/{light.id}", {
        "dimming": {"brightness": 100}
    })
    await asyncio.sleep(2)

    # Test with 60 second duration
    print("\n4. Testing 60 second (1 min) transition to 20% brightness...")
    print("   (Watch your light - it should dim slowly over 1 minute)")
    await connector.put(f"/resource/light/{light.id}", {
        "dimming": {"brightness": 20},
        "dynamics": {"duration": 60000}  # 60 seconds
    })

    print("   Checking brightness every 10 seconds for 70 seconds...")
    for i in range(7):
        await asyncio.sleep(10)
        response = await connector.get(f"/resource/light/{light.id}")
        current = response.get("data", [{}])[0]
        brightness = current.get("dimming", {}).get("brightness", "unknown")
        print(f"   t={10*(i+1)}s: brightness = {brightness}")

    await connector.close()
    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
