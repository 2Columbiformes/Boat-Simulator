from dataclasses import dataclass
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


# All coordinates are in world space (3200 × 2400), scaled 4× from the old 800×600 screen.

# ── Level 1: Open Water ────────────────────────────────────────────────────────
level1 = LevelDef(
    name          = "Open Water",
    player_start  = (320, 1200),
    flag_pos      = (2800, 1200),
    obstacles     = [
        {"x": 1400, "y": 1000, "radius": 80},
        {"x": 1400, "y": 1480, "radius": 80},
    ],
    enemies       = [
        {"type": "drift",  "x": 2000, "y":  800},
        {"type": "patrol", "x": 2000, "y": 1680, "cx": 2000, "cy": 1600},
    ],
    splashes      = [
        (GRID_W // 2, GRID_H // 2, 2.0, 8),
    ],
    player_weapon = Pistol(),
)

# ── Level 2: The Gauntlet ──────────────────────────────────────────────────────
level2 = LevelDef(
    name          = "The Gauntlet",
    player_start  = (320, 1200),
    flag_pos      = (2880, 1200),
    obstacles     = [
        # Wall 1 at x=1120 — blocks top and bottom, gap in the middle
        {"x": 1120, "y":  400, "radius": 72},
        {"x": 1120, "y":  760, "radius": 72},
        {"x": 1120, "y": 1640, "radius": 72},
        {"x": 1120, "y": 2000, "radius": 72},
        # Wall 2 at x=1920 — offset gaps
        {"x": 1920, "y":  320, "radius": 72},
        {"x": 1920, "y":  800, "radius": 72},
        {"x": 1920, "y": 1440, "radius": 72},
        {"x": 1920, "y": 1920, "radius": 72},
    ],
    enemies       = [
        {"type": "chase", "x":  640, "y":  520},
        {"type": "chase", "x":  640, "y": 1880},
        {"type": "snipe", "x": 2400, "y": 1200},
        {"type": "chase", "x":  640, "y":  520},
        {"type": "chase", "x":  640, "y": 1880},
        {"type": "snipe", "x": 2400, "y": 1200},
        {"type": "chase", "x":  640, "y":  520},
        {"type": "chase", "x":  640, "y": 1880},
        {"type": "snipe", "x": 2400, "y": 1200},
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
    player_start  = (320, 2000),
    flag_pos      = (2800,  400),
    obstacles     = [
        {"x": 1520, "y": 1080, "radius": 100},
        {"x": 1720, "y": 1320, "radius": 100},
        {"x":  800, "y":  800, "radius":  72},
        {"x": 2400, "y": 1600, "radius":  72},
    ],
    enemies       = [
        {"type": "snipe",     "x": 2800, "y": 2000},
        {"type": "snipe",     "x":  400, "y":  400},
        {"type": "artillery", "x": 1600, "y": 1200},
        {"type": "drift",     "x": 1600, "y":  600},
        {"type": "chase", "x":  640, "y":  520},
        {"type": "chase", "x":  640, "y": 1880},
        {"type": "snipe", "x": 2400, "y": 1200},
        {"type": "chase", "x":  640, "y":  520},
        {"type": "chase", "x":  640, "y": 1880},
        {"type": "snipe", "x": 2400, "y": 1200},
        {"type": "chase", "x":  640, "y":  520},
        {"type": "chase", "x":  640, "y": 1880},
        {"type": "snipe", "x": 2400, "y": 1200},
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
    player_start  = (240,  240),
    flag_pos      = (2880, 2080),
    obstacles     = [
        # Grid at 400-px spacing, r=60.  (400,400) and (2800,2000) omitted to
        # keep player start (240,240) and flag approach (2880,2080) clear.
        {"x":  800, "y":  400, "radius": 60},
        {"x": 1200, "y":  400, "radius": 60},
        {"x": 1600, "y":  400, "radius": 60},
        {"x": 2000, "y":  400, "radius": 60},
        {"x": 2400, "y":  400, "radius": 60},
        {"x": 2800, "y":  400, "radius": 60},
        {"x":  400, "y":  800, "radius": 60},
        {"x":  800, "y":  800, "radius": 60},
        {"x": 1200, "y":  800, "radius": 60},
        {"x": 1600, "y":  800, "radius": 60},
        {"x": 2000, "y":  800, "radius": 60},
        {"x": 2400, "y":  800, "radius": 60},
        {"x": 2800, "y":  800, "radius": 60},
        {"x":  400, "y": 1200, "radius": 60},
        {"x":  800, "y": 1200, "radius": 60},
        {"x": 1200, "y": 1200, "radius": 60},
        {"x": 1600, "y": 1200, "radius": 60},
        {"x": 2000, "y": 1200, "radius": 60},
        {"x": 2400, "y": 1200, "radius": 60},
        {"x": 2800, "y": 1200, "radius": 60},
        {"x":  400, "y": 1600, "radius": 60},
        {"x":  800, "y": 1600, "radius": 60},
        {"x": 1200, "y": 1600, "radius": 60},
        {"x": 1600, "y": 1600, "radius": 60},
        {"x": 2000, "y": 1600, "radius": 60},
        {"x": 2400, "y": 1600, "radius": 60},
        {"x": 2800, "y": 1600, "radius": 60},
        {"x":  400, "y": 2000, "radius": 60},
        {"x":  800, "y": 2000, "radius": 60},
        {"x": 1200, "y": 2000, "radius": 60},
        {"x": 1600, "y": 2000, "radius": 60},
        {"x": 2000, "y": 2000, "radius": 60},
        {"x": 2400, "y": 2000, "radius": 60},
    ],
    enemies       = [
        {"type": "chase",     "x": 1200, "y": 1200},
        {"type": "chase",     "x": 1200, "y": 1200},
        {"type": "chase",     "x": 1200, "y": 1200},
        {"type": "chase",     "x": 1200, "y": 1200},
        {"type": "chase",     "x": 1200, "y": 1200},
        {"type": "chase",     "x": 1200, "y": 1200},
        {"type": "patrol",    "x": 2400, "y":  800, "cx": 2400, "cy":  800},
        {"type": "snipe",     "x": 2800, "y": 1600},
        {"type": "artillery", "x": 1600, "y": 2000},
        {"type": "drift",     "x": 2200, "y":  400},
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
    player_start  = (2600, 1200),
    flag_pos      = None,           # win by surviving
    obstacles     = [],
    enemies       = [
        {"type": "chase",  "x": 1600, "y": 1200},
        {"type": "chase",  "x": 1600, "y": 1200},
        {"type": "chase",  "x": 1600, "y": 1200},
        {"type": "chase",  "x": 1600, "y": 1200},
        {"type": "chase",  "x": 1600, "y": 1200},
        {"type": "chase",  "x": 1600, "y": 1200},
        {"type": "chase",  "x": 1600, "y": 1200},
        {"type": "patrol", "x": 1200, "y":  800, "cx": 1200, "cy":  800},
        {"type": "snipe",  "x": 2400, "y":  400},
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
