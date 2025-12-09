"""
Bridge connection, discovery, and authentication for Hue API v2.
"""

import asyncio
import json
import logging
import os
import ssl
import time
from pathlib import Path
from typing import Any, AsyncIterator

import httpx
from zeroconf import ServiceBrowser, ServiceStateChange, Zeroconf
from zeroconf.asyncio import AsyncZeroconf

from .exceptions import (
    APIError,
    AuthenticationError,
    BridgeNotFoundError,
    ConnectionError,
    LinkButtonNotPressedError,
    RateLimitError,
)

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter for API calls."""

    def __init__(self, calls_per_second: float = 10.0):
        self._calls_per_second = calls_per_second
        self._min_interval = 1.0 / calls_per_second
        self._last_call = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait until a request can be made."""
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_call
            if elapsed < self._min_interval:
                await asyncio.sleep(self._min_interval - elapsed)
            self._last_call = time.monotonic()


class BridgeConnector:
    """
    Manages connection, authentication, and HTTP communication with a Hue Bridge.

    Handles:
        - mDNS and cloud-based bridge discovery
        - Link button authentication flow
        - Credential persistence
        - Rate-limited HTTPS requests
        - Server-Sent Events (SSE) for real-time updates
    """

    DEFAULT_CONFIG_PATH = "config.json"
    DISCOVERY_TIMEOUT = 10.0
    API_BASE = "/clip/v2"
    HUE_MDNS_SERVICE = "_hue._tcp.local."

    def __init__(self, config_path: str | Path | None = None):
        """
        Initialize the connector.

        Args:
            config_path: Path to config file. Defaults to config.json in current directory.
        """
        self.config_path = Path(config_path or self.DEFAULT_CONFIG_PATH)
        self.bridge_ip: str | None = None
        self.application_key: str | None = None
        self.bridge_id: str | None = None

        self._client: httpx.AsyncClient | None = None
        self._rate_limiter = RateLimiter(calls_per_second=10.0)
        self._group_rate_limiter = RateLimiter(calls_per_second=1.0)

        # Load existing config if available
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from file if it exists."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    config = json.load(f)
                self.bridge_ip = config.get("bridge_ip")
                self.application_key = config.get("application_key")
                self.bridge_id = config.get("bridge_id")
                logger.info(f"Loaded config from {self.config_path}")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load config: {e}")

    def save_config(self) -> None:
        """Save current configuration to file with restricted permissions."""
        config = {
            "bridge_ip": self.bridge_ip,
            "application_key": self.application_key,
            "bridge_id": self.bridge_id,
        }

        # Write to temp file first, then rename for atomicity
        temp_path = self.config_path.with_suffix(".tmp")
        with open(temp_path, "w") as f:
            json.dump(config, f, indent=2)

        # Set restrictive permissions (owner read/write only)
        os.chmod(temp_path, 0o600)

        # Atomic rename
        temp_path.rename(self.config_path)
        logger.info(f"Saved config to {self.config_path}")

    @property
    def is_configured(self) -> bool:
        """Check if we have valid bridge configuration."""
        return bool(self.bridge_ip and self.application_key)

    async def discover_bridge(self, timeout: float = DISCOVERY_TIMEOUT) -> str:
        """
        Discover Hue Bridge on the local network.

        Tries mDNS first, falls back to cloud discovery service.

        Args:
            timeout: Discovery timeout in seconds

        Returns:
            Bridge IP address

        Raises:
            BridgeNotFoundError: If no bridge is found
        """
        # Try mDNS first
        logger.info("Searching for Hue Bridge via mDNS...")
        bridge_ip = await self._discover_mdns(timeout)

        if bridge_ip:
            logger.info(f"Found bridge via mDNS: {bridge_ip}")
            self.bridge_ip = bridge_ip
            return bridge_ip

        # Fall back to cloud discovery
        logger.info("mDNS failed, trying cloud discovery...")
        bridge_ip = await self._discover_cloud()

        if bridge_ip:
            logger.info(f"Found bridge via cloud: {bridge_ip}")
            self.bridge_ip = bridge_ip
            return bridge_ip

        raise BridgeNotFoundError()

    async def _discover_mdns(self, timeout: float) -> str | None:
        """Discover bridge using mDNS (Zeroconf)."""
        discovered_bridges: list[str] = []
        discovery_event = asyncio.Event()

        def on_service_state_change(
            zeroconf: Zeroconf,
            service_type: str,
            name: str,
            state_change: ServiceStateChange
        ) -> None:
            if state_change == ServiceStateChange.Added:
                info = zeroconf.get_service_info(service_type, name)
                if info and info.addresses:
                    # Get IPv4 address
                    for addr in info.addresses:
                        if len(addr) == 4:  # IPv4
                            ip = ".".join(str(b) for b in addr)
                            discovered_bridges.append(ip)
                            discovery_event.set()
                            break

        azc = AsyncZeroconf()
        try:
            browser = ServiceBrowser(
                azc.zeroconf,
                self.HUE_MDNS_SERVICE,
                handlers=[on_service_state_change]
            )

            try:
                await asyncio.wait_for(discovery_event.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                pass

        finally:
            await azc.async_close()

        return discovered_bridges[0] if discovered_bridges else None

    async def _discover_cloud(self) -> str | None:
        """Discover bridge using Philips cloud service."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("https://discovery.meethue.com")
                if response.status_code == 200:
                    bridges = response.json()
                    if bridges and len(bridges) > 0:
                        return bridges[0].get("internalipaddress")
        except Exception as e:
            logger.warning(f"Cloud discovery failed: {e}")
        return None

    async def authenticate(
        self,
        app_name: str = "hue_controller",
        device_name: str = "python"
    ) -> str:
        """
        Authenticate with the bridge via link button.

        The user must press the link button on the bridge before calling this.

        Args:
            app_name: Application name (max 20 chars)
            device_name: Device name (max 19 chars)

        Returns:
            Application key

        Raises:
            BridgeNotFoundError: If bridge IP is not set
            LinkButtonNotPressedError: If link button was not pressed
            AuthenticationError: On other authentication errors
        """
        if not self.bridge_ip:
            raise BridgeNotFoundError("Bridge IP not set. Run discover_bridge() first.")

        # V1 API endpoint for creating users (still used for key generation)
        url = f"https://{self.bridge_ip}/api"

        payload = {
            "devicetype": f"{app_name[:20]}#{device_name[:19]}",
            "generateclientkey": True
        }

        ssl_context = self._create_ssl_context()

        async with httpx.AsyncClient(verify=ssl_context, timeout=10.0) as client:
            response = await client.post(url, json=payload)

            if response.status_code != 200:
                raise AuthenticationError(f"HTTP {response.status_code}")

            result = response.json()

            if isinstance(result, list) and len(result) > 0:
                item = result[0]

                if "error" in item:
                    error = item["error"]
                    if error.get("type") == 101:
                        raise LinkButtonNotPressedError()
                    raise AuthenticationError(
                        error.get("description", "Unknown error"),
                        {"error_type": error.get("type")}
                    )

                if "success" in item:
                    success = item["success"]
                    self.application_key = success.get("username")
                    self.bridge_id = success.get("clientkey")  # For entertainment API
                    self.save_config()
                    return self.application_key

            raise AuthenticationError("Unexpected response format")

    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context that accepts the bridge's self-signed certificate."""
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            ssl_context = self._create_ssl_context()
            self._client = httpx.AsyncClient(
                base_url=f"https://{self.bridge_ip}",
                verify=ssl_context,
                http2=True,  # Use HTTP/2 for multiplexing
                timeout=30.0,
                headers={
                    "hue-application-key": self.application_key,
                    "Content-Type": "application/json",
                }
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def request(
        self,
        method: str,
        endpoint: str,
        body: dict | None = None,
        is_group_command: bool = False
    ) -> dict[str, Any]:
        """
        Make a rate-limited API request.

        Args:
            method: HTTP method (GET, PUT, POST, DELETE)
            endpoint: API endpoint (relative to /clip/v2)
            body: Request body for PUT/POST
            is_group_command: If True, use stricter rate limit for group commands

        Returns:
            Response JSON

        Raises:
            ConnectionError: On connection failure
            RateLimitError: If rate limit is hit (429)
            APIError: On API errors
        """
        if not self.is_configured:
            raise ConnectionError("Not configured. Run setup first.", self.bridge_ip)

        # Apply rate limiting
        if is_group_command:
            await self._group_rate_limiter.acquire()
        await self._rate_limiter.acquire()

        client = await self._get_client()

        # Build full path
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        if not endpoint.startswith(self.API_BASE):
            endpoint = self.API_BASE + endpoint

        try:
            if method.upper() == "GET":
                response = await client.get(endpoint)
            elif method.upper() == "PUT":
                response = await client.put(endpoint, json=body)
            elif method.upper() == "POST":
                response = await client.post(endpoint, json=body)
            elif method.upper() == "DELETE":
                response = await client.delete(endpoint)
            else:
                raise ValueError(f"Unsupported method: {method}")

        except httpx.ConnectError as e:
            raise ConnectionError(f"Failed to connect to bridge: {e}", self.bridge_ip)
        except httpx.TimeoutException as e:
            raise ConnectionError(f"Request timed out: {e}", self.bridge_ip)

        # Handle response
        if response.status_code == 429:
            raise RateLimitError()

        if response.status_code == 401:
            raise AuthenticationError("Invalid application key")

        if response.status_code >= 400:
            try:
                error_data = response.json()
                errors = error_data.get("errors", [])
                message = errors[0].get("description") if errors else f"HTTP {response.status_code}"
            except Exception:
                message = f"HTTP {response.status_code}"
                errors = []

            raise APIError(message, response.status_code, endpoint, errors)

        return response.json()

    async def get(self, endpoint: str) -> dict[str, Any]:
        """Convenience method for GET requests."""
        return await self.request("GET", endpoint)

    async def put(
        self,
        endpoint: str,
        body: dict,
        is_group_command: bool = False
    ) -> dict[str, Any]:
        """Convenience method for PUT requests."""
        return await self.request("PUT", endpoint, body, is_group_command)

    async def post(self, endpoint: str, body: dict) -> dict[str, Any]:
        """Convenience method for POST requests."""
        return await self.request("POST", endpoint, body)

    async def delete(self, endpoint: str) -> dict[str, Any]:
        """Convenience method for DELETE requests."""
        return await self.request("DELETE", endpoint)

    async def subscribe_events(self) -> AsyncIterator[dict]:
        """
        Subscribe to Server-Sent Events (SSE) for real-time updates.

        Yields:
            Event dictionaries with type, id, and data fields

        Note:
            This is a long-running generator. Use it in an async for loop.
        """
        if not self.is_configured:
            raise ConnectionError("Not configured", self.bridge_ip)

        ssl_context = self._create_ssl_context()
        url = f"https://{self.bridge_ip}/eventstream/clip/v2"

        async with httpx.AsyncClient(
            verify=ssl_context,
            timeout=None,  # SSE is long-running
            headers={
                "hue-application-key": self.application_key,
                "Accept": "text/event-stream",
            }
        ) as client:
            async with client.stream("GET", url) as response:
                event_data = {}
                async for line in response.aiter_lines():
                    line = line.strip()

                    if not line:
                        # Empty line signals end of event
                        if event_data:
                            yield event_data
                            event_data = {}
                        continue

                    if line.startswith("id:"):
                        event_data["id"] = line[3:].strip()
                    elif line.startswith("data:"):
                        data_str = line[5:].strip()
                        try:
                            event_data["data"] = json.loads(data_str)
                        except json.JSONDecodeError:
                            event_data["data"] = data_str

    async def get_bridge_config(self) -> dict:
        """Get bridge configuration (useful for checking API version)."""
        # Use V1 config endpoint for basic info
        ssl_context = self._create_ssl_context()
        async with httpx.AsyncClient(verify=ssl_context, timeout=10.0) as client:
            response = await client.get(f"https://{self.bridge_ip}/api/config")
            return response.json()

    async def check_v2_support(self) -> bool:
        """Check if the bridge supports API v2."""
        try:
            config = await self.get_bridge_config()
            sw_version = config.get("swversion", "0")
            # V2 requires software version 1948086000 or higher
            return int(sw_version) >= 1948086000
        except Exception:
            return False
