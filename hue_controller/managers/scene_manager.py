"""
Scene Manager

Handles scene CRUD operations for Hue API v2.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Callable, Optional

from ..models import (
    Scene,
    SceneDetails,
    SceneAction,
    SceneLightAction,
    ScenePalette,
    ScenePaletteColor,
    CreateSceneRequest,
    UpdateSceneRequest,
    RecallSceneRequest,
    XYColor,
    CommandResult,
    Light,
)
from ..exceptions import (
    SceneCreationError,
    SceneUpdateError,
    SceneNotFoundError,
    TargetNotFoundError,
    APIError,
)

if TYPE_CHECKING:
    from ..bridge_connector import BridgeConnector
    from ..device_manager import DeviceManager

logger = logging.getLogger(__name__)


class SceneManager:
    """Manages scene CRUD operations."""

    def __init__(self, connector: BridgeConnector, device_manager: DeviceManager):
        """
        Initialize the scene manager.

        Args:
            connector: Bridge connector for API calls
            device_manager: Device manager for state access
        """
        self.connector = connector
        self.dm = device_manager

    # =========================================================================
    # Read Operations
    # =========================================================================

    async def get_scene_details(self, scene_id: str) -> SceneDetails:
        """
        Fetch full scene details including actions.

        Args:
            scene_id: Scene ID to fetch

        Returns:
            SceneDetails with full action information

        Raises:
            SceneNotFoundError: If scene doesn't exist
            APIError: On API errors
        """
        try:
            response = await self.connector.get(f"/resource/scene/{scene_id}")
            data = response.get("data", [])
            if not data:
                raise SceneNotFoundError(scene_id)

            scene_data = data[0]
            return self._parse_scene_details(scene_data)

        except APIError as e:
            if e.status_code == 404:
                raise SceneNotFoundError(scene_id)
            raise

    async def get_scene_actions(self, scene_id: str) -> list[SceneAction]:
        """
        Get the per-light actions for a scene.

        Args:
            scene_id: Scene ID

        Returns:
            List of SceneAction objects
        """
        details = await self.get_scene_details(scene_id)
        return details.actions

    async def list_scenes(
        self,
        group_id: Optional[str] = None
    ) -> list[Scene]:
        """
        List all scenes, optionally filtered by group.

        Args:
            group_id: Optional group ID to filter by

        Returns:
            List of Scene objects
        """
        response = await self.connector.get("/resource/scene")
        scenes = []

        for scene_data in response.get("data", []):
            scene = self._parse_scene(scene_data)
            if group_id is None or scene.group_id == group_id:
                scenes.append(scene)

        return sorted(scenes, key=lambda s: s.name)

    # =========================================================================
    # Create Operations
    # =========================================================================

    async def create_scene(self, request: CreateSceneRequest) -> Scene:
        """
        Create a new scene with specified actions.

        Args:
            request: Scene creation request

        Returns:
            Created Scene object

        Raises:
            SceneCreationError: On creation failure
        """
        try:
            response = await self.connector.post(
                "/resource/scene",
                request.to_dict()
            )

            data = response.get("data", [])
            if not data:
                raise SceneCreationError(
                    request.name,
                    "No scene data returned",
                    request.group_id
                )

            scene_id = data[0].get("rid")
            logger.info(f"Created scene '{request.name}' with ID {scene_id}")

            # Fetch and return the created scene
            await self.dm.sync_state()  # Refresh to include new scene
            return self.dm.scenes.get(scene_id) or Scene(
                id=scene_id,
                name=request.name,
                group_id=request.group_id,
                group_type=request.group_type
            )

        except APIError as e:
            raise SceneCreationError(
                request.name,
                str(e),
                request.group_id
            )

    async def create_scene_from_current_state(
        self,
        name: str,
        group_id: str,
        group_type: str = "room"
    ) -> Scene:
        """
        Create a scene capturing current light states.

        Args:
            name: Name for the new scene
            group_id: ID of the room or zone
            group_type: "room" or "zone"

        Returns:
            Created Scene object
        """
        # Get lights in the group
        if group_type == "room" and group_id in self.dm.rooms:
            group = self.dm.rooms[group_id]
        elif group_type == "zone" and group_id in self.dm.zones:
            group = self.dm.zones[group_id]
        else:
            raise SceneCreationError(name, f"Group '{group_id}' not found", group_id)

        lights = self.dm.get_lights_for_target(group)

        # Build actions from current light states
        actions = []
        for light in lights:
            action = SceneLightAction(
                on=light.is_on,
                brightness=light.brightness if light.is_on else None,
                color_xy=light.color_xy if light.supports_color and light.color_xy else None,
                color_temperature_mirek=(
                    light.color_temperature_mirek
                    if light.supports_color_temperature and light.color_temperature_mirek
                    else None
                ),
            )
            actions.append(SceneAction(
                target_rid=light.id,
                target_rtype="light",
                action=action
            ))

        request = CreateSceneRequest(
            name=name,
            group_id=group_id,
            group_type=group_type,
            actions=actions
        )

        return await self.create_scene(request)

    async def duplicate_scene(
        self,
        scene_id: str,
        new_name: str
    ) -> Scene:
        """
        Duplicate an existing scene with a new name.

        Args:
            scene_id: ID of scene to duplicate
            new_name: Name for the new scene

        Returns:
            Created Scene object
        """
        # Get original scene details
        original = await self.get_scene_details(scene_id)

        request = CreateSceneRequest(
            name=new_name,
            group_id=original.group_id or "",
            group_type=original.group_type or "room",
            actions=original.actions,
            palette=original.palette,
            speed=original.speed,
            auto_dynamic=original.auto_dynamic
        )

        return await self.create_scene(request)

    # =========================================================================
    # Update Operations
    # =========================================================================

    async def update_scene(self, request: UpdateSceneRequest) -> Scene:
        """
        Update scene properties or actions.

        Args:
            request: Scene update request

        Returns:
            Updated Scene object

        Raises:
            SceneUpdateError: On update failure
        """
        try:
            payload = request.to_dict()
            if payload:  # Only make request if there's something to update
                await self.connector.put(
                    f"/resource/scene/{request.scene_id}",
                    payload
                )
                logger.info(f"Updated scene {request.scene_id}")

            # Refresh state and return updated scene
            await self.dm.sync_state()
            scene = self.dm.scenes.get(request.scene_id)
            if not scene:
                raise SceneNotFoundError(request.scene_id)
            return scene

        except APIError as e:
            raise SceneUpdateError(request.scene_id, str(e))

    async def update_scene_action(
        self,
        scene_id: str,
        light_id: str,
        action: SceneLightAction
    ) -> None:
        """
        Update a single light's action within a scene.

        Args:
            scene_id: Scene ID
            light_id: Light ID to update
            action: New action settings
        """
        # Get current scene details
        details = await self.get_scene_details(scene_id)

        # Find and update the action for this light
        updated_actions = []
        found = False

        for scene_action in details.actions:
            if scene_action.target_rid == light_id:
                # Merge existing action with new values
                existing = scene_action.action
                merged = SceneLightAction(
                    on=action.on if action.on is not None else existing.on,
                    brightness=action.brightness if action.brightness is not None else existing.brightness,
                    color_xy=action.color_xy if action.color_xy is not None else existing.color_xy,
                    color_temperature_mirek=(
                        action.color_temperature_mirek
                        if action.color_temperature_mirek is not None
                        else existing.color_temperature_mirek
                    ),
                    gradient=action.gradient if action.gradient is not None else existing.gradient,
                    effect=action.effect if action.effect is not None else existing.effect,
                )
                updated_actions.append(SceneAction(
                    target_rid=light_id,
                    target_rtype=scene_action.target_rtype,
                    action=merged
                ))
                found = True
            else:
                updated_actions.append(scene_action)

        if not found:
            # Add new action for this light
            updated_actions.append(SceneAction(
                target_rid=light_id,
                target_rtype="light",
                action=action
            ))

        # Update the scene
        await self.update_scene(UpdateSceneRequest(
            scene_id=scene_id,
            actions=updated_actions
        ))

    async def set_scene_palette(
        self,
        scene_id: str,
        palette: ScenePalette
    ) -> None:
        """
        Set the dynamic palette for a scene.

        Args:
            scene_id: Scene ID
            palette: Palette configuration
        """
        await self.update_scene(UpdateSceneRequest(
            scene_id=scene_id,
            palette=palette
        ))

    async def rename_scene(self, scene_id: str, new_name: str) -> Scene:
        """
        Rename a scene.

        Args:
            scene_id: Scene ID
            new_name: New scene name

        Returns:
            Updated Scene object
        """
        return await self.update_scene(UpdateSceneRequest(
            scene_id=scene_id,
            name=new_name
        ))

    # =========================================================================
    # Delete Operations
    # =========================================================================

    async def delete_scene(self, scene_id: str) -> None:
        """
        Delete a scene.

        Args:
            scene_id: Scene ID to delete

        Raises:
            SceneNotFoundError: If scene doesn't exist
        """
        try:
            await self.connector.delete(f"/resource/scene/{scene_id}")
            logger.info(f"Deleted scene {scene_id}")

            # Remove from local cache
            if scene_id in self.dm.scenes:
                del self.dm.scenes[scene_id]

        except APIError as e:
            if e.status_code == 404:
                raise SceneNotFoundError(scene_id)
            raise

    def get_scenes_for_room(self, room_id: str) -> list[Scene]:
        """
        Get all scenes belonging to a specific room.

        Args:
            room_id: Room ID to filter by

        Returns:
            List of Scene objects for this room
        """
        return [
            scene for scene in self.dm.scenes.values()
            if scene.group_id == room_id
        ]

    async def delete_scenes_for_room(
        self,
        room_id: str,
        force: bool = False,
        on_progress: Optional[Callable[[str, int, int], None]] = None
    ) -> tuple[int, list[str]]:
        """
        Delete all scenes in a room.

        Args:
            room_id: Room ID to delete scenes from
            force: If True, skip confirmation (for CLI --force flag)
            on_progress: Optional callback(scene_name, current, total) for progress

        Returns:
            Tuple of (deleted_count, list of error messages)

        Raises:
            TargetNotFoundError: If room doesn't exist
        """
        # Verify room exists
        room = self.dm.rooms.get(room_id)
        if not room:
            raise TargetNotFoundError(room_id, "room")

        # Get all scenes for this room
        scenes = self.get_scenes_for_room(room_id)

        if not scenes:
            logger.info(f"No scenes found in room '{room.name}'")
            return 0, []

        deleted_count = 0
        errors: list[str] = []

        for i, scene in enumerate(scenes):
            if on_progress:
                on_progress(scene.name, i + 1, len(scenes))

            try:
                await self.delete_scene(scene.id)
                deleted_count += 1
                logger.info(f"Deleted scene '{scene.name}' ({i + 1}/{len(scenes)})")
            except Exception as e:
                error_msg = f"Failed to delete '{scene.name}': {e}"
                errors.append(error_msg)
                logger.error(error_msg)

        return deleted_count, errors

    # =========================================================================
    # Recall Operations
    # =========================================================================

    async def recall_scene(
        self,
        scene_id: str,
        action: str = "active",
        duration_ms: Optional[int] = None,
        brightness: Optional[float] = None
    ) -> CommandResult:
        """
        Recall (activate) a scene.

        Args:
            scene_id: Scene ID to recall
            action: Recall action ("active", "dynamic_palette", "static")
            duration_ms: Optional transition duration
            brightness: Optional brightness override

        Returns:
            CommandResult indicating success/failure
        """
        scene = self.dm.scenes.get(scene_id)
        if not scene:
            raise SceneNotFoundError(scene_id)

        request = RecallSceneRequest(
            scene_id=scene_id,
            action=action,
            duration_ms=duration_ms,
            brightness=brightness
        )

        try:
            await self.connector.put(
                f"/resource/scene/{scene_id}",
                request.to_dict()
            )

            return CommandResult(
                success=True,
                message=f"Activated scene '{scene.name}'",
                target_name=scene.name
            )

        except APIError as e:
            return CommandResult(
                success=False,
                message=f"Failed to activate scene: {e}",
                errors=[str(e)]
            )

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _parse_scene(self, data: dict) -> Scene:
        """Parse API response into Scene object."""
        group_ref = data.get("group", {})

        return Scene(
            id=data.get("id", ""),
            name=data.get("metadata", {}).get("name", "Unknown"),
            id_v1=data.get("id_v1"),
            group_id=group_ref.get("rid"),
            group_type=group_ref.get("rtype"),
            image_id=data.get("metadata", {}).get("image", {}).get("rid"),
            speed=data.get("speed", 0.5),
            auto_dynamic=data.get("auto_dynamic", False),
        )

    def _parse_scene_details(self, data: dict) -> SceneDetails:
        """Parse API response into SceneDetails object."""
        base = self._parse_scene(data)

        # Parse actions
        actions = []
        for action_data in data.get("actions", []):
            target = action_data.get("target", {})
            action = action_data.get("action", {})

            light_action = SceneLightAction(
                on=action.get("on", {}).get("on"),
                brightness=action.get("dimming", {}).get("brightness"),
                color_xy=self._parse_xy_color(action.get("color", {}).get("xy")),
                color_temperature_mirek=action.get("color_temperature", {}).get("mirek"),
                effect=action.get("effects", {}).get("effect"),
            )

            actions.append(SceneAction(
                target_rid=target.get("rid", ""),
                target_rtype=target.get("rtype", "light"),
                action=light_action
            ))

        # Parse palette
        palette = None
        palette_data = data.get("palette", {})
        if palette_data:
            colors = []
            for c in palette_data.get("color", []):
                xy = self._parse_xy_color(c.get("color", {}).get("xy"))
                if xy:
                    dimming = c.get("dimming", {}).get("brightness")
                    colors.append(ScenePaletteColor(color=xy, dimming=dimming))

            palette = ScenePalette(colors=colors)

        return SceneDetails(
            id=base.id,
            name=base.name,
            id_v1=base.id_v1,
            group_id=base.group_id,
            group_type=base.group_type,
            image_id=base.image_id,
            speed=base.speed,
            auto_dynamic=base.auto_dynamic,
            actions=actions,
            palette=palette
        )

    def _parse_xy_color(self, xy_data: Optional[dict]) -> Optional[XYColor]:
        """Parse xy color from API response."""
        if not xy_data:
            return None
        return XYColor(x=xy_data.get("x", 0), y=xy_data.get("y", 0))
