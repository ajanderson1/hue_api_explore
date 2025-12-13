# Wizard System Guide

A comprehensive guide to the Hue Controller wizard system, including interaction modes, contextual help, visual feedback, and the built-in glossary.

## Table of Contents

- [Overview](#overview)
- [Mode Selection](#mode-selection)
  - [Simple Mode](#simple-mode)
  - [Standard Mode](#standard-mode)
  - [Advanced Mode](#advanced-mode)
- [Contextual Help](#contextual-help)
- [Visual Feedback](#visual-feedback)
- [Navigation](#navigation)
- [Presets](#presets)
- [Glossary](#glossary)

---

## Overview

The Hue Controller wizard system provides an interactive, guided experience for configuring Philips Hue lights, scenes, rooms, and entertainment areas. Key features include:

- **Three-tier interaction model**: Choose your experience level (Simple, Standard, Advanced)
- **Contextual help**: Get explanations at every prompt
- **Visual feedback**: See brightness bars, color swatches, and progress indicators
- **Built-in glossary**: Look up Hue terminology anytime
- **Session persistence**: Resume interrupted wizards where you left off

---

## Mode Selection

When launching a wizard, you'll be prompted to select an interaction mode:

```
╭──────────────────────────────────────────╮
│     Choose Your Experience Level         │
│                                          │
│ Select how much detail you want to see   │
│ in this wizard.                          │
╰──────────────────────────────────────────╯

? Select mode:
  🟢 Simple Mode
  🟡 Standard Mode
  🔴 Advanced Mode
```

### Simple Mode

**Best for:** Beginners who want quick results without technical complexity.

**What you'll see:**
- Preset-based selections with friendly names
- No technical values (mirek, xy coordinates, etc.)
- Plain English descriptions
- Guided step-by-step flow

**Hidden features:**
- Palette configuration
- Gradient setup
- Recall settings
- Raw value input

**Example interaction:**
```
? Select a mood for your scene:

  ── Everyday ──
  ☀️ Bright & Energizing - Full brightness, cool daylight
  🌤️ Natural Daylight - Bright and balanced
  💡 Soft White - Comfortable everyday lighting

  ── Relax ──
  🔥 Warm & Cozy - Relaxing warm glow
  🌙 Dim & Relaxing - Low, warm light for winding down
  🕯️ Candlelight - Very warm, flickering ambiance
```

### Standard Mode

**Best for:** Users who want to understand what they're configuring while still getting guidance.

**What you'll see:**
- Technical values with explanations (e.g., "2700K - warm white, like incandescent bulbs")
- Presets with technical annotations
- Dynamics configuration
- Current value displays when editing

**Additional features:**
- Dynamics section
- Technical value display
- Skip-able steps with defaults

**Example interaction:**
```
Preset: Warm & Cozy
  Technical: 50% brightness, 2700K (370 mirek), 1000ms transition

? Adjust brightness:
  [████████████████░░░░░░░░░░░░░░] 50%

  Enter 0-100%, or press Enter for default (50%)
  Tip: 30% is good for ambient, 70% for tasks.
```

### Advanced Mode

**Best for:** Power users who want full control over every parameter.

**What you'll see:**
- All API parameters exposed
- Raw value input with validation
- Every section available
- Technical terminology (with help available on request)

**Full access to:**
- Palette configuration (dynamic scene colors)
- Gradient setup (multi-color gradients)
- Recall settings (activation behavior)
- Per-light transition durations
- All effects and dynamics options

---

## Contextual Help

Help is available throughout the wizard system:

### Inline Help

Every prompt includes context-aware help text:

```
? Enter color temperature:
  Choose warmth: 2700K (cozy) to 6500K (energizing).
  Type '?mirek' for detailed information.
```

### Quick Term Lookup

Type `?term` at any prompt to get instant help:

```
? Enter mirek value: ?mirek

╭─────────────────────── Mirek ───────────────────────╮
│                                                     │
│ A unit for measuring color temperature. Lower       │
│ mirek = cooler/bluer, higher mirek = warmer/        │
│ yellower.                                           │
│                                                     │
│ Example: 153 (6500K cool) to 500 (2000K warm)       │
│                                                     │
│ See also: color temperature, kelvin                 │
╰─────────────────────────────────────────────────────╯
```

### CLI Help Commands

From the main CLI:

```bash
hue> /help mirek     # Look up a term
hue> ?gamut          # Quick lookup
hue> glossary        # List all terms
```

---

## Visual Feedback

### Brightness Bars

When adjusting brightness, you'll see a visual representation:

```
Current brightness:
  [██████████████████████░░░░░░░░] 75%
```

### Color Temperature Swatches

Color temperature shows visual warmth indicator:

```
Selected temperature:
  ████ 2700K (370 mirek) - Warm white
```

### Progress Breadcrumbs

Multi-step wizards show your progress:

```
✓ Metadata → ● Light Actions → ○ Palette → ○ Dynamics → ○ Review
```

### Light State Indicators

Light status is shown visually:

```
Lights in Living Room:
  ● Ceiling Light - On (75%)
  ◕ Floor Lamp - On (50%)
  ○ Table Lamp - Off
  ◌ Desk Light - Unreachable
```

---

## Navigation

### Common Navigation Commands

At any prompt, you can type:

| Command | Action |
|---------|--------|
| `back` or `b` | Go to previous step |
| `skip` or `s` | Skip optional step |
| `cancel` or `c` | Cancel wizard |
| `?term` | Look up help for term |

### Arrow Key Navigation

Selection menus support:
- ↑/↓ arrows to navigate
- j/k vim keys to navigate
- Enter to select
- Esc or Ctrl+C to cancel

### Session Recovery

If you cancel or get disconnected mid-wizard, you can resume:

```
╭─────────────────────────────────────────╮
│     Found an interrupted session        │
│                                         │
│ Started 5 minutes ago                   │
│ Progress: 2 sections completed          │
╰─────────────────────────────────────────╯

? Would you like to continue where you left off? (Y/n)
```

---

## Presets

### Simple Mode Presets

Pre-configured lighting settings available in Simple Mode:

| Category | Presets |
|----------|---------|
| **Everyday** | Bright & Energizing, Natural Daylight, Soft White |
| **Relax** | Warm & Cozy, Dim & Relaxing, Candlelight, Nightlight |
| **Focus** | Focus Mode, Reading Light |
| **Entertainment** | Movie Time, Gaming, Party Colors |
| **Special** | Romantic, Sunset Glow, Ocean Waves, Forest |

### Standard Mode Presets

Same presets with technical details:

```
Warm & Cozy
  Technical: 50% brightness, 2700K (370 mirek), 1s transition

Movie Time
  Technical: 15% brightness, 2700K, 1.5s transition

Party Colors
  Technical: 75% brightness, dynamic cycling, 0.7 speed
```

### Templates in Advanced Mode

Advanced mode includes light templates for per-light configuration:

- Bright, Dimmed, Nightlight
- Warm, Cool, Neutral
- Red, Orange, Yellow, Green, Blue, Purple
- Candle, Fire, Prism effects
- Custom XY color input

---

## Glossary

### Color & Light Terms

| Term | Definition |
|------|------------|
| **Mirek** | Color temperature unit. Lower = cooler (153 = 6500K), higher = warmer (500 = 2000K) |
| **Kelvin (K)** | Standard color temperature unit. 2700K = warm, 6500K = cool daylight |
| **Gamut** | Color range a bulb can produce. Gamut C (newer) has wider range than Gamut A (older) |
| **XY Color** | CIE coordinate system for specifying colors. Values 0-1 for both x and y |
| **Brightness** | Light intensity 0-100%. Also called "dimming" in API |

### Groups & Rooms

| Term | Definition |
|------|------------|
| **Room** | Physical space containing devices. Each device belongs to one room |
| **Zone** | Flexible light grouping that can span rooms |
| **Grouped Light** | Virtual light controlling all lights in a room/zone together |
| **Archetype** | Category describing light/room type (e.g., living_room, spot_bulb) |

### Scenes

| Term | Definition |
|------|------------|
| **Scene** | Saved lighting configuration activated with one command |
| **Recall** | Activating a scene. "Active" = normal, "Static" = no transition |
| **Palette** | Collection of colors for dynamic scenes |
| **Auto Dynamic** | When enabled, scene cycles through palette colors |
| **Speed** | How fast dynamic scenes cycle (0 = slow, 1 = fast) |

### Effects & Dynamics

| Term | Definition |
|------|------------|
| **Effect** | Built-in animation (candle, fire, prism, sparkle, etc.) |
| **Timed Effect** | Duration-based effect like sunrise/sunset simulation |
| **Dynamics** | How lights animate when changing |
| **Transition** | Time for light to change states (in milliseconds) |
| **Gradient** | Multi-color display on gradient-capable lights |

### Entertainment

| Term | Definition |
|------|------------|
| **Entertainment Area** | Lights configured for high-speed sync with media |

---

## Tips

1. **Start with Simple Mode** if you're new to Hue customization
2. **Use `?term` frequently** to learn terminology as you go
3. **Test your settings** before saving - most wizards have a "Test" option
4. **Standard Mode is great for learning** - shows technical values with explanations
5. **Session recovery** means you won't lose work if you need to step away

---

*For detailed information about the Admin Scene Wizard, see [ADVANCED_USAGE.md](ADVANCED_USAGE.md)*
