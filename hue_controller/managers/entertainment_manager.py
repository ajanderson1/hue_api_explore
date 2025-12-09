"""
Entertainment Manager

Handles entertainment configuration operations for Hue API v2.
Entertainment configurations enable streaming for synchronized lighting
with games, movies, and music.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from ..models import (
    EntertainmentConfiguration,
    EntertainmentChannel,
    EntertainmentLocation,
    CreateEntertainmentRequest,
    CommandResult,
)
from ..constants import ENTERTAINMENT_TYPES
from ..exceptions import (
    EntertainmentError,
    EntertainmentCreationError,
    EntertainmentActivationError,
    TargetNotFoundError,
    APIError,
)

if TYPE_CHECKING:
    from ..bridge_connector import BridgeConnector
    from ..device_manager import DeviceManager

logger = logging.getLogger(__name__)


class EntertainmentManager:
    """Manages entertainment configurations for streaming."""

    def __init__(self, connector: BridgeConnector, device_manager: DeviceManager):
        """
        Initialize the entertainment manager.

        Args:
            connector: Bridge connector for API calls
            device_manager: Device manager for state access
        """
        self.connector = connector
        self.dm = device_manager
        self._configurations: dict[str, EntertainmentConfiguration] = {}

    # =========================================================================
    # Read Operations
    # =========================================================================

    async def list_configurations(self) -> list[EntertainmentConfiguration]:
        """
        List all entertainment configurations.

        Returns:
            List of EntertainmentConfiguration objects
        """
        await self._sync_configurations()
        return sorted(self._configurations.values(), key=lambda c: c.name)

    async def get_configuration(
        self,
        config_id: str
    ) -> EntertainmentConfiguration:
        """
        Get a specific entertainment configuration.

        Args:
            config_id: Configuration ID

        Returns:
            EntertainmentConfiguration object

        Raises:
            TargetNotFoundError: If configuration doesn't exist
        """
        await self._sync_configurations()
        if config_id not in self._configurations:
            raise TargetNotFoundError(config_id, "entertainment configuration")
        return self._configurations[config_id]

    async def _sync_configurations(self) -> None:
        """Sync entertainment configurations from bridge."""
        try:
            response = await self.connector.get("/resource/entertainment_configuration")
            self._configurations.clear()

            for data in response.get("data", []):
                config = self._parse_configuration(data)
                self._configurations[config.id] = config

        except APIError as e:
            logger.error(f"Failed to sync entertainment configurations: {e}")

    # =========================================================================
    # Create Operations
    # =========================================================================

    async def create_configuration(
        self,
        name: str,
        config_type: str,
        light_ids: list[str],
        locations: Optional[list[EntertainmentLocation]] = None
    ) -> EntertainmentConfiguration:
        """
        Create a new entertainment configuration.

        Args:
            name: Configuration name
            config_type: Configuration type (screen, monitor, music, 3dspace, other)
            light_ids: List of light service IDs to include
            locations: Optional light positions

        Returns:
            Created EntertainmentConfiguration object

        Raises:
            EntertainmentCreationError: On creation failure
        """
        if config_type not in ENTERTAINMENT_TYPES:
            raise EntertainmentCreationError(
                name,
                f"Invalid type. Valid types: {', '.join(ENTERTAINMENT_TYPES)}"
            )

        request = CreateEntertainmentRequest(
            name=name,
            configuration_type=config_type,
            light_services=light_ids,
            locations=locations or []
        )

        try:
            response = await self.connector.post(
                "/resource/entertainment_configuration",
                request.to_dict()
            )

            data = response.get("data", [])
            if not data:
                raise EntertainmentCreationError(name, "No configuration data returned")

            config_id = data[0].get("rid")
            logger.info(f"Created entertainment configuration '{name}' with ID {config_id}")

            # Fetch and return the created configuration
            await self._sync_configurations()
            return self._configurations.get(config_id) or EntertainmentConfiguration(
                id=config_id,
                name=name,
                configuration_type=config_type,
                light_services=light_ids
            )

        except APIError as e:
            raise EntertainmentCreationError(name, str(e))

    # =========================================================================
    # Update Operations
    # =========================================================================

    async def update_configuration(
        self,
        config_id: str,
        name: Optional[str] = None,
        light_ids: Optional[list[str]] = None
    ) -> EntertainmentConfiguration:
        """
        Update an entertainment configuration.

        Args:
            config_id: Configuration ID
            name: Optional new name
            light_ids: Optional new list of light service IDs

        Returns:
            Updated EntertainmentConfiguration object
        """
        payload: dict = {}

        if name is not None:
            payload["metadata"] = {"name": name}

        if light_ids is not None:
            payload["light_services"] = [
                {"rid": lid, "rtype": "light"} for lid in light_ids
            ]

        if payload:
            try:
                await self.connector.put(
                    f"/resource/entertainment_configuration/{config_id}",
                    payload
                )
                logger.info(f"Updated entertainment configuration {config_id}")
            except APIError as e:
                raise EntertainmentError(f"Failed to update configuration: {e}")

        await self._sync_configurations()
        return await self.get_configuration(config_id)

    async def set_light_positions(
        self,
        config_id: str,
        positions: dict[str, tuple[float, float, float]]
    ) -> EntertainmentConfiguration:
        """
        Set light positions in the entertainment space.

        Args:
            config_id: Configuration ID
            positions: Dict mapping light service IDs to (x, y, z) positions

        Returns:
            Updated EntertainmentConfiguration object
        """
        locations = [
            {
                "service": {"rid": light_id, "rtype": "entertainment"},
                "position": {"x": pos[0], "y": pos[1], "z": pos[2]}
            }
            for light_id, pos in positions.items()
        ]

        try:
            await self.connector.put(
                f"/resource/entertainment_configuration/{config_id}",
                {"locations": {"service_locations": locations}}
            )
            logger.info(f"Updated light positions for configuration {config_id}")
        except APIError as e:
            raise EntertainmentError(f"Failed to set light positions: {e}")

        await self._sync_configurations()
        return await self.get_configuration(config_id)

    async def rename_configuration(
        self,
        config_id: str,
        new_name: str
    ) -> EntertainmentConfiguration:
        """
        Rename an entertainment configuration.

        Args:
            config_id: Configuration ID
            new_name: New configuration name

        Returns:
            Updated EntertainmentConfiguration object
        """
        return await self.update_configuration(config_id, name=new_name)

    # =========================================================================
    # Delete Operations
    # =========================================================================

    async def delete_configuration(self, config_id: str) -> None:
        """
        Delete an entertainment configuration.

        Args:
            config_id: Configuration ID to delete

        Raises:
            TargetNotFoundError: If configuration doesn't exist
        """
        try:
            await self.connector.delete(
                f"/resource/entertainment_configuration/{config_id}"
            )
            logger.info(f"Deleted entertainment configuration {config_id}")

            # Remove from local cache
            if config_id in self._configurations:
                del self._configurations[config_id]

        except APIError as e:
            if e.status_code == 404:
                raise TargetNotFoundError(config_id, "entertainment configuration")
            raise

    # =========================================================================
    # Activation Operations
    # =========================================================================

    async def activate(self, config_id: str) -> CommandResult:
        """
        Activate an entertainment configuration.

        This prepares the configuration for streaming but does not
        start the stream itself. Streaming requires a separate
        DTLS connection to the bridge.

        Args:
            config_id: Configuration ID to activate

        Returns:
            CommandResult indicating success/failure
        """
        config = await self.get_configuration(config_id)

        try:
            await self.connector.put(
                f"/resource/entertainment_configuration/{config_id}",
                {"action": "start"}
            )

            return CommandResult(
                success=True,
                message=f"Activated entertainment configuration '{config.name}'"
            )

        except APIError as e:
            raise EntertainmentActivationError(config_id, str(e))

    async def deactivate(self, config_id: str) -> CommandResult:
        """
        Deactivate an entertainment configuration.

        Args:
            config_id: Configuration ID to deactivate

        Returns:
            CommandResult indicating success/failure
        """
        config = await self.get_configuration(config_id)

        try:
            await self.connector.put(
                f"/resource/entertainment_configuration/{config_id}",
                {"action": "stop"}
            )

            return CommandResult(
                success=True,
                message=f"Deactivated entertainment configuration '{config.name}'"
            )

        except APIError as e:
            return CommandResult(
                success=False,
                message=f"Failed to deactivate: {e}",
                errors=[str(e)]
            )

    async def get_status(self, config_id: str) -> str:
        """
        Get the current status of an entertainment configuration.

        Args:
            config_id: Configuration ID

        Returns:
            Status string ("active" or "inactive")
        """
        config = await self.get_configuration(config_id)
        return config.status

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _parse_configuration(self, data: dict) -> EntertainmentConfiguration:
        """Parse API response into EntertainmentConfiguration object."""
        # Parse channels
        channels = []
        for ch_data in data.get("channels", []):
            members = [
                m.get("service", {}).get("rid", "")
                for m in ch_data.get("members", [])
            ]
            pos = ch_data.get("position", {})
            channels.append(EntertainmentChannel(
                channel_id=ch_data.get("channel_id", 0),
                position=(pos.get("x", 0), pos.get("y", 0), pos.get("z", 0)),
                members=members
            ))

        # Parse locations
        locations = []
        for loc_data in data.get("locations", {}).get("service_locations", []):
            service = loc_data.get("service", {})
            pos = loc_data.get("position", {})
            locations.append(EntertainmentLocation(
                service_id=service.get("rid", ""),
                position=(pos.get("x", 0), pos.get("y", 0), pos.get("z", 0))
            ))

        # Parse light services
        light_services = [
            ls.get("rid", "")
            for ls in data.get("light_services", [])
        ]

        return EntertainmentConfiguration(
            id=data.get("id", ""),
            name=data.get("metadata", {}).get("name", "Unknown"),
            configuration_type=data.get("configuration_type", "other"),
            status=data.get("status", "inactive"),
            stream_proxy_mode=data.get("stream_proxy", {}).get("mode", "auto"),
            channels=channels,
            locations=locations,
            light_services=light_services
        )

    def get_configuration_types(self) -> list[str]:
        """Get list of valid entertainment configuration types."""
        return ENTERTAINMENT_TYPES.copy()

    async def get_entertainment_services(self) -> list[dict]:
        """
        Get list of entertainment-capable light services.

        Returns:
            List of dicts with 'id' and 'name' keys
        """
        services = []
        try:
            response = await self.connector.get("/resource/entertainment")
            for data in response.get("data", []):
                service_id = data.get("id")
                owner = data.get("owner", {})
                owner_id = owner.get("rid")

                # Try to get the light name
                light_name = "Unknown"
                if owner_id:
                    device = self.dm.devices.get(owner_id)
                    if device:
                        light_name = device.name

                services.append({
                    "id": service_id,
                    "name": light_name,
                    "owner_id": owner_id
                })

        except APIError as e:
            logger.error(f"Failed to get entertainment services: {e}")

        return services
