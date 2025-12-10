# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hue Controller is a Python natural language interface for Philips Hue lights using API v2. It provides CLI control through plain English commands, bridge discovery, and state management.

## Commands

```bash
# Install dependencies (using Poetry)
poetry install

# First-time setup (discovers bridge, authenticates via link button)
poetry run hue-setup
# or: python setup_bridge.py

# Run the interactive CLI
poetry run hue
poetry run hue --config custom_config.json
poetry run hue -v  # verbose logging
# or: python cli_interface.py [options]
```

## Architecture

### Core Layer (`hue_controller/`)

- **bridge_connector.py**: HTTP client with rate limiting (10 req/s lights, 1 req/s groups), mDNS/cloud bridge discovery, link button authentication, SSE event subscription
- **device_manager.py**: State cache for all resources (lights, rooms, zones, scenes), fuzzy name matching via normalized index, connectivity tracking from zigbee_connectivity events
- **command_interpreter.py**: NLP parser converts English to `ParsedCommand` objects; `CommandExecutor` sends API requests
- **models.py**: Dataclasses for all Hue resources (Light, Room, Zone, Scene) and API request/response types

### Extended Features (`hue_controller/managers/`)

- **scene_manager.py**: Create, update, duplicate, delete scenes
- **group_manager.py**: Room and zone management
- **effects_manager.py**: Light effects (candle, fire, etc.) and timed effects (sunrise/sunset)
- **entertainment_manager.py**: Entertainment API configuration

### Wizards (`hue_controller/wizards/`)

Interactive CLI wizards for complex operations (scene creation, room setup, entertainment configuration).

### Entry Points

- **cli_interface.py**: `HueCLI` class runs the REPL, routes built-in commands (help, status, lights, rooms, scenes, refresh) and delegates natural language to `CommandInterpreter`
- **setup_bridge.py**: One-time setup flow for bridge discovery and authentication

## Key Patterns

- All API communication is async via `httpx` with HTTP/2
- Config stored in `config.json` with 0600 permissions (contains application_key)
- Bridge uses self-signed certs, SSL verification disabled via custom context
- Rate limiting enforced by `RateLimiter` class using token bucket algorithm
- Rooms contain devices, zones contain lights directly
- `grouped_light` service used for room/zone commands (more efficient than individual lights)
- State updates via SSE keep `DeviceManager` cache current

## API Endpoints

Base path: `/clip/v2`

- Resources: `/resource/light`, `/resource/room`, `/resource/zone`, `/resource/scene`, etc.
- Scene recall: `PUT /resource/scene/{id}` with `{"recall": {"action": "active"}}`
- Light control: `PUT /resource/light/{id}` with payload like `{"on": {"on": true}, "dimming": {"brightness": 50}}`
- Group control: `PUT /resource/grouped_light/{id}` (same payload format)

## Dependencies

Dependencies are managed with Poetry (see `pyproject.toml`):

- `httpx[http2]`: Async HTTP client
- `zeroconf`: mDNS bridge discovery
