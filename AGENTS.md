# AGENTS.md - Pygame Platformer Shooter

## Project Overview

Single-file Pygame-ce platformer shooter game. The codebase consists of `APIVersion1.13.py` containing all game logic, entities, and level design.

---

## Build & Run Commands

### Running the Game
```bash
python APIVersion1.13.py
```
Requires `pygame-ce` (Pygame community edition):
```bash
pip install pygame-ce
```

### Development Tools (Optional)

Install linting and type checking:
```bash
pip install ruff mypy
```

Run linter:
```bash
ruff check APIVersion1.13.py
```

Run type checker:
```bash
mypy APIVersion1.13.py
```

---

## Code Style Guidelines

### File Organization
- Single file architecture - all code in `APIVersion1.13.py`
- Sections marked with comment headers: `# --- SECTION NAME ---`
- Order: imports, constants, globals, functions, classes, main()

### Imports
```python
import pygame
import random
```
- Standard library imports first, then third-party
- Use `pygame.Vector2` for positions/velocities
- Use `pygame.Rect` for collision detection

### Naming Conventions
| Element | Convention | Example |
|---------|------------|---------|
| Classes | PascalCase | `class Player:` |
| Constants | CAPS_SNAKE_CASE | `SCREEN_WIDTH = 800` |
| Colors | COLOR_* prefix | `COLOR_BG = (15, 15, 15)` |
| Functions | snake_case | `def update_camera(player_pos):` |
| Variables | snake_case | `camera_offset` |

### Class Structure
Follow this pattern for game entities:
```python
class EntityName:
    def __init__(self, params):
        # Initialize state

    def update(self, params):
        # Game logic, physics, AI
        pass

    def draw(self, surface):
        # Rendering logic
        pass
```

### Types
- Use type hints for function parameters and return types where beneficial
- Prefer explicit types over `Any`
- Pygame types: `pygame.Vector2`, `pygame.Rect`, `pygame.Surface`

### Functions
- Keep functions under 50 lines
- Use descriptive names: `apply_camera()` not `cam()`
- Single responsibility per function

### Formatting
- Line length: 120 characters max
- Indentation: 4 spaces
- No trailing whitespace
- One blank line between top-level definitions

### Error Handling
- Let Pygame exceptions propagate (game cannot run without display)
- Use defensive checks for game logic edge cases
- No logging framework currently - use print for debugging

### Comments
- Russian comments used throughout existing codebase
- Comment sections: `# --- SECTION NAME ---`
- Inline comments for complex logic: `self.vel_y += 0.7  # gravity`

### Game Loop Pattern
```python
def main():
    # Initialize
    while True:
        # Handle events
        # Update game state
        # Draw frame
        clock.tick(FPS)
```

### Constants
- Screen: `SCREEN_WIDTH`, `SCREEN_HEIGHT`, `FPS`
- Colors: `COLOR_*` tuple constants (RGB)
- Physics: inline magic numbers acceptable (e.g., gravity=0.7)

### Testing
- No formal test framework
- Manual testing via gameplay
- Test edge cases: collision detection, AI pathfinding, win condition

---

## Important Implementation Details

### Coordinate System
- Y increases downward (standard Pygame)
- Camera follows player with smooth interpolation (lerp factor 0.1)

### Entity Update Order
1. Player movement
2. Camera update
3. Portal spawning
4. Enemy AI
5. Laser updates & collision

### Win Condition
Game won when all portals destroyed AND no enemies remain.

### Controls
- `W` - Jump
- `A`/`D` - Move left/right
- Mouse click - Shoot laser

---

## Cursor/Copilot Rules

No custom rules found. If adding rules, place in:
- `.cursor/rules/` for Cursor
- `.cursorrules` in root
- `.github/copilot-instructions.md` for Copilot
