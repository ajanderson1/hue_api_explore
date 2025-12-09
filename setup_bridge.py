#!/usr/bin/env python3
"""
Hue Bridge Setup Script

Discovers the Hue Bridge on your network and creates authentication credentials.
Run this once before using the CLI interface.

Usage:
    python setup_bridge.py [--config CONFIG_PATH]
"""

import argparse
import asyncio
import sys
from pathlib import Path


async def setup(config_path: str) -> bool:
    """
    Run the bridge setup process.

    Args:
        config_path: Path to save configuration

    Returns:
        True if setup was successful
    """
    # Import here to avoid issues if dependencies aren't installed
    try:
        from hue_controller.bridge_connector import BridgeConnector
        from hue_controller.exceptions import (
            BridgeNotFoundError,
            LinkButtonNotPressedError,
            AuthenticationError,
        )
    except ImportError as e:
        print(f"Error: Could not import hue_controller. {e}")
        print("Make sure you've installed the dependencies:")
        print("  pip install httpx zeroconf")
        return False

    print("=" * 50)
    print("Hue Bridge Setup")
    print("=" * 50)
    print()

    # Check for existing config
    connector = BridgeConnector(config_path)

    if connector.is_configured:
        print(f"Existing configuration found at {config_path}")
        print(f"  Bridge IP: {connector.bridge_ip}")
        print()
        response = input("Overwrite existing configuration? [y/N]: ").strip().lower()
        if response != "y":
            print("Setup cancelled.")
            return False
        print()

    # Step 1: Discover bridge
    print("Step 1: Searching for Hue Bridge on your network...")
    print("  (This may take up to 10 seconds)")
    print()

    try:
        bridge_ip = await connector.discover_bridge(timeout=10.0)
        print(f"  Found bridge at: {bridge_ip}")
    except BridgeNotFoundError:
        print("  ERROR: No Hue Bridge found on the network.")
        print()
        print("  Troubleshooting:")
        print("    - Make sure your bridge is powered on")
        print("    - Ensure you're on the same network as the bridge")
        print("    - Try entering the IP manually:")
        print()
        manual_ip = input("  Enter bridge IP (or press Enter to cancel): ").strip()
        if not manual_ip:
            return False
        connector.bridge_ip = manual_ip
        bridge_ip = manual_ip

    # Step 2: Check V2 API support
    print()
    print("Step 2: Checking bridge compatibility...")

    try:
        if await connector.check_v2_support():
            print("  Bridge supports API v2")
        else:
            print("  WARNING: Bridge may not support API v2.")
            print("  Please update your bridge firmware for best compatibility.")
    except Exception as e:
        print(f"  Could not check API version: {e}")

    # Step 3: Authenticate
    print()
    print("Step 3: Authentication")
    print()
    print("  +-------------------------------------------------+")
    print("  |  Press the LINK BUTTON on your Hue Bridge now!  |")
    print("  +-------------------------------------------------+")
    print()
    input("  Press Enter after pressing the link button...")
    print()
    print("  Authenticating...")

    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            app_key = await connector.authenticate(
                app_name="hue_controller",
                device_name="python_cli"
            )
            print(f"  Success! Application key created.")
            break

        except LinkButtonNotPressedError:
            if attempt < max_attempts:
                print(f"  Link button not pressed. Attempt {attempt}/{max_attempts}")
                print()
                input("  Press the link button and then press Enter...")
                print("  Retrying...")
            else:
                print("  ERROR: Link button was not pressed.")
                print("  Please run setup again and press the link button.")
                return False

        except AuthenticationError as e:
            print(f"  ERROR: Authentication failed: {e}")
            return False

    # Step 4: Save config
    print()
    print("Step 4: Saving configuration...")
    connector.save_config()
    print(f"  Configuration saved to: {Path(config_path).absolute()}")

    # Step 5: Verify
    print()
    print("Step 5: Verifying connection...")

    try:
        response = await connector.get("/resource")
        resource_count = len(response.get("data", []))
        print(f"  Success! Found {resource_count} resources on the bridge.")
    except Exception as e:
        print(f"  WARNING: Verification failed: {e}")
        print("  The configuration was saved, but there may be connection issues.")

    await connector.close()

    # Done!
    print()
    print("=" * 50)
    print("Setup Complete!")
    print("=" * 50)
    print()
    print("You can now run the CLI interface:")
    print("  python cli_interface.py")
    print()

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Set up connection to your Hue Bridge"
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to configuration file (default: config.json)"
    )

    args = parser.parse_args()

    try:
        success = asyncio.run(setup(args.config))
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
        sys.exit(1)


if __name__ == "__main__":
    main()
