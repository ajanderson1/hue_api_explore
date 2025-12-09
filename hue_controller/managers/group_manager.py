"""
Group Manager

Handles room and zone CRUD operations for Hue API v2.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional, Union

from ..models import (
    Room,
    Zone,
    Device,
    Light,
    CreateRoomRequest,
    CreateZoneRequest,
    UpdateGroupRequest,
    ResourceReference,
    CommandResult,
)
from ..constants import ROOM_ARCHETYPES
from ..exceptions import (
    GroupCreationError,
    GroupUpdateError,
    InvalidArchetypeError,
    TargetNotFoundError,
    APIError,
)

if TYPE_CHECKING:
    from ..bridge_connector import BridgeConnector
    from ..device_manager import DeviceManager

logger = logging.getLogger(__name__)


class GroupManager:
    """Manages room and zone CRUD operations."""

    def __init__(self, connector: BridgeConnector, device_manager: DeviceManager):
        """
        Initialize the group manager.

        Args:
            connector: Bridge connector for API calls
            device_manager: Device manager for state access
        """
        self.connector = connector
        self.dm = device_manager

    # =========================================================================
    # Room Operations
    # =========================================================================

    async def create_room(self, request: CreateRoomRequest) -> Room:
        """
        Create a new room with specified devices.

        Args:
            request: Room creation request

        Returns:
            Created Room object

        Raises:
            GroupCreationError: On creation failure
            InvalidArchetypeError: If archetype is invalid
        """
        # Validate archetype
        if request.archetype not in ROOM_ARCHETYPES:
            raise InvalidArchetypeError(request.archetype, ROOM_ARCHETYPES)

        try:
            response = await self.connector.post(
                "/resource/room",
                request.to_dict()
            )

            data = response.get("data", [])
            if not data:
                raise GroupCreationError(
                    request.name,
                    "room",
                    "No room data returned"
                )

            room_id = data[0].get("rid")
            logger.info(f"Created room '{request.name}' with ID {room_id}")

            # Refresh state and return the new room
            await self.dm.sync_state()
            return self.dm.rooms.get(room_id) or Room(
                id=room_id,
                name=request.name,
                archetype=request.archetype
            )

        except APIError as e:
            raise GroupCreationError(request.name, "room", str(e))

    async def update_room(self, request: UpdateGroupRequest) -> Room:
        """
        Update room name, archetype, or membership.

        Args:
            request: Room update request

        Returns:
            Updated Room object

        Raises:
            GroupUpdateError: On update failure
        """
        if request.archetype and request.archetype not in ROOM_ARCHETYPES:
            raise InvalidArchetypeError(request.archetype, ROOM_ARCHETYPES)

        try:
            payload = request.to_dict(is_room=True)
            if payload:
                await self.connector.put(
                    f"/resource/room/{request.group_id}",
                    payload
                )
                logger.info(f"Updated room {request.group_id}")

            # Handle children updates separately
            if request.children_to_add:
                await self._add_devices_to_room(request.group_id, request.children_to_add)
            if request.children_to_remove:
                await self._remove_devices_from_room(request.group_id, request.children_to_remove)

            # Refresh and return updated room
            await self.dm.sync_state()
            room = self.dm.rooms.get(request.group_id)
            if not room:
                raise TargetNotFoundError(request.group_id, "room")
            return room

        except APIError as e:
            raise GroupUpdateError(request.group_id, "room", str(e))

    async def delete_room(self, room_id: str) -> None:
        """
        Delete a room. Lights become unassigned.

        Args:
            room_id: Room ID to delete

        Raises:
            TargetNotFoundError: If room doesn't exist
        """
        try:
            await self.connector.delete(f"/resource/room/{room_id}")
            logger.info(f"Deleted room {room_id}")

            # Remove from local cache
            if room_id in self.dm.rooms:
                del self.dm.rooms[room_id]

        except APIError as e:
            if e.status_code == 404:
                raise TargetNotFoundError(room_id, "room")
            raise

    async def add_devices_to_room(
        self,
        room_id: str,
        device_ids: list[str]
    ) -> Room:
        """
        Add devices to an existing room.

        Args:
            room_id: Room ID
            device_ids: List of device IDs to add

        Returns:
            Updated Room object
        """
        await self._add_devices_to_room(room_id, device_ids)
        await self.dm.sync_state()
        room = self.dm.rooms.get(room_id)
        if not room:
            raise TargetNotFoundError(room_id, "room")
        return room

    async def remove_devices_from_room(
        self,
        room_id: str,
        device_ids: list[str]
    ) -> Room:
        """
        Remove devices from a room.

        Args:
            room_id: Room ID
            device_ids: List of device IDs to remove

        Returns:
            Updated Room object
        """
        await self._remove_devices_from_room(room_id, device_ids)
        await self.dm.sync_state()
        room = self.dm.rooms.get(room_id)
        if not room:
            raise TargetNotFoundError(room_id, "room")
        return room

    async def _add_devices_to_room(
        self,
        room_id: str,
        device_ids: list[str]
    ) -> None:
        """Internal method to add devices to a room."""
        room = self.dm.rooms.get(room_id)
        if not room:
            raise TargetNotFoundError(room_id, "room")

        # Build new children list
        existing_ids = {ref.rid for ref in room.children}
        new_children = list(room.children)

        for device_id in device_ids:
            if device_id not in existing_ids:
                new_children.append(ResourceReference(rid=device_id, rtype="device"))

        # Update the room
        await self.connector.put(
            f"/resource/room/{room_id}",
            {"children": [{"rid": ref.rid, "rtype": ref.rtype} for ref in new_children]}
        )

    async def _remove_devices_from_room(
        self,
        room_id: str,
        device_ids: list[str]
    ) -> None:
        """Internal method to remove devices from a room."""
        room = self.dm.rooms.get(room_id)
        if not room:
            raise TargetNotFoundError(room_id, "room")

        # Build new children list without the removed devices
        remove_set = set(device_ids)
        new_children = [ref for ref in room.children if ref.rid not in remove_set]

        # Update the room
        await self.connector.put(
            f"/resource/room/{room_id}",
            {"children": [{"rid": ref.rid, "rtype": ref.rtype} for ref in new_children]}
        )

    async def rename_room(self, room_id: str, new_name: str) -> Room:
        """
        Rename a room.

        Args:
            room_id: Room ID
            new_name: New room name

        Returns:
            Updated Room object
        """
        return await self.update_room(UpdateGroupRequest(
            group_id=room_id,
            name=new_name
        ))

    # =========================================================================
    # Zone Operations
    # =========================================================================

    async def create_zone(self, request: CreateZoneRequest) -> Zone:
        """
        Create a new zone with specified lights.

        Args:
            request: Zone creation request

        Returns:
            Created Zone object

        Raises:
            GroupCreationError: On creation failure
        """
        if request.archetype not in ROOM_ARCHETYPES:
            raise InvalidArchetypeError(request.archetype, ROOM_ARCHETYPES)

        try:
            response = await self.connector.post(
                "/resource/zone",
                request.to_dict()
            )

            data = response.get("data", [])
            if not data:
                raise GroupCreationError(
                    request.name,
                    "zone",
                    "No zone data returned"
                )

            zone_id = data[0].get("rid")
            logger.info(f"Created zone '{request.name}' with ID {zone_id}")

            # Refresh state and return the new zone
            await self.dm.sync_state()
            return self.dm.zones.get(zone_id) or Zone(
                id=zone_id,
                name=request.name,
                archetype=request.archetype
            )

        except APIError as e:
            raise GroupCreationError(request.name, "zone", str(e))

    async def update_zone(self, request: UpdateGroupRequest) -> Zone:
        """
        Update zone name, archetype, or membership.

        Args:
            request: Zone update request

        Returns:
            Updated Zone object
        """
        if request.archetype and request.archetype not in ROOM_ARCHETYPES:
            raise InvalidArchetypeError(request.archetype, ROOM_ARCHETYPES)

        try:
            payload = request.to_dict(is_room=False)
            if payload:
                await self.connector.put(
                    f"/resource/zone/{request.group_id}",
                    payload
                )
                logger.info(f"Updated zone {request.group_id}")

            # Handle children updates separately
            if request.children_to_add:
                await self._add_lights_to_zone(request.group_id, request.children_to_add)
            if request.children_to_remove:
                await self._remove_lights_from_zone(request.group_id, request.children_to_remove)

            # Refresh and return updated zone
            await self.dm.sync_state()
            zone = self.dm.zones.get(request.group_id)
            if not zone:
                raise TargetNotFoundError(request.group_id, "zone")
            return zone

        except APIError as e:
            raise GroupUpdateError(request.group_id, "zone", str(e))

    async def delete_zone(self, zone_id: str) -> None:
        """
        Delete a zone.

        Args:
            zone_id: Zone ID to delete

        Raises:
            TargetNotFoundError: If zone doesn't exist
        """
        try:
            await self.connector.delete(f"/resource/zone/{zone_id}")
            logger.info(f"Deleted zone {zone_id}")

            # Remove from local cache
            if zone_id in self.dm.zones:
                del self.dm.zones[zone_id]

        except APIError as e:
            if e.status_code == 404:
                raise TargetNotFoundError(zone_id, "zone")
            raise

    async def add_lights_to_zone(
        self,
        zone_id: str,
        light_ids: list[str]
    ) -> Zone:
        """
        Add lights to an existing zone.

        Args:
            zone_id: Zone ID
            light_ids: List of light IDs to add

        Returns:
            Updated Zone object
        """
        await self._add_lights_to_zone(zone_id, light_ids)
        await self.dm.sync_state()
        zone = self.dm.zones.get(zone_id)
        if not zone:
            raise TargetNotFoundError(zone_id, "zone")
        return zone

    async def remove_lights_from_zone(
        self,
        zone_id: str,
        light_ids: list[str]
    ) -> Zone:
        """
        Remove lights from a zone.

        Args:
            zone_id: Zone ID
            light_ids: List of light IDs to remove

        Returns:
            Updated Zone object
        """
        await self._remove_lights_from_zone(zone_id, light_ids)
        await self.dm.sync_state()
        zone = self.dm.zones.get(zone_id)
        if not zone:
            raise TargetNotFoundError(zone_id, "zone")
        return zone

    async def _add_lights_to_zone(
        self,
        zone_id: str,
        light_ids: list[str]
    ) -> None:
        """Internal method to add lights to a zone."""
        zone = self.dm.zones.get(zone_id)
        if not zone:
            raise TargetNotFoundError(zone_id, "zone")

        # Build new children list
        existing_ids = {ref.rid for ref in zone.children}
        new_children = list(zone.children)

        for light_id in light_ids:
            if light_id not in existing_ids:
                new_children.append(ResourceReference(rid=light_id, rtype="light"))

        # Update the zone
        await self.connector.put(
            f"/resource/zone/{zone_id}",
            {"children": [{"rid": ref.rid, "rtype": ref.rtype} for ref in new_children]}
        )

    async def _remove_lights_from_zone(
        self,
        zone_id: str,
        light_ids: list[str]
    ) -> None:
        """Internal method to remove lights from a zone."""
        zone = self.dm.zones.get(zone_id)
        if not zone:
            raise TargetNotFoundError(zone_id, "zone")

        # Build new children list without the removed lights
        remove_set = set(light_ids)
        new_children = [ref for ref in zone.children if ref.rid not in remove_set]

        # Update the zone
        await self.connector.put(
            f"/resource/zone/{zone_id}",
            {"children": [{"rid": ref.rid, "rtype": ref.rtype} for ref in new_children]}
        )

    async def rename_zone(self, zone_id: str, new_name: str) -> Zone:
        """
        Rename a zone.

        Args:
            zone_id: Zone ID
            new_name: New zone name

        Returns:
            Updated Zone object
        """
        return await self.update_zone(UpdateGroupRequest(
            group_id=zone_id,
            name=new_name
        ))

    # =========================================================================
    # Query Operations
    # =========================================================================

    async def get_unassigned_devices(self) -> list[Device]:
        """
        Get devices not assigned to any room.

        Returns:
            List of unassigned Device objects
        """
        # Collect all device IDs that are in rooms
        assigned_device_ids: set[str] = set()
        for room in self.dm.rooms.values():
            assigned_device_ids.update(room.device_ids)

        # Find devices not in any room
        unassigned = []
        for device in self.dm.devices.values():
            if device.id not in assigned_device_ids:
                unassigned.append(device)

        return sorted(unassigned, key=lambda d: d.name)

    async def get_unassigned_lights(self) -> list[Light]:
        """
        Get lights whose devices are not assigned to any room.

        Returns:
            List of unassigned Light objects
        """
        unassigned_devices = await self.get_unassigned_devices()
        unassigned_device_ids = {d.id for d in unassigned_devices}

        # Find lights owned by unassigned devices
        unassigned_lights = []
        for light in self.dm.lights.values():
            if light.owner_id in unassigned_device_ids:
                unassigned_lights.append(light)

        return sorted(unassigned_lights, key=lambda l: l.name)

    def get_room_archetypes(self) -> list[str]:
        """
        Get list of valid room archetypes.

        Returns:
            List of archetype strings
        """
        return ROOM_ARCHETYPES.copy()

    async def move_device_to_room(
        self,
        device_id: str,
        target_room_id: str
    ) -> CommandResult:
        """
        Move a device from its current room to another room.

        Args:
            device_id: Device ID to move
            target_room_id: Destination room ID

        Returns:
            CommandResult indicating success/failure
        """
        # Find current room
        current_room_id: Optional[str] = None
        for room in self.dm.rooms.values():
            if device_id in room.device_ids:
                current_room_id = room.id
                break

        try:
            # Remove from current room if assigned
            if current_room_id:
                await self._remove_devices_from_room(current_room_id, [device_id])

            # Add to target room
            await self._add_devices_to_room(target_room_id, [device_id])

            await self.dm.sync_state()

            device = self.dm.devices.get(device_id)
            target_room = self.dm.rooms.get(target_room_id)

            return CommandResult(
                success=True,
                message=f"Moved '{device.name if device else device_id}' to '{target_room.name if target_room else target_room_id}'"
            )

        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Failed to move device: {e}",
                errors=[str(e)]
            )
