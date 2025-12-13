# Advanced Usage Guide

This guide covers the Admin Scene Wizard and other advanced features for power users who want complete control over their Philips Hue scenes.

## Table of Contents

- [Choosing Your Interaction Mode](#choosing-your-interaction-mode)
- [Admin Scene Wizard](#admin-scene-wizard)
  - [Getting Started](#getting-started)
  - [Wizard Sections](#wizard-sections)
  - [Light Templates](#light-templates)
  - [Live Testing](#live-testing)
- [Glossary & Help System](#glossary--help-system)
- [Scene Data Structure](#scene-data-structure)
- [API Reference](#api-reference)

---

## Choosing Your Interaction Mode

Hue Controller wizards support three interaction modes to match your experience level. When you launch a wizard, you'll be prompted to select a mode:

### Mode Comparison

| Feature | Simple Mode | Standard Mode | Advanced Mode |
|---------|-------------|---------------|---------------|
| Presets | Yes | Yes + technical details | Yes |
| Technical values (mirek, xy) | Hidden | Shown with explanations | Shown |
| All API options | No | Some | All |
| Palette section | No | No | Yes |
| Dynamics section | No | Yes | Yes |
| Gradient section | No | No | Yes |
| Recall settings | No | No | Yes |
| Help text | Friendly | With technical context | Available on request |

### Simple Mode

Best for: **New users who want quick results**

- Choose from preset templates like "Warm & Cozy" or "Movie Time"
- No technical jargon - everything uses plain English
- Guided step-by-step with sensible defaults
- Perfect for: Creating scenes quickly without learning API terminology

**Example flow:**
```
🟢 Using Simple mode

? Select a mood:
  ☀️ Bright & Energizing - Perfect for mornings or active tasks
  🔥 Warm & Cozy - Relaxing warm glow
  🕯️ Candlelight - Very warm, flickering ambiance
  🎬 Movie Time - Dim, warm bias lighting
```

### Standard Mode

Best for: **Users who want to understand what they're configuring**

- See technical values (2700K, 50%) with explanations
- Presets available with technical annotations
- Skip steps with sensible defaults
- Perfect for: Learning how Hue lighting works while still getting guidance

**Example:**
```
🟡 Using Standard mode

Preset: Warm & Cozy
Technical: 50% brightness, 2700K (370 mirek), 1s transition

? Adjust brightness (0-100%):
  Current: 50% - Comfortable level for relaxation
```

### Advanced Mode

Best for: **Power users who want full control**

- Access every Hue API parameter
- Raw value input with validation
- All sections available (palette, dynamics, gradient, recall)
- Perfect for: Fine-tuning scenes, gradients, and dynamic effects

**Example:**
```
🔴 Using Advanced mode

Configure light actions:
  > Apply template to ALL lights
  > Configure lights individually
    - Set brightness (0-100)
    - Set color (temperature/XY/gradient)
    - Set effect (candle, fire, prism...)
    - Set transition duration (0-6553500ms)
  > Configure palette
  > Configure dynamics
```

### Switching Modes

Mode is selected once at wizard start and cannot be changed mid-flow. To use a different mode, exit the wizard and restart.

---

## Glossary & Help System

Get help on Hue terminology at any time:

### From the CLI

```bash
hue> /help mirek
# or
hue> ?gamut
# or
hue> glossary    # List all available terms
```

### Example Output

```
╭───────────────────────── Mirek ──────────────────────────╮
│                                                          │
│ A unit for measuring color temperature (micro reciprocal │
│ degrees). Lower mirek = cooler/bluer light (like         │
│ daylight). Higher mirek = warmer/yellower light (like    │
│ candlelight).                                            │
│                                                          │
│ Example: 153 mirek = 6500K (cool daylight), 370 mirek =  │
│ 2700K (warm white), 500 mirek = 2000K (candlelight)      │
│                                                          │
│ Technical: Mirek = 1,000,000 / Kelvin. Valid range:      │
│ 153-500 (6500K-2000K).                                   │
│                                                          │
│ See also: color temperature, kelvin, warm, cool          │
╰──────────────────────────────────────────────────────────╯
```

### Available Terms

| Category | Terms |
|----------|-------|
| Color & Light | mirek, color temperature, kelvin, gamut, xy color, brightness |
| Groups | room, zone, grouped light, archetype |
| Scenes | scene, recall, palette, auto dynamic, scene action |
| Effects | effect, timed effect, dynamics, transition, signaling, gradient |
| Entertainment | entertainment area |

---

## Admin Scene Wizard

The Admin Scene Wizard provides comprehensive access to **every scene parameter** available in the Hue API v2. Unlike the basic scene wizard, the admin wizard exposes all options including:

- Per-light transition durations
- Dynamic color palettes with brightness per color
- Gradient configurations
- Light effects (candle, fire, prism, etc.)
- Scene icons/images
- Recall settings (activation mode, duration override)

### Getting Started

Launch the wizard from the CLI:

```bash
poetry run hue
> wizard admin
```

Or use any of these aliases:
- `wizard admin`
- `wizard advanced`
- `wizard admin scene`
- `wizard admin-scene`

### Wizard Sections

The wizard is organized into 6 sections. You can navigate forward, backward, or jump directly to any section from the review screen.

```
┌─────────────────────────────────────────────────────────────┐
│  ○ Metadata  ○ Light Actions  ○ Palette  ○ Dynamics  ○ Recall  ● Review  │
└─────────────────────────────────────────────────────────────┘
```

#### 1. Target Selection (Pre-section)

Before the main wizard begins, select where the scene applies:

| Target | Description |
|--------|-------------|
| **Room** | A specific room (e.g., Living Room, Bedroom) |
| **Zone** | A lighting zone (e.g., Reading Nook, TV Area) |
| **Bridge Home** | All lights connected to your bridge |

#### 2. Metadata Section

Configure the scene's identity:

| Field | Required | Description |
|-------|----------|-------------|
| **Name** | Yes | 1-32 characters |
| **Icon** | No | Select from preset scene images |

Available scene icons:
- Bright, Dimmed, Nightlight
- Relax, Read, Concentrate, Energize
- Movie, Romance, Party

#### 3. Light Actions Section

This is where you configure what each light does when the scene activates.

**Menu Options:**

| Option | Description |
|--------|-------------|
| Apply template to ALL lights | Quick setup using a preset |
| Configure lights individually | Fine-tune each light |
| View current configuration | See a table of all settings |
| Test current settings | Preview on actual lights |

**Per-Light Configuration:**

| Setting | Range/Options | Description |
|---------|---------------|-------------|
| Power | ON / OFF | Whether light is on |
| Brightness | 1-100% | Light intensity |
| Color Mode | Temperature / Color / Gradient | How color is specified |
| Color Temperature | 2000K-6500K (or mirek 153-500) | Warm to cool white |
| Color (XY) | Name, hex (#FF0000), or XY coordinates | Full color spectrum |
| Gradient | 2-5 color points | Multi-color gradient |
| Effect | candle, fire, prism, sparkle, etc. | Dynamic light effect |
| Transition | 0ms - 6553500ms (~109 min) | Animation duration |
| Enabled | Yes / No | Include in scene or exclude |

#### 4. Palette Section

Configure dynamic color cycling for scenes that continuously change.

| Palette Component | Max Items | Description |
|-------------------|-----------|-------------|
| **Colors** | 9 | XY colors with optional brightness per color |
| **Color Temperatures** | 9 | Mirek values with optional brightness |
| **Dimming Levels** | 9 | Brightness percentages to cycle through |
| **Effects** | Multiple | Effects to cycle through |

When enabled, lights will smoothly transition between palette entries.

#### 5. Dynamics Section

Control how the scene transitions and animates:

| Setting | Range | Description |
|---------|-------|-------------|
| **Speed** | 0.0 - 1.0 | Palette cycling speed (0=slowest, 1=fastest) |
| **Auto Dynamic** | Yes/No | Automatically enable palette cycling on activation |
| **Global Transition** | 0ms - 1hr | Default transition for all lights |

#### 6. Recall Section

Configure how the scene behaves when activated:

| Setting | Options | Description |
|---------|---------|-------------|
| **Recall Action** | active, dynamic_palette, static | Activation mode |
| **Transition Duration** | 0ms - 60s | Override scene's transition times |
| **Brightness Override** | 1-100% | Override all brightness values |

**Recall Actions Explained:**

| Action | Behavior |
|--------|----------|
| `active` | Normal activation with configured transitions |
| `dynamic_palette` | Activate and immediately start palette cycling |
| `static` | Activate instantly without any transitions |

#### 7. Review Section

Final summary before creating the scene:

- View complete configuration summary
- Test all settings on actual lights
- Jump back to any section to make changes
- Create the scene
- Optionally activate immediately after creation

---

## Light Templates

The wizard includes 12 pre-configured templates for quick setup:

### White/Temperature Templates

| Template | Brightness | Temperature | Description |
|----------|------------|-------------|-------------|
| **Bright White** | 100% | 4000K | Full brightness, neutral white |
| **Warm Relaxed** | 50% | 2700K | Dimmed warm light for relaxation |
| **Cozy Evening** | 30% | 2200K | Very warm, low brightness |
| **Energize** | 100% | 5500K | Cool bright light for focus |
| **Nightlight** | 5% | 2200K | Very dim warm light |
| **Off** | 0% | - | Light turned off |

### Color Templates

| Template | Brightness | Color | Description |
|----------|------------|-------|-------------|
| **Sunset Red** | 80% | Red-orange | Warm sunset colors |
| **Ocean Blue** | 70% | Deep blue | Calm ocean ambiance |
| **Forest Green** | 60% | Green | Natural forest tones |
| **Purple Mood** | 50% | Purple | Deep purple ambiance |

### Effect Templates

| Template | Brightness | Effect | Description |
|----------|------------|--------|-------------|
| **Candle Effect** | 60% | candle | Flickering candle simulation |
| **Fire Effect** | 80% | fire | Warm fire glow |

---

## Live Testing

The wizard supports testing your configuration on actual lights before saving:

### Test All Lights

From the Light Actions menu or Review section:
1. Select "Test current settings" or "Test All Settings"
2. All configured lights will update to your settings
3. Press Enter when done viewing
4. Continue editing or create the scene

### Test Single Light

While configuring an individual light:
1. Select "Test this light"
2. That specific light updates to current settings
3. Press Enter when done
4. Continue configuring

> **Note:** Testing applies settings temporarily. The scene is not saved until you complete the wizard.

---

## Scene Data Structure

For developers and advanced users, here's the complete JSON structure that the wizard generates:

```json
{
    "metadata": {
        "name": "My Scene",
        "image": {
            "rid": "732ff1d9-76a7-4630-aad0-c8acc499bb0b",
            "rtype": "public_image"
        }
    },

    "group": {
        "rid": "da994502-9245-4aeb-8176-39c2f9f735e5",
        "rtype": "room"
    },

    "actions": [
        {
            "target": {
                "rid": "6266e06b-372a-4427-9db0-43b781feb30e",
                "rtype": "light"
            },
            "action": {
                "on": {"on": true},
                "dimming": {"brightness": 80.0},
                "color_temperature": {"mirek": 370},
                "dynamics": {"duration": 1000}
            }
        }
    ],

    "palette": {
        "color": [
            {
                "color": {"xy": {"x": 0.6, "y": 0.38}},
                "dimming": {"brightness": 100.0}
            }
        ],
        "color_temperature": [
            {
                "color_temperature": {"mirek": 370},
                "dimming": {"brightness": 80.0}
            }
        ],
        "dimming": [
            {"brightness": 100.0},
            {"brightness": 50.0}
        ],
        "effects": [
            {"effect": "candle"}
        ]
    },

    "speed": 0.5,
    "auto_dynamic": false,

    "type": "scene"
}
```

### Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `metadata.name` | string | Scene name (1-32 chars) |
| `metadata.image.rid` | UUID | Public image resource ID |
| `group.rid` | UUID | Target room/zone/bridge_home ID |
| `group.rtype` | string | "room", "zone", or "bridge_home" |
| `actions` | array | Per-light configurations |
| `actions[].target.rid` | UUID | Light resource ID |
| `actions[].action.on.on` | boolean | Power state |
| `actions[].action.dimming.brightness` | float | 0-100 |
| `actions[].action.color.xy` | object | {x, y} color coordinates |
| `actions[].action.color_temperature.mirek` | int | 153-500 |
| `actions[].action.dynamics.duration` | int | Transition ms |
| `actions[].action.effects.effect` | string | Effect name |
| `actions[].action.gradient` | object | Gradient config |
| `palette.color` | array | Colors for cycling |
| `palette.color_temperature` | array | Temps for cycling |
| `palette.dimming` | array | Brightness levels |
| `palette.effects` | array | Effects for cycling |
| `speed` | float | 0.0-1.0 palette speed |
| `auto_dynamic` | boolean | Auto-enable cycling |

---

## API Reference

### Color Temperature Presets

| Name | Kelvin | Mirek | Description |
|------|--------|-------|-------------|
| candlelight | 2000K | 500 | Very warm, like candlelight |
| warm | 2700K | 370 | Warm white, incandescent |
| soft | 3000K | 333 | Soft white |
| neutral | 4000K | 250 | Neutral white, balanced |
| cool | 5000K | 200 | Cool white |
| daylight | 5500K | 182 | Natural daylight |
| bright | 6500K | 153 | Bright daylight |

**Conversion:** `mirek = 1,000,000 / kelvin`

### Available Effects

| Effect | Description |
|--------|-------------|
| `no_effect` | Static light (no effect) |
| `candle` | Flickering candle |
| `fire` | Warm fire glow |
| `prism` | Shifting rainbow |
| `sparkle` | Twinkling sparkle |
| `opal` | Soft shifting opal |
| `glisten` | Gentle glistening |
| `underwater` | Blue underwater shimmer |
| `cosmos` | Deep space colors |
| `sunbeam` | Warm sunbeam glow |
| `enchant` | Magical colors |

### Gradient Modes

| Mode | Description |
|------|-------------|
| `interpolated_palette` | Smooth gradient between colors |
| `interpolated_palette_mirrored` | Symmetric mirrored gradient |
| `random_pixelated` | Random color pixels |
| `segmented` | Distinct color segments |

### Recall Actions

| Action | Description |
|--------|-------------|
| `active` | Normal activation |
| `dynamic_palette` | Activate with cycling |
| `static` | Instant, no transitions |

---

## Tips & Best Practices

1. **Start with templates** - Apply a template to all lights first, then customize individual lights as needed.

2. **Test frequently** - Use the live test feature to preview changes before saving.

3. **Use meaningful names** - Scene names appear in the Hue app and voice assistants.

4. **Consider transitions** - Longer transitions (2-5 seconds) create smoother, more relaxing changes. Instant transitions are better for task lighting.

5. **Palette vs. Static** - Use palettes for ambient/mood scenes that should continuously change. Use static actions for task-oriented scenes.

6. **Exclude lights** - If you don't want a scene to affect certain lights, disable them rather than deleting the action. This makes it easier to re-enable later.

7. **Gradient lights** - If you have gradient-capable lights (like Play Gradient Lightstrip), use the gradient color mode for multi-color effects on a single light.
