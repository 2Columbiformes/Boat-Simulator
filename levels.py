from dataclasses import dataclass, field
from water import GRID_W, GRID_H
from weapon import Pistol, MachineGun, Sniper, Shotgun, Bazooka


@dataclass
class LevelDef:
    name:          str
    player_start:  tuple
    flag_pos:      object       # (x, y) or None for survival levels
    obstacles:     list         # dicts: {"x", "y", "radius", "color"(opt)}
    enemies:       list         # dicts: {"type", "x", "y", "cx"(opt), "cy"(opt)}
    splashes:      list         # (gx, gy, amp, radius)
    survival:      bool  = False
    survival_secs: float = 120.0
    current_force: float = 80.0   # px/s² leftward (applied to player only)
    scroll_speed:  float = 4.0    # grid cells/s scrolled left visually
    player_weapon: object = None  # Weapon instance given to the player


# ── Level 1: Open Water ────────────────────────────────────────────────────────
level1 = LevelDef(
    name          = "Open Water",
    player_start  = (80, 300),
    flag_pos      = (700, 300),
    obstacles     = [
        {"x": 350, "y": 250, "radius": 20},
        {"x": 350, "y": 370, "radius": 20},
    ],
    enemies       = [
        {"type": "drift",  "x": 500, "y": 200},
        {"type": "patrol", "x": 500, "y": 420, "cx": 500, "cy": 400},
    ],
    splashes      = [
        (GRID_W // 2, GRID_H // 2, 2.0, 8),
    ],
    player_weapon = Pistol(),
)

# ── Level 2: The Gauntlet ──────────────────────────────────────────────────────
level2 = LevelDef(
    name          = "The Gauntlet",
    player_start  = (80, 300),
    flag_pos      = (720, 300),
    obstacles     = [
        # Wall 1 at x=280 — blocks top and bottom, gap in the middle
        {"x": 280, "y": 100, "radius": 18},
        {"x": 280, "y": 190, "radius": 18},
        {"x": 280, "y": 410, "radius": 18},
        {"x": 280, "y": 500, "radius": 18},
        # Wall 2 at x=480 — offset gaps
        {"x": 480, "y":  80, "radius": 18},
        {"x": 480, "y": 200, "radius": 18},
        {"x": 480, "y": 360, "radius": 18},
        {"x": 480, "y": 480, "radius": 18},
    ],
    enemies       = [
        {"type": "chase", "x": 160, "y": 130},
        {"type": "chase", "x": 160, "y": 470},
        {"type": "snipe", "x": 600, "y": 300},
    ],
    splashes      = [
        (GRID_W // 3,     GRID_H // 3,     1.5, 6),
        (GRID_W * 2 // 3, GRID_H * 2 // 3, 1.5, 6),
    ],
    player_weapon = MachineGun(),
)

# ── Level 3: Crossfire ─────────────────────────────────────────────────────────
level3 = LevelDef(
    name          = "Crossfire",
    player_start  = (80, 500),
    flag_pos      = (700, 100),
    obstacles     = [
        {"x": 380, "y": 270, "radius": 25},
        {"x": 430, "y": 330, "radius": 25},
        {"x": 200, "y": 200, "radius": 18},
        {"x": 600, "y": 400, "radius": 18},
    ],
    enemies       = [
        {"type": "snipe",     "x": 700, "y": 500},
        {"type": "snipe",     "x": 100, "y": 100},
        {"type": "artillery", "x": 400, "y": 300},
        {"type": "drift",     "x": 400, "y": 150},
    ],
    splashes      = [
        (GRID_W // 4, GRID_H // 4, 2.0, 8),
        (GRID_W * 3 // 4, GRID_H * 3 // 4, 1.5, 6),
    ],
    player_weapon = Sniper(),
)

# ── Level 4: The Maze ──────────────────────────────────────────────────────────
level4 = LevelDef(
    name          = "The Maze",
    player_start  = (60, 60),
    flag_pos      = (720, 520),
    obstacles     = [
        # S-curve column 1 at x=200 — blocks most of the height except ~y=300
        {"x": 200, "y": 100, "radius": 20},
        {"x": 200, "y": 180, "radius": 20},
        {"x": 200, "y": 380, "radius": 20},
        {"x": 200, "y": 460, "radius": 20},
        # S-curve column 2 at x=440 — gap near y=220 instead
        {"x": 440, "y": 120, "radius": 20},
        {"x": 440, "y": 320, "radius": 20},
        {"x": 440, "y": 400, "radius": 20},
        {"x": 440, "y": 520, "radius": 20},
        # Flanking guards
        {"x": 640, "y": 300, "radius": 22},
        {"x": 340, "y": 520, "radius": 20},
    ],
    enemies       = [
        {"type": "chase",     "x": 300, "y": 300},
        {"type": "patrol",    "x": 600, "y": 200, "cx": 600, "cy": 200},
        {"type": "snipe",     "x": 700, "y": 400},
        {"type": "artillery", "x": 400, "y": 500},
        {"type": "drift",     "x": 550, "y": 100},
    ],
    splashes      = [
        (GRID_W // 4, GRID_H // 4, 2.0, 7),
        (GRID_W * 3 // 4, GRID_H // 2, 1.8, 7),
    ],
    player_weapon = Shotgun(),
)

# ── Level 5: River of No Return (survival) ─────────────────────────────────────
level5 = LevelDef(
    name          = "No Return",
    player_start  = (650, 300),
    flag_pos      = None,       # win by surviving
    obstacles     = [],
    enemies       = [
        {"type": "drift",  "x": 500, "y": 150},
        {"type": "drift",  "x": 500, "y": 450},
        {"type": "chase",  "x": 400, "y": 300},
        {"type": "patrol", "x": 300, "y": 200, "cx": 300, "cy": 200},
        {"type": "snipe",  "x": 600, "y": 100},
    ],
    splashes      = [
        (GRID_W * 3 // 4, GRID_H // 2, 2.5, 10),
    ],
    survival      = True,
    survival_secs = 120.0,
    current_force = 90.0,
    scroll_speed  = 5.0,
    player_weapon = Bazooka(),
)


LEVELS: list = [level1, level2, level3, level4, level5]
