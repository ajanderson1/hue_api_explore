#!/usr/bin/env python3
"""Test scene recall with 30-minute duration."""

import asyncio
import json

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
        if scene.name == "Sleep Fade 30" and scene.group_id == bedroom.id:
            print(f"Deleting existing scene: {scene.id}")
            await scene_manager.delete_scene(scene.id)
            await dm.sync_state()

    # Create scene: 1% brightness, 3000K
    print("\nCreating 'Sleep Fade 30' scene with target: 1% brightness, 3000K...")
    actions = []
    for light in lights:
        action = SceneLightAction(
            on=True,
            brightness=1.0,
            color_temperature_mirek=333,  # 3000K
        )
        actions.append(SceneAction(
            target_rid=light.id,
            target_rtype="light",
            action=action
        ))

    request = CreateSceneRequest(
        name="Sleep Fade 30",
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

    # Recall with 30-minute duration
    duration_ms = 30 * 60 * 1000  # 30 minutes = 1,800,000 ms
    print(f"\n--- Recalling scene with {duration_ms}ms (30 min) duration ---")

    payload = {
        "recall": {
            "action": "active",
            "duration": duration_ms
        }
    }
    print(f"Payload: {json.dumps(payload, indent=2)}")

    response = await connector.put(f"/resource/scene/{scene.id}", payload)
    print(f"Response: {json.dumps(response, indent=2)}")

    print("\nChecking brightness every 30 seconds for 3 minutes...")
    print("(If working, brightness should decrease ~3.3% every 30 seconds)")

    for i in range(6):
        await asyncio.sleep(30)
        elapsed_min = (i + 1) * 0.5
        expected = 100 - (99 * elapsed_min / 30)  # Linear from 100 to 1 over 30 min
        for light in lights:
            resp = await connector.get(f"/resource/light/{light.id}")
            data = resp.get("data", [{}])[0]
            brightness = data.get("dimming", {}).get("brightness", "?")
            print(f"  t={elapsed_min}min: {light.name} = {brightness:.1f}% (expected ~{expected:.1f}%)")
        print()

    await connector.close()
    print("Scene remains active. Your lights will continue fading to 1% over 30 minutes.")


if __name__ == "__main__":
    asyncio.run(main())
