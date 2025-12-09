"""
Group Wizard

Interactive wizard for creating and managing rooms and zones.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .base_wizard import BaseWizard, WizardResult, WizardAction
from ..models import (
    Room,
    Zone,
    Device,
    Light,
    CreateRoomRequest,
    CreateZoneRequest,
    UpdateGroupRequest,
)
from ..constants import ROOM_ARCHETYPES, ROOM_ARCHETYPE_DESCRIPTIONS
from ..managers.group_manager import GroupManager

if TYPE_CHECKING:
    from ..device_manager import DeviceManager
    from ..bridge_connector import BridgeConnector


class GroupWizard(BaseWizard):
    """Interactive wizard for room and zone management."""

    def __init__(
        self,
        connector: BridgeConnector,
        device_manager: DeviceManager
    ):
        """
        Initialize the group wizard.

        Args:
            connector: Bridge connector for API calls
            device_manager: Device manager for state access
        """
        super().__init__(device_manager)
        self.connector = connector
        self.group_manager = GroupManager(connector, device_manager)

    async def run(self) -> WizardResult:
        """
        Run the group wizard main menu.

        Returns:
            WizardResult indicating success/failure
        """
        self.print_header("Group Wizard")

        options = [
            ("Create new room", "create_room"),
            ("Create new zone", "create_zone"),
            ("Edit room", "edit_room"),
            ("Edit zone", "edit_zone"),
            ("Delete room", "delete_room"),
            ("Delete zone", "delete_zone"),
            ("Show unassigned devices", "unassigned"),
        ]

        choice, action = self.select_one("What would you like to do?", options)

        if action == WizardAction.CANCEL:
            return self.handle_cancel("Group")

        if choice == "create_room":
            return await self._create_room_wizard()
        elif choice == "create_zone":
            return await self._create_zone_wizard()
        elif choice == "edit_room":
            return await self._edit_room_wizard()
        elif choice == "edit_zone":
            return await self._edit_zone_wizard()
        elif choice == "delete_room":
            return await self._delete_room_wizard()
        elif choice == "delete_zone":
            return await self._delete_zone_wizard()
        elif choice == "unassigned":
            return await self._show_unassigned()

        return WizardResult(success=False, message="Invalid choice")

    async def run_create_room(self) -> WizardResult:
        """Run the room creation wizard directly."""
        return await self._create_room_wizard()

    async def run_create_zone(self) -> WizardResult:
        """Run the zone creation wizard directly."""
        return await self._create_zone_wizard()

    # =========================================================================
    # Create Room Wizard
    # =========================================================================

    async def _create_room_wizard(self) -> WizardResult:
        """Create a new room."""
        self.print_header("Create New Room")

        # Step 1: Enter name
        self.print_step(1, 4, "Name your room")
        name, action = self.get_input(
            "Room name",
            validator=lambda x: len(x) >= 1 and len(x) <= 32,
            error_message="Name must be 1-32 characters"
        )
        if action != WizardAction.CONTINUE:
            return self.handle_cancel("Group")

        # Step 2: Select archetype
        self.print_step(2, 4, "Select room type")
        archetype, action = await self._select_archetype()
        if action != WizardAction.CONTINUE:
            return self.handle_cancel("Group")

        # Step 3: Select devices
        self.print_step(3, 4, "Add devices to room")
        devices, action = await self._select_devices_for_room()
        if action != WizardAction.CONTINUE:
            return self.handle_cancel("Group")

        # Step 4: Confirm
        self.print_step(4, 4, "Confirm and create")
        print(f"\nRoom: {name}")
        print(f"Type: {ROOM_ARCHETYPE_DESCRIPTIONS.get(archetype, archetype)}")
        print(f"Devices: {len(devices)}")
        if devices:
            for device in devices:
                print(f"  - {device.name}")

        confirmed, action = self.get_confirmation("Create this room?", default=True)
        if not confirmed or action != WizardAction.CONTINUE:
            return self.handle_cancel("Group")

        # Create the room
        try:
            request = CreateRoomRequest(
                name=name,
                archetype=archetype,
                children=[d.id for d in devices]
            )
            room = await self.group_manager.create_room(request)

            self.print_success(f"Created room '{name}'")
            return WizardResult(
                success=True,
                message=f"Created room '{name}'",
                data=room
            )

        except Exception as e:
            self.print_error(str(e))
            return WizardResult(success=False, message=str(e))

    # =========================================================================
    # Create Zone Wizard
    # =========================================================================

    async def _create_zone_wizard(self) -> WizardResult:
        """Create a new zone."""
        self.print_header("Create New Zone")

        # Step 1: Enter name
        self.print_step(1, 4, "Name your zone")
        name, action = self.get_input(
            "Zone name",
            validator=lambda x: len(x) >= 1 and len(x) <= 32,
            error_message="Name must be 1-32 characters"
        )
        if action != WizardAction.CONTINUE:
            return self.handle_cancel("Group")

        # Step 2: Select archetype
        self.print_step(2, 4, "Select zone type")
        archetype, action = await self._select_archetype()
        if action != WizardAction.CONTINUE:
            return self.handle_cancel("Group")

        # Step 3: Select lights
        self.print_step(3, 4, "Add lights to zone")
        print("\nZones can include lights from any room.")
        lights, action = await self._select_lights_for_zone()
        if action != WizardAction.CONTINUE:
            return self.handle_cancel("Group")

        # Step 4: Confirm
        self.print_step(4, 4, "Confirm and create")
        print(f"\nZone: {name}")
        print(f"Type: {ROOM_ARCHETYPE_DESCRIPTIONS.get(archetype, archetype)}")
        print(f"Lights: {len(lights)}")
        if lights:
            for light in lights:
                print(f"  - {light.name}")

        confirmed, action = self.get_confirmation("Create this zone?", default=True)
        if not confirmed or action != WizardAction.CONTINUE:
            return self.handle_cancel("Group")

        # Create the zone
        try:
            request = CreateZoneRequest(
                name=name,
                archetype=archetype,
                children=[l.id for l in lights]
            )
            zone = await self.group_manager.create_zone(request)

            self.print_success(f"Created zone '{name}'")
            return WizardResult(
                success=True,
                message=f"Created zone '{name}'",
                data=zone
            )

        except Exception as e:
            self.print_error(str(e))
            return WizardResult(success=False, message=str(e))

    # =========================================================================
    # Edit Room Wizard
    # =========================================================================

    async def _edit_room_wizard(
        self,
        room_id: Optional[str] = None
    ) -> WizardResult:
        """Edit an existing room."""
        self.print_header("Edit Room")

        # Select room if not provided
        if room_id is None:
            room, action = await self._select_room()
            if action != WizardAction.CONTINUE or room is None:
                return self.handle_cancel("Group")
        else:
            room = self.dm.rooms.get(room_id)
            if not room:
                self.print_error("Room not found")
                return WizardResult(success=False, message="Room not found")

        # Show edit menu
        while True:
            lights = self.dm.get_lights_for_target(room)
            print(f"\nEditing: {room.name}")
            print(f"Type: {ROOM_ARCHETYPE_DESCRIPTIONS.get(room.archetype or '', room.archetype or 'Unknown')}")
            print(f"Devices: {len(room.device_ids)}")
            print(f"Lights: {len(lights)}")

            options = [
                ("Add devices", "add"),
                ("Remove devices", "remove"),
                ("Rename room", "rename"),
                ("Change type", "archetype"),
                ("Done", "done"),
            ]

            choice, action = self.select_one("What would you like to do?", options)

            if action == WizardAction.CANCEL:
                return self.handle_cancel("Group")

            if choice == "add":
                await self._add_devices_to_room(room)
            elif choice == "remove":
                await self._remove_devices_from_room(room)
            elif choice == "rename":
                new_name, action = self.get_input("New name")
                if action == WizardAction.CONTINUE:
                    try:
                        room = await self.group_manager.rename_room(room.id, new_name)
                        self.print_success(f"Renamed to '{new_name}'")
                    except Exception as e:
                        self.print_error(str(e))
            elif choice == "archetype":
                archetype, action = await self._select_archetype()
                if action == WizardAction.CONTINUE:
                    try:
                        room = await self.group_manager.update_room(UpdateGroupRequest(
                            group_id=room.id,
                            archetype=archetype
                        ))
                        self.print_success("Updated room type")
                    except Exception as e:
                        self.print_error(str(e))
            elif choice == "done":
                break

            # Refresh room data
            room = self.dm.rooms.get(room.id) or room

        return WizardResult(
            success=True,
            message=f"Finished editing '{room.name}'",
            data=room
        )

    # =========================================================================
    # Edit Zone Wizard
    # =========================================================================

    async def _edit_zone_wizard(
        self,
        zone_id: Optional[str] = None
    ) -> WizardResult:
        """Edit an existing zone."""
        self.print_header("Edit Zone")

        # Select zone if not provided
        if zone_id is None:
            zone, action = await self._select_zone()
            if action != WizardAction.CONTINUE or zone is None:
                return self.handle_cancel("Group")
        else:
            zone = self.dm.zones.get(zone_id)
            if not zone:
                self.print_error("Zone not found")
                return WizardResult(success=False, message="Zone not found")

        # Show edit menu
        while True:
            lights = self.dm.get_lights_for_target(zone)
            print(f"\nEditing: {zone.name}")
            print(f"Type: {ROOM_ARCHETYPE_DESCRIPTIONS.get(zone.archetype or '', zone.archetype or 'Unknown')}")
            print(f"Lights: {len(lights)}")

            options = [
                ("Add lights", "add"),
                ("Remove lights", "remove"),
                ("Rename zone", "rename"),
                ("Change type", "archetype"),
                ("Done", "done"),
            ]

            choice, action = self.select_one("What would you like to do?", options)

            if action == WizardAction.CANCEL:
                return self.handle_cancel("Group")

            if choice == "add":
                await self._add_lights_to_zone(zone)
            elif choice == "remove":
                await self._remove_lights_from_zone(zone)
            elif choice == "rename":
                new_name, action = self.get_input("New name")
                if action == WizardAction.CONTINUE:
                    try:
                        zone = await self.group_manager.rename_zone(zone.id, new_name)
                        self.print_success(f"Renamed to '{new_name}'")
                    except Exception as e:
                        self.print_error(str(e))
            elif choice == "archetype":
                archetype, action = await self._select_archetype()
                if action == WizardAction.CONTINUE:
                    try:
                        zone = await self.group_manager.update_zone(UpdateGroupRequest(
                            group_id=zone.id,
                            archetype=archetype
                        ))
                        self.print_success("Updated zone type")
                    except Exception as e:
                        self.print_error(str(e))
            elif choice == "done":
                break

            # Refresh zone data
            zone = self.dm.zones.get(zone.id) or zone

        return WizardResult(
            success=True,
            message=f"Finished editing '{zone.name}'",
            data=zone
        )

    # =========================================================================
    # Delete Wizards
    # =========================================================================

    async def _delete_room_wizard(self) -> WizardResult:
        """Delete a room."""
        self.print_header("Delete Room")

        room, action = await self._select_room()
        if action != WizardAction.CONTINUE or room is None:
            return self.handle_cancel("Group")

        lights = self.dm.get_lights_for_target(room)
        print(f"\nRoom: {room.name}")
        print(f"Lights: {len(lights)}")
        print("\nNote: Deleting the room will unassign all devices.")

        confirmed, action = self.get_confirmation(
            f"Delete room '{room.name}'?",
            default=False
        )
        if not confirmed or action != WizardAction.CONTINUE:
            return self.handle_cancel("Group")

        try:
            await self.group_manager.delete_room(room.id)
            self.print_success(f"Deleted room '{room.name}'")
            return WizardResult(
                success=True,
                message=f"Deleted room '{room.name}'"
            )

        except Exception as e:
            self.print_error(str(e))
            return WizardResult(success=False, message=str(e))

    async def _delete_zone_wizard(self) -> WizardResult:
        """Delete a zone."""
        self.print_header("Delete Zone")

        zone, action = await self._select_zone()
        if action != WizardAction.CONTINUE or zone is None:
            return self.handle_cancel("Group")

        confirmed, action = self.get_confirmation(
            f"Delete zone '{zone.name}'?",
            default=False
        )
        if not confirmed or action != WizardAction.CONTINUE:
            return self.handle_cancel("Group")

        try:
            await self.group_manager.delete_zone(zone.id)
            self.print_success(f"Deleted zone '{zone.name}'")
            return WizardResult(
                success=True,
                message=f"Deleted zone '{zone.name}'"
            )

        except Exception as e:
            self.print_error(str(e))
            return WizardResult(success=False, message=str(e))

    # =========================================================================
    # Show Unassigned Devices
    # =========================================================================

    async def _show_unassigned(self) -> WizardResult:
        """Show devices not assigned to any room."""
        self.print_header("Unassigned Devices")

        devices = await self.group_manager.get_unassigned_devices()

        if not devices:
            print("All devices are assigned to rooms.")
            return WizardResult(
                success=True,
                message="No unassigned devices"
            )

        print(f"Found {len(devices)} unassigned device(s):\n")
        for device in devices:
            print(f"  - {device.name}")
            if device.product_name:
                print(f"    Product: {device.product_name}")

        # Offer to assign them
        assign, action = self.get_confirmation(
            "\nWould you like to assign a device to a room?",
            default=False
        )

        if assign and action == WizardAction.CONTINUE:
            # Select device
            options = [(d.name, d) for d in devices]
            device, action = self.select_one("Select device", options)

            if action == WizardAction.CONTINUE and device:
                # Select room
                room, action = await self._select_room()
                if action == WizardAction.CONTINUE and room:
                    try:
                        await self.group_manager.add_devices_to_room(
                            room.id, [device.id]
                        )
                        self.print_success(f"Added '{device.name}' to '{room.name}'")
                    except Exception as e:
                        self.print_error(str(e))

        return WizardResult(
            success=True,
            message=f"Found {len(devices)} unassigned device(s)",
            data=devices
        )

    # =========================================================================
    # Helper Methods
    # =========================================================================

    async def _select_archetype(self) -> tuple[Optional[str], WizardAction]:
        """Let user select a room archetype."""
        # Group archetypes into categories for easier selection
        common = ["living_room", "bedroom", "kitchen", "bathroom", "office", "hallway"]
        outdoor = ["garden", "terrace", "balcony", "porch", "garage", "driveway"]

        print("\nCommon room types:")
        options = []
        for arch in common:
            desc = ROOM_ARCHETYPE_DESCRIPTIONS.get(arch, arch)
            options.append((desc, arch))

        print("\nOr enter a number for other types...")

        # Add "more options" choice
        options.append(("-- More options --", "_more"))

        choice, action = self.select_one("Select room type", options)

        if action != WizardAction.CONTINUE:
            return None, action

        if choice == "_more":
            # Show all options
            all_options = [
                (ROOM_ARCHETYPE_DESCRIPTIONS.get(arch, arch), arch)
                for arch in ROOM_ARCHETYPES
            ]
            return self.select_one("Select room type", all_options)

        return choice, WizardAction.CONTINUE

    async def _select_room(self) -> tuple[Optional[Room], WizardAction]:
        """Let user select a room."""
        rooms = list(self.dm.rooms.values())

        if not rooms:
            self.print_error("No rooms found")
            return None, WizardAction.CANCEL

        options = []
        for room in sorted(rooms, key=lambda r: r.name):
            light_count = len(self.dm.get_lights_for_target(room))
            options.append((f"{room.name} ({light_count} lights)", room))

        return self.select_one("Select a room", options)

    async def _select_zone(self) -> tuple[Optional[Zone], WizardAction]:
        """Let user select a zone."""
        zones = list(self.dm.zones.values())

        if not zones:
            self.print_error("No zones found")
            return None, WizardAction.CANCEL

        options = []
        for zone in sorted(zones, key=lambda z: z.name):
            light_count = len(self.dm.get_lights_for_target(zone))
            options.append((f"{zone.name} ({light_count} lights)", zone))

        return self.select_one("Select a zone", options)

    async def _select_devices_for_room(
        self
    ) -> tuple[list[Device], WizardAction]:
        """Let user select devices for a new room."""
        # Get unassigned devices
        unassigned = await self.group_manager.get_unassigned_devices()

        if not unassigned:
            print("No unassigned devices available.")
            print("Devices can only belong to one room.")
            return [], WizardAction.CONTINUE

        options = [(d.name, d) for d in unassigned]
        return self.select_multiple(
            "Select devices to add (comma-separated numbers)",
            options,
            min_selections=0
        )

    async def _select_lights_for_zone(self) -> tuple[list[Light], WizardAction]:
        """Let user select lights for a zone."""
        # Group lights by room for easier selection
        lights_by_room: dict[str, list[Light]] = {}

        for room in self.dm.rooms.values():
            lights = self.dm.get_lights_for_target(room)
            if lights:
                lights_by_room[room.name] = lights

        if not lights_by_room:
            self.print_error("No lights found")
            return [], WizardAction.CANCEL

        # Build flat list with room prefixes
        options = []
        for room_name in sorted(lights_by_room.keys()):
            for light in sorted(lights_by_room[room_name], key=lambda l: l.name):
                options.append((f"{light.name} ({room_name})", light))

        return self.select_multiple(
            "Select lights to add (comma-separated numbers)",
            options,
            min_selections=1
        )

    async def _add_devices_to_room(self, room: Room) -> None:
        """Add devices to an existing room."""
        unassigned = await self.group_manager.get_unassigned_devices()

        if not unassigned:
            print("\nNo unassigned devices available.")
            return

        options = [(d.name, d) for d in unassigned]
        devices, action = self.select_multiple(
            "Select devices to add",
            options,
            min_selections=1
        )

        if action == WizardAction.CONTINUE and devices:
            try:
                await self.group_manager.add_devices_to_room(
                    room.id, [d.id for d in devices]
                )
                self.print_success(f"Added {len(devices)} device(s)")
            except Exception as e:
                self.print_error(str(e))

    async def _remove_devices_from_room(self, room: Room) -> None:
        """Remove devices from a room."""
        device_ids = room.device_ids
        devices = [self.dm.devices[did] for did in device_ids if did in self.dm.devices]

        if not devices:
            print("\nNo devices in this room.")
            return

        options = [(d.name, d) for d in devices]
        to_remove, action = self.select_multiple(
            "Select devices to remove",
            options,
            min_selections=1
        )

        if action == WizardAction.CONTINUE and to_remove:
            try:
                await self.group_manager.remove_devices_from_room(
                    room.id, [d.id for d in to_remove]
                )
                self.print_success(f"Removed {len(to_remove)} device(s)")
            except Exception as e:
                self.print_error(str(e))

    async def _add_lights_to_zone(self, zone: Zone) -> None:
        """Add lights to a zone."""
        # Get lights not already in this zone
        current_light_ids = set(zone.light_ids)
        available = [
            l for l in self.dm.lights.values()
            if l.id not in current_light_ids
        ]

        if not available:
            print("\nAll lights are already in this zone.")
            return

        options = [(l.name, l) for l in sorted(available, key=lambda l: l.name)]
        lights, action = self.select_multiple(
            "Select lights to add",
            options,
            min_selections=1
        )

        if action == WizardAction.CONTINUE and lights:
            try:
                await self.group_manager.add_lights_to_zone(
                    zone.id, [l.id for l in lights]
                )
                self.print_success(f"Added {len(lights)} light(s)")
            except Exception as e:
                self.print_error(str(e))

    async def _remove_lights_from_zone(self, zone: Zone) -> None:
        """Remove lights from a zone."""
        lights = self.dm.get_lights_for_target(zone)

        if not lights:
            print("\nNo lights in this zone.")
            return

        options = [(l.name, l) for l in lights]
        to_remove, action = self.select_multiple(
            "Select lights to remove",
            options,
            min_selections=1
        )

        if action == WizardAction.CONTINUE and to_remove:
            try:
                await self.group_manager.remove_lights_from_zone(
                    zone.id, [l.id for l in to_remove]
                )
                self.print_success(f"Removed {len(to_remove)} light(s)")
            except Exception as e:
                self.print_error(str(e))
