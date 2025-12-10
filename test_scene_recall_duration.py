#!/usr/bin/env python3
"""Test scene recall with duration in the recall object."""

import asyncio
import json
import time

from hue_controller import BridgeConnector, DeviceManager, SceneManager
from hue_controller.models import CreateSceneRequest, SceneAction, SceneLightAction


async def main():
    connector = BridgeConnector("config.json")
    dm = DeviceManager(connector)

    print("Syncing state from bridge...")
    await dm.sync_state()

    # Find bedroom
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

    # Delete existing test scene if it exists
    scene_manager = SceneManager(connector, dm)
    for scene in list(dm.scenes.values()):
        if scene.name == "Test Fade" and scene.group_id == bedroom.id:
            print(f"Deleting existing test scene: {scene.id}")
            await scene_manager.delete_scene(scene.id)
            await dm.sync_state()

    # Create a simple test scene: 20% brightness
    print("\nCreating test scene with target: 20% brightness...")
    actions = []
    for light in lights:
        action = SceneLightAction(
            on=True,
            brightness=20.0,
            color_temperature_mirek=333,
        )
        actions.append(SceneAction(
            target_rid=light.id,
            target_rtype="light",
            action=action
        ))

    request = CreateSceneRequest(
        name="Test Fade",
        group_id=bedroom.id,
        group_type="room",
        actions=actions,
    )

    scene = await scene_manager.create_scene(request)
    print(f"Created scene: {scene.name} (ID: {scene.id})")

    # Set lights to 100%
    print("\nSetting lights to 100% first...")
    for light in lights:
        await connector.put(f"/resource/light/{light.id}", {
            "on": {"on": True},
            "dimming": {"brightness": 100}
        })
    await asyncio.sleep(2)

    # Verify they're at 100%
    for light in lights:
        response = await connector.get(f"/resource/light/{light.id}")
        data = response.get("data", [{}])[0]
        print(f"  {light.name}: {data.get('dimming', {}).get('brightness')}%")

    # Test 1: Use recall.duration (from API docs)
    print("\n--- Test 1: Using recall.duration (60 seconds) ---")
    duration_ms = 60 * 1000  # 60 seconds

    payload = {
        "recall": {
            "action": "active",
            "duration": duration_ms
        }
    }
    print(f"Payload: {json.dumps(payload, indent=2)}")

    response = await connector.put(f"/resource/scene/{scene.id}", payload)
    print(f"Response: {json.dumps(response, indent=2)}")

    print("\nChecking brightness every 10 seconds...")
    for i in range(7):
        await asyncio.sleep(10)
        for light in lights:
            resp = await connector.get(f"/resource/light/{light.id}")
            data = resp.get("data", [{}])[0]
            brightness = data.get("dimming", {}).get("brightness", "?")
            print(f"  t={10*(i+1)}s: {light.name} = {brightness}%")
        if i < 6:
            print()

    # Cleanup
    print("\nCleaning up...")
    await scene_manager.delete_scene(scene.id)
    await connector.close()
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
