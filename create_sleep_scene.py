#!/usr/bin/env python3
"""
Create a 'Sleep Fade 30' scene in the bedroom and activate it with 30 min transition.

Scene end state:
- Both lights ON at 1% brightness, 3000K color temperature
- The scene recall uses dynamics.duration for 30 minute transition

Key insight: The scene must have on=True for gradual dimming to work.
If on=False, the light turns off immediately regardless of duration.
"""

import asyncio
import sys

from hue_controller import (
    BridgeConnector,
    DeviceManager,
    SceneManager,
)
from hue_controller.models import (
    CreateSceneRequest,
    SceneAction,
    SceneLightAction,
)


async def main():
    connector = BridgeConnector("config.json")
    dm = DeviceManager(connector)

    print("Syncing state from bridge...")
    await dm.sync_state()

    # Find the bedroom
    bedroom = None
    for room in dm.rooms.values():
        if "bedroom" in room.name.lower():
            bedroom = room
            break

    if not bedroom:
        print("Error: Could not find a room with 'bedroom' in the name")
        print("Available rooms:")
        for room in dm.rooms.values():
            print(f"  - {room.name}")
        await connector.close()
        return 1

    print(f"Found room: {bedroom.name} (ID: {bedroom.id})")

    # Get lights in the bedroom
    lights = dm.get_lights_for_target(bedroom)
    print(f"Found {len(lights)} lights in {bedroom.name}:")
    for light in lights:
        print(f"  - {light.name} (ID: {light.id})")

    if not lights:
        print("Error: No lights found in bedroom")
        await connector.close()
        return 1

    # Check if scene already exists and delete it
    scene_manager = SceneManager(connector, dm)
    existing_scene = None
    for scene in dm.scenes.values():
        if scene.name == "Sleep Fade 30" and scene.group_id == bedroom.id:
            existing_scene = scene
            break

    if existing_scene:
        print(f"\nScene 'Sleep Fade 30' already exists (ID: {existing_scene.id})")
        print("Deleting existing scene...")
        await scene_manager.delete_scene(existing_scene.id)
        await dm.sync_state()

    # Create scene actions for each light
    # End state: ON at 1% brightness, 3000K (333 mirek)
    # Note: on=True is critical for gradual dimming to work!
    actions = []
    for light in lights:
        action = SceneLightAction(
            on=True,  # Must be True for gradual transition
            brightness=1.0,  # 1% brightness (minimum visible)
            color_temperature_mirek=333,  # 3000K
        )
        actions.append(SceneAction(
            target_rid=light.id,
            target_rtype="light",
            action=action
        ))

    # Create the scene
    request = CreateSceneRequest(
        name="Sleep Fade 30",
        group_id=bedroom.id,
        group_type="room",
        actions=actions,
    )

    print(f"\nCreating scene 'Sleep Fade 30' in {bedroom.name}...")

    try:
        scene = await scene_manager.create_scene(request)
        print(f"\nSuccess! Created scene:")
        print(f"  Name: {scene.name}")
        print(f"  ID: {scene.id}")
        print(f"  End state: ON at 1% brightness, 3000K")

        # First turn lights on to 100% so we can see the fade
        print("\nSetting lights to 100% brightness first...")
        for light in lights:
            await connector.put(f"/resource/light/{light.id}", {
                "on": {"on": True},
                "dimming": {"brightness": 100}
            })
        await asyncio.sleep(1)

        # Now recall the scene with 30-minute duration using dynamics
        duration_ms = 30 * 60 * 1000  # 30 minutes = 1,800,000 ms

        print(f"\nActivating scene with {duration_ms}ms (30 minute) transition...")

        # The key is to use dynamics.duration in the scene recall
        recall_payload = {
            "recall": {
                "action": "active",
            },
            "dynamics": {
                "duration": duration_ms
            }
        }

        await connector.put(f"/resource/scene/{scene.id}", recall_payload)

        print(f"\nScene activated!")
        print(f"Your bedroom lights will now gradually fade from 100% to 1% over 30 minutes.")
        print(f"End state: On at 1% brightness, 3000K color temperature")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        await connector.close()
        return 1

    await connector.close()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
