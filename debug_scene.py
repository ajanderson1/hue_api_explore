#!/usr/bin/env python3
"""Debug script to test scene recall with duration and see what the API returns."""

import asyncio
import json

from hue_controller import BridgeConnector, DeviceManager


async def main():
    connector = BridgeConnector("config.json")
    dm = DeviceManager(connector)

    print("Syncing state from bridge...")
    await dm.sync_state()

    # Find the Sleep Fade 30 scene
    scene = None
    for s in dm.scenes.values():
        if "Sleep Fade" in s.name:
            scene = s
            break

    if not scene:
        print("Scene not found")
        await connector.close()
        return

    print(f"Found scene: {scene.name} (ID: {scene.id})")

    # Get full scene details
    print("\n--- Scene Details from API ---")
    response = await connector.get(f"/resource/scene/{scene.id}")
    print(json.dumps(response, indent=2))

    # Try recall with duration and capture response
    print("\n--- Attempting recall with 30 min duration ---")
    duration_ms = 30 * 60 * 1000

    recall_payload = {
        "recall": {
            "action": "active",
            "duration": duration_ms
        }
    }
    print(f"Payload: {json.dumps(recall_payload, indent=2)}")

    try:
        result = await connector.put(f"/resource/scene/{scene.id}", recall_payload)
        print(f"Response: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    # Also try setting dynamics duration directly on a light
    print("\n--- Testing dynamics.duration on light directly ---")
    bedroom = None
    for room in dm.rooms.values():
        if "bedroom" in room.name.lower():
            bedroom = room
            break

    if bedroom:
        lights = dm.get_lights_for_target(bedroom)
        if lights:
            light = lights[0]
            print(f"Testing on light: {light.name} (ID: {light.id})")

            # Try setting brightness with dynamics duration
            light_payload = {
                "dimming": {"brightness": 50},
                "dynamics": {"duration": duration_ms}
            }
            print(f"Light payload: {json.dumps(light_payload, indent=2)}")

            try:
                result = await connector.put(f"/resource/light/{light.id}", light_payload)
                print(f"Response: {json.dumps(result, indent=2)}")
            except Exception as e:
                print(f"Error: {e}")

    await connector.close()


if __name__ == "__main__":
    asyncio.run(main())
