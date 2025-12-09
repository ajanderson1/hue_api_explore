"""
Device state management with caching and fuzzy name matching.
"""

import asyncio
import logging
import re
from typing import Optional, Union

from .bridge_connector import BridgeConnector
from .exceptions import TargetNotFoundError, SceneNotFoundError
from .models import (
    ConnectivityStatus,
    Device,
    GamutType,
    GroupedLight,
    Light,
    ResourceReference,
    Room,
    Scene,
    XYColor,
    Zone,
    GAMUT_A,
    GAMUT_B,
    GAMUT_C,
)

logger = logging.getLogger(__name__)

# Type alias for targets
Target = Union[Light, Room, Zone]


class DeviceManager:
    """
    Manages device state with caching and provides fuzzy name matching.

    Fetches and caches:
        - Lights (individual light services)
        - Devices (physical devices)
        - Rooms and Zones (groupings)
        - Grouped lights (for controlling groups)
        - Scenes (stored configurations)
        - Connectivity status (for reachability checks)
    """

    def __init__(self, connector: BridgeConnector):
        """
        Initialize the device manager.

        Args:
            connector: Configured BridgeConnector instance
        """
        self.connector = connector

        # Resource caches (UUID -> resource)
        self.lights: dict[str, Light] = {}
        self.devices: dict[str, Device] = {}
        self.rooms: dict[str, Room] = {}
        self.zones: dict[str, Zone] = {}
        self.grouped_lights: dict[str, GroupedLight] = {}
        self.scenes: dict[str, Scene] = {}

        # Name index for fuzzy matching (normalized_name -> (type, uuid))
        self._name_index: dict[str, tuple[str, str]] = {}

        # Mapping from device to its lights
        self._device_to_lights: dict[str, list[str]] = {}

        # Mapping from light to its connectivity service
        self._light_to_connectivity: dict[str, str] = {}

        # Event listener task
        self._event_task: Optional[asyncio.Task] = None

    @staticmethod
    def _normalize_name(name: str) -> str:
        """
        Normalize a name for fuzzy matching.

        Removes spaces, punctuation, and lowercases.
        "Living Room" -> "livingroom"
        """
        return re.sub(r'[^a-z0-9]', '', name.lower())

    def _index_name(self, name: str, resource_type: str, resource_id: str) -> None:
        """Add a name to the index for lookup."""
        normalized = self._normalize_name(name)
        self._name_index[normalized] = (resource_type, resource_id)

    async def sync_state(self) -> None:
        """
        Fetch all resources from the bridge and build state caches.

        This performs multiple parallel API calls to fetch:
        - devices, lights, rooms, zones, grouped_lights, scenes, zigbee_connectivity
        """
        logger.info("Syncing device state from bridge...")

        # Fetch all resource types in parallel
        results = await asyncio.gather(
            self.connector.get("/resource/device"),
            self.connector.get("/resource/light"),
            self.connector.get("/resource/room"),
            self.connector.get("/resource/zone"),
            self.connector.get("/resource/grouped_light"),
            self.connector.get("/resource/scene"),
            self.connector.get("/resource/zigbee_connectivity"),
            return_exceptions=True
        )

        # Process results
        device_data, light_data, room_data, zone_data, grouped_data, scene_data, connectivity_data = results

        # Clear existing caches
        self.lights.clear()
        self.devices.clear()
        self.rooms.clear()
        self.zones.clear()
        self.grouped_lights.clear()
        self.scenes.clear()
        self._name_index.clear()
        self._device_to_lights.clear()
        self._light_to_connectivity.clear()

        # Build connectivity map first (device_id -> status)
        connectivity_map: dict[str, ConnectivityStatus] = {}
        device_connectivity_map: dict[str, str] = {}  # device_id -> connectivity_id
        if isinstance(connectivity_data, dict):
            for conn in connectivity_data.get("data", []):
                conn_id = conn.get("id")
                owner = conn.get("owner", {})
                device_id = owner.get("rid")
                status_str = conn.get("status", "unknown")
                try:
                    status = ConnectivityStatus(status_str)
                except ValueError:
                    status = ConnectivityStatus.UNKNOWN

                if device_id:
                    connectivity_map[device_id] = status
                    device_connectivity_map[device_id] = conn_id

        # Process devices
        if isinstance(device_data, dict):
            for d in device_data.get("data", []):
                device = self._parse_device(d, connectivity_map)
                self.devices[device.id] = device
                self._index_name(device.name, "device", device.id)

                # Build device -> lights mapping
                light_ids = [
                    s.rid for s in device.service_ids
                    if s.rtype == "light"
                ]
                if light_ids:
                    self._device_to_lights[device.id] = light_ids

        # Process lights
        if isinstance(light_data, dict):
            for l in light_data.get("data", []):
                light = self._parse_light(l)

                # Get connectivity status from owner device
                owner = l.get("owner", {})
                owner_id = owner.get("rid")
                if owner_id and owner_id in connectivity_map:
                    light.connectivity_status = connectivity_map[owner_id]
                    # Map light to connectivity service
                    if owner_id in device_connectivity_map:
                        self._light_to_connectivity[light.id] = device_connectivity_map[owner_id]

                self.lights[light.id] = light
                self._index_name(light.name, "light", light.id)

        # Process rooms
        if isinstance(room_data, dict):
            for r in room_data.get("data", []):
                room = self._parse_room(r)
                self.rooms[room.id] = room
                self._index_name(room.name, "room", room.id)

        # Process zones
        if isinstance(zone_data, dict):
            for z in zone_data.get("data", []):
                zone = self._parse_zone(z)
                self.zones[zone.id] = zone
                self._index_name(zone.name, "zone", zone.id)

        # Process grouped lights
        if isinstance(grouped_data, dict):
            for g in grouped_data.get("data", []):
                grouped = self._parse_grouped_light(g)
                self.grouped_lights[grouped.id] = grouped

        # Process scenes
        if isinstance(scene_data, dict):
            for s in scene_data.get("data", []):
                scene = self._parse_scene(s)
                self.scenes[scene.id] = scene
                self._index_name(scene.name, "scene", scene.id)

        logger.info(
            f"Synced: {len(self.lights)} lights, {len(self.rooms)} rooms, "
            f"{len(self.zones)} zones, {len(self.scenes)} scenes"
        )

    def _parse_device(self, data: dict, connectivity_map: dict[str, ConnectivityStatus]) -> Device:
        """Parse device data from API response."""
        metadata = data.get("metadata", {})
        product_data = data.get("product_data", {})

        device_id = data["id"]
        status = connectivity_map.get(device_id, ConnectivityStatus.UNKNOWN)

        return Device(
            id=device_id,
            name=metadata.get("name", "Unknown Device"),
            id_v1=data.get("id_v1"),
            model_id=product_data.get("model_id"),
            manufacturer=product_data.get("manufacturer_name"),
            product_name=product_data.get("product_name"),
            software_version=product_data.get("software_version"),
            service_ids=[
                ResourceReference(rid=s["rid"], rtype=s["rtype"])
                for s in data.get("services", [])
            ],
            connectivity_status=status,
        )

    def _parse_light(self, data: dict) -> Light:
        """Parse light data from API response."""
        metadata = data.get("metadata", {})
        dimming = data.get("dimming", {})
        color = data.get("color", {})
        color_temp = data.get("color_temperature", {})
        on_state = data.get("on", {})

        # Parse gamut
        gamut_type_str = color.get("gamut_type", "C")
        try:
            gamut_type = GamutType(gamut_type_str)
        except ValueError:
            gamut_type = GamutType.OTHER

        gamut = None
        gamut_data = color.get("gamut")
        if gamut_data:
            try:
                gamut = self._parse_gamut(gamut_data)
            except (KeyError, TypeError):
                pass

        # Parse current color
        color_xy = None
        xy_data = color.get("xy")
        if xy_data:
            color_xy = XYColor(x=xy_data.get("x", 0), y=xy_data.get("y", 0))

        owner = data.get("owner", {})

        return Light(
            id=data["id"],
            name=metadata.get("name", "Unknown Light"),
            id_v1=data.get("id_v1"),
            owner_id=owner.get("rid"),
            is_on=on_state.get("on", False),
            brightness=dimming.get("brightness", 100.0),
            supports_color=bool(color),
            supports_color_temperature=bool(color_temp),
            color_xy=color_xy,
            color_temperature_mirek=color_temp.get("mirek"),
            mirek_min=color_temp.get("mirek_schema", {}).get("mirek_minimum"),
            mirek_max=color_temp.get("mirek_schema", {}).get("mirek_maximum"),
            gamut_type=gamut_type,
            gamut=gamut,
        )

    def _parse_gamut(self, data: dict):
        """Parse gamut data."""
        from .models import Gamut

        return Gamut(
            red=XYColor(x=data["red"]["x"], y=data["red"]["y"]),
            green=XYColor(x=data["green"]["x"], y=data["green"]["y"]),
            blue=XYColor(x=data["blue"]["x"], y=data["blue"]["y"]),
        )

    def _parse_room(self, data: dict) -> Room:
        """Parse room data from API response."""
        metadata = data.get("metadata", {})

        children = [
            ResourceReference(rid=c["rid"], rtype=c["rtype"])
            for c in data.get("children", [])
        ]

        services = [
            ResourceReference(rid=s["rid"], rtype=s["rtype"])
            for s in data.get("services", [])
        ]

        # Find grouped_light service
        grouped_light_id = None
        for s in services:
            if s.rtype == "grouped_light":
                grouped_light_id = s.rid
                break

        return Room(
            id=data["id"],
            name=metadata.get("name", "Unknown Room"),
            id_v1=data.get("id_v1"),
            archetype=metadata.get("archetype"),
            children=children,
            services=services,
            grouped_light_id=grouped_light_id,
        )

    def _parse_zone(self, data: dict) -> Zone:
        """Parse zone data from API response."""
        metadata = data.get("metadata", {})

        children = [
            ResourceReference(rid=c["rid"], rtype=c["rtype"])
            for c in data.get("children", [])
        ]

        services = [
            ResourceReference(rid=s["rid"], rtype=s["rtype"])
            for s in data.get("services", [])
        ]

        # Find grouped_light service
        grouped_light_id = None
        for s in services:
            if s.rtype == "grouped_light":
                grouped_light_id = s.rid
                break

        return Zone(
            id=data["id"],
            name=metadata.get("name", "Unknown Zone"),
            id_v1=data.get("id_v1"),
            archetype=metadata.get("archetype"),
            children=children,
            services=services,
            grouped_light_id=grouped_light_id,
        )

    def _parse_grouped_light(self, data: dict) -> GroupedLight:
        """Parse grouped_light data from API response."""
        on_state = data.get("on", {})
        dimming = data.get("dimming", {})
        owner = data.get("owner", {})

        return GroupedLight(
            id=data["id"],
            id_v1=data.get("id_v1"),
            owner_id=owner.get("rid"),
            is_on=on_state.get("on", False),
            brightness=dimming.get("brightness", 100.0),
        )

    def _parse_scene(self, data: dict) -> Scene:
        """Parse scene data from API response."""
        metadata = data.get("metadata", {})
        group = data.get("group", {})

        return Scene(
            id=data["id"],
            name=metadata.get("name", "Unknown Scene"),
            id_v1=data.get("id_v1"),
            group_id=group.get("rid"),
            group_type=group.get("rtype"),
            speed=data.get("speed", 0.5),
            auto_dynamic=data.get("auto_dynamic", False),
        )

    def find_target(self, query: str) -> Optional[Target]:
        """
        Find a light, room, or zone by name using fuzzy matching.

        Args:
            query: Name to search for (e.g., "living room", "kitchen light")

        Returns:
            Light, Room, or Zone if found, None otherwise
        """
        normalized = self._normalize_name(query)

        # Exact match
        if normalized in self._name_index:
            resource_type, resource_id = self._name_index[normalized]
            return self._get_resource(resource_type, resource_id)

        # Substring match (query is contained in name)
        for name, (resource_type, resource_id) in self._name_index.items():
            if normalized in name:
                return self._get_resource(resource_type, resource_id)

        # Substring match (name is contained in query)
        for name, (resource_type, resource_id) in self._name_index.items():
            if name in normalized:
                return self._get_resource(resource_type, resource_id)

        return None

    def find_target_strict(self, query: str) -> Target:
        """
        Find a target or raise TargetNotFoundError.

        Args:
            query: Name to search for

        Returns:
            Light, Room, or Zone

        Raises:
            TargetNotFoundError: If target not found
        """
        target = self.find_target(query)
        if target is None:
            raise TargetNotFoundError(query)
        return target

    def _get_resource(self, resource_type: str, resource_id: str) -> Optional[Target]:
        """Get a resource by type and ID."""
        if resource_type == "light":
            return self.lights.get(resource_id)
        elif resource_type == "room":
            return self.rooms.get(resource_id)
        elif resource_type == "zone":
            return self.zones.get(resource_id)
        elif resource_type == "device":
            # For devices, try to return the primary light
            device = self.devices.get(resource_id)
            if device:
                light_ids = self._device_to_lights.get(resource_id, [])
                if light_ids:
                    return self.lights.get(light_ids[0])
        return None

    def find_scene(
        self,
        scene_name: str,
        group_name: Optional[str] = None
    ) -> Optional[Scene]:
        """
        Find a scene by name, optionally filtered by group.

        Args:
            scene_name: Scene name to search for
            group_name: Optional room/zone name to filter by

        Returns:
            Scene if found, None otherwise
        """
        normalized_scene = self._normalize_name(scene_name)

        # If group specified, find it first
        group_id = None
        if group_name:
            target = self.find_target(group_name)
            if target and isinstance(target, (Room, Zone)):
                group_id = target.id

        for scene in self.scenes.values():
            normalized = self._normalize_name(scene.name)
            if normalized_scene in normalized or normalized in normalized_scene:
                # If group filter specified, check it matches
                if group_id and scene.group_id != group_id:
                    continue
                return scene

        return None

    def find_scene_strict(
        self,
        scene_name: str,
        group_name: Optional[str] = None
    ) -> Scene:
        """
        Find a scene or raise SceneNotFoundError.

        Args:
            scene_name: Scene name to search for
            group_name: Optional room/zone name to filter by

        Returns:
            Scene

        Raises:
            SceneNotFoundError: If scene not found
        """
        scene = self.find_scene(scene_name, group_name)
        if scene is None:
            raise SceneNotFoundError(scene_name, group_name)
        return scene

    def get_lights_for_target(self, target: Target) -> list[Light]:
        """
        Get all lights associated with a target.

        Args:
            target: A Light, Room, or Zone

        Returns:
            List of Light objects
        """
        if isinstance(target, Light):
            return [target]

        elif isinstance(target, Room):
            # Room children are devices
            lights = []
            for child in target.children:
                if child.rtype == "device":
                    device_lights = self._device_to_lights.get(child.rid, [])
                    for light_id in device_lights:
                        if light_id in self.lights:
                            lights.append(self.lights[light_id])
            return lights

        elif isinstance(target, Zone):
            # Zone children are lights
            lights = []
            for child in target.children:
                if child.rtype == "light" and child.rid in self.lights:
                    lights.append(self.lights[child.rid])
            return lights

        return []

    def get_unreachable_lights(self, target: Target) -> list[Light]:
        """Get list of unreachable lights for a target."""
        lights = self.get_lights_for_target(target)
        return [l for l in lights if not l.is_reachable]

    def get_reachable_lights(self, target: Target) -> list[Light]:
        """Get list of reachable lights for a target."""
        lights = self.get_lights_for_target(target)
        return [l for l in lights if l.is_reachable]

    def get_scenes_for_group(self, group: Union[Room, Zone]) -> list[Scene]:
        """Get all scenes available for a room or zone."""
        return [
            scene for scene in self.scenes.values()
            if scene.group_id == group.id
        ]

    def list_all_targets(self) -> dict[str, list[str]]:
        """
        Get a summary of all available targets.

        Returns:
            Dict with keys 'lights', 'rooms', 'zones' containing name lists
        """
        return {
            "lights": [l.name for l in self.lights.values()],
            "rooms": [r.name for r in self.rooms.values()],
            "zones": [z.name for z in self.zones.values()],
            "scenes": [s.name for s in self.scenes.values()],
        }

    async def update_from_event(self, event: dict) -> None:
        """
        Update local state from an SSE event.

        Args:
            event: Event data from bridge
        """
        event_type = event.get("type")
        data_list = event.get("data", [])

        for item in data_list:
            item_type = item.get("type")
            item_id = item.get("id")

            if item_type == "light" and item_id in self.lights:
                light = self.lights[item_id]

                # Update on state
                if "on" in item:
                    light.is_on = item["on"].get("on", light.is_on)

                # Update brightness
                if "dimming" in item:
                    light.brightness = item["dimming"].get("brightness", light.brightness)

                # Update color
                if "color" in item and "xy" in item["color"]:
                    xy = item["color"]["xy"]
                    light.color_xy = XYColor(x=xy.get("x", 0), y=xy.get("y", 0))

                # Update color temperature
                if "color_temperature" in item:
                    light.color_temperature_mirek = item["color_temperature"].get("mirek")

            elif item_type == "zigbee_connectivity":
                # Update connectivity status
                status_str = item.get("status", "unknown")
                owner = item.get("owner", {})
                device_id = owner.get("rid")

                if device_id:
                    try:
                        status = ConnectivityStatus(status_str)
                    except ValueError:
                        status = ConnectivityStatus.UNKNOWN

                    # Update all lights owned by this device
                    light_ids = self._device_to_lights.get(device_id, [])
                    for light_id in light_ids:
                        if light_id in self.lights:
                            self.lights[light_id].connectivity_status = status

    async def start_event_listener(self) -> None:
        """Start background task to listen for SSE events."""
        if self._event_task is not None:
            return

        async def _listen():
            try:
                async for event in self.connector.subscribe_events():
                    await self.update_from_event(event)
            except Exception as e:
                logger.error(f"Event listener error: {e}")

        self._event_task = asyncio.create_task(_listen())

    async def stop_event_listener(self) -> None:
        """Stop the event listener task."""
        if self._event_task:
            self._event_task.cancel()
            try:
                await self._event_task
            except asyncio.CancelledError:
                pass
            self._event_task = None
