# Hue Controller - Future Improvements

A roadmap of nice-to-haves and planned enhancements for future development.

---

## Getting Back Up to Speed

### Quick Start When Returning
```bash
# 1. Check what's changed since last session
git status
git log --oneline -5

# 2. See what's currently broken or in-progress
grep -r "TODO" hue_controller/ --include="*.py" | head -20
grep -r "FIXME" hue_controller/ --include="*.py"

# 3. Run the CLI to refresh your memory on current state
poetry run hue
# Try: help, lights, rooms, scenes

# 4. Test the wizards to see current UX
# From the CLI, try creating a scene to experience the flow
```

### Current Project State (Update This!)
<!-- Update this section whenever you make significant progress -->

**Last worked on**: December 2024

**Current focus**: Wizard system in `hue_controller/wizards/`

**What's working**:
- Basic CLI with natural language commands
- Bridge discovery and authentication
- Light/room/zone/scene control
- Initial wizard framework

**What's in progress**:
- Advanced scene wizard (`wizards/admin_scene_wizard.py`)
- Scene wizard components (`wizards/scene/`)
- UI components (`wizards/ui/`)
- Wizard templates (`wizards/templates/`)

**Known issues / Next steps**:
- Wizard UX needs improvement (see sections below)
- Advanced mode prompts lack context/descriptions
- No help system for terminology

### Key Files to Review
| File | Purpose |
|------|---------|
| `cli_interface.py` | Main REPL and command routing |
| `hue_controller/wizards/` | All wizard implementations |
| `hue_controller/command_interpreter.py` | Natural language parsing |
| `hue_controller/models.py` | Data structures for Hue resources |

---

## Wizard UI/UX Overhaul

### General Issues
- [ ] Current wizard (especially advanced mode) is not intuitive
- [ ] Terminology and jargon are not explained to users
- [ ] User flow feels disjointed rather than natural

### Improvements Needed
- [ ] Add contextual help/descriptions for every prompt
  - Explain what each setting does (e.g., "Mirek: Color temperature in micro reciprocal degrees, lower = cooler/bluer, higher = warmer/yellower")
  - Provide practical examples (e.g., "2700K feels like candlelight, 6500K feels like daylight")
- [ ] Show current values when editing existing resources
- [ ] Add visual feedback where possible (e.g., ASCII representations of color, brightness bars)
- [ ] Implement input validation with helpful error messages
- [ ] Add "back" and "cancel" options at every step
- [ ] Progress indicators for multi-step wizards

### Three Levels of Interaction
Design the UI to accommodate different user expertise levels:

1. **Simple Mode**
   - [ ] Preset-based selections (e.g., "Warm", "Cool", "Bright", "Dim")
   - [ ] Plain English options, no technical values exposed
   - [ ] Guided step-by-step with sensible defaults

2. **Standard Mode**
   - [ ] Balance of presets and manual control
   - [ ] Show technical values but with explanations
   - [ ] Allow skipping steps to use defaults

3. **Advanced Mode**
   - [ ] Full access to every API parameter
   - [ ] Raw value input with validation
   - [ ] Bulk operations and scripting support
   - [ ] Expert terminology (but still with help available on request)

---

## Full API Coverage

### Goal
Expose every possible Hue API v2 endpoint through an intuitive interface.

### Resources to Support
- [ ] **Lights**: All attributes (on/off, brightness, color, color temperature, effects, dynamics)
- [ ] **Rooms**: Creation, membership, grouped_light control
- [ ] **Zones**: Creation, membership, grouped_light control
- [ ] **Scenes**: Full CRUD, palette vs. actions, dynamic scenes
- [ ] **Smart Scenes**: Time-based scene automation
- [ ] **Entertainment Areas**: Configuration for sync/gaming
- [ ] **Schedules/Timers**: Automation rules
- [ ] **Behaviors**: Motion sensor behaviors, etc.
- [ ] **Device Power**: Power-on behavior settings
- [ ] **Bridge Settings**: Network, timezone, etc.

### Per-Resource Capabilities
For each resource type, ensure users can:
- [ ] List all instances with relevant details
- [ ] View full details of a single instance
- [ ] Create new instances with all available options
- [ ] Edit/update any attribute
- [ ] Delete instances
- [ ] Understand relationships (e.g., which lights are in which room)

---

## Documentation & Help System

### In-App Help
- [ ] `help <topic>` command for detailed explanations
- [ ] Glossary of Hue terminology accessible from CLI
- [ ] Tooltips/descriptions at every wizard prompt

### Terminology to Document
- [ ] **Mirek**: Color temperature unit (micro reciprocal degrees)
- [ ] **Gamut**: Color space/range a light can produce
- [ ] **CIE xy**: Color coordinate system used by Hue
- [ ] **Grouped Light**: Virtual light representing all lights in a room/zone
- [ ] **Dynamics**: Transition/animation settings for color changes
- [ ] **Signaling**: Light alerts (e.g., breathe, blink)
- [ ] **Gradient**: Multi-color capability on supported lights
- [ ] **Archetype**: Device category (e.g., sultan_bulb, spot_bulb)
- [ ] **Entertainment Area**: Low-latency sync zones for gaming/video
- [ ] **Recall/Active**: How scenes are triggered

---

## Natural Language via LLM

### Vision
Integrate an actual LLM to interpret complex natural language commands and execute them.

### Features
- [ ] Conversational scene creation ("Create a cozy evening scene with warm amber lights at 40% in the living room")
- [ ] Context-aware commands ("Make it a bit brighter", "Turn those off too")
- [ ] Ambiguity resolution via clarifying questions
- [ ] Natural descriptions of current state ("What's the living room like right now?")
- [ ] Complex multi-step operations from single commands

### Implementation Considerations
- [ ] Local vs. cloud LLM (privacy, latency, cost)
- [ ] Ollama integration for local inference
- [ ] OpenAI/Anthropic API for cloud option
- [ ] Structured output for reliable command parsing
- [ ] Fallback to current regex-based parser when LLM unavailable
- [ ] Rate limiting / token budget management

---

## Other Nice-to-Haves

### CLI Enhancements
- [ ] Tab completion for resource names
- [ ] Command aliases (user-definable shortcuts)
- [ ] Batch command files / scripting mode
- [ ] Output formatting options (JSON, table, minimal)
- [ ] Color-coded output for better readability

### State & Persistence
- [ ] Save/restore full bridge state snapshots
- [ ] Undo recent changes
- [ ] Favorites / quick-access saved commands
- [ ] Profile switching (e.g., "morning", "movie night")

### Monitoring & Events
- [ ] Real-time light status display (ncurses-style dashboard)
- [ ] Event log viewer for SSE stream
- [ ] Notifications for connectivity changes

### Automation
- [ ] Simple time-based schedules from CLI
- [ ] Sunrise/sunset-aware scheduling
- [ ] Integration with external triggers (webhooks, MQTT)

### Testing & Reliability
- [ ] Mock bridge for testing without hardware
- [ ] Comprehensive test suite for wizards
- [ ] Graceful handling of network issues

---

## Priority Suggestions

**High Priority** (most impact on usability):
1. Add descriptions/help to all wizard prompts
2. Implement the three-tier interaction model
3. Document all terminology in accessible glossary

**Medium Priority**:
4. Full API coverage for core resources
5. Tab completion and CLI polish
6. LLM integration prototype

**Lower Priority** (nice-to-have):
7. Advanced automation features
8. Real-time dashboard
9. External integrations

---

*Last updated: December 2024*
