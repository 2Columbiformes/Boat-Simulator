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
    survival_secs: float = 60.0
    current_force: float = 80.0   # px/s² leftward (applied to player only)
    scroll_speed:  float = 4.0    # grid cells/s scrolled left visually
    player_weapon: object = None  # Weapon instance given to the player
    enemy_budget: int = 0
    spawn_pool: list = None
    topology:            str  = "torus"   # "torus" = wrap edges; "bounded" = wall bounce
    entity_barriers:    bool = False     # True = entities bounce at world edges; bullets still wrap
    no_obstacle_damage: bool = False     # True = entities take no damage from hitting obstacles
    obstacle_factory: object = None     # callable() -> (obstacles, enemies); called fresh each replay


# All coordinates are in world space (800 × 600 — world matches screen).

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
        (GRID_W // 2, GRID_H // 2, 0.02, 4),
    ],
    player_weapon   = Pistol(),
    entity_barriers = True,
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
        {"type": "chase", "x": 160, "y": 130},
        {"type": "chase", "x": 160, "y": 470},
    ],
    splashes      = [
        (GRID_W // 3,     GRID_H // 3,     0.015, 3),
        (GRID_W * 2 // 3, GRID_H * 2 // 3, 0.015, 3),
    ],
    player_weapon   = MachineGun(),
    entity_barriers = True,
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
        {"type": "snipe",     "x": 700, "y": 500},
        {"type": "snipe",     "x": 100, "y": 100},
        {"type": "artillery", "x": 400, "y": 300},
        {"type": "artillery", "x": 400, "y": 300},
        {"type": "artillery", "x": 400, "y": 300},
        {"type": "drift",     "x": 400, "y": 150},
        {"type": "drift",     "x": 400, "y": 450},
    ],
    splashes      = [
        (GRID_W // 4,     GRID_H // 4,     0.02, 4),
        (GRID_W * 3 // 4, GRID_H * 3 // 4, 0.015, 3),
    ],
    player_weapon   = Sniper(),
    entity_barriers = True,
)


# ── Level 4: The Maze (procedural) ─────────────────────────────────────────────
import random

def _generate_maze(width, height):
    # Ensure odd dimensions
    if width % 2 == 0:
        width += 1
    if height % 2 == 0:
        height += 1

    maze = [[1 for _ in range(width)] for _ in range(height)]

    def carve(x, y):
        directions = [(2,0), (-2,0), (0,2), (0,-2)]
        random.shuffle(directions)

        for dx, dy in directions:
            nx, ny = x + dx, y + dy

            if 1 <= nx < width - 1 and 1 <= ny < height - 1:
                if maze[ny][nx] == 1:
                    maze[ny][nx] = 0
                    maze[y + dy//2][x + dx//2] = 0
                    carve(nx, ny)

    maze[1][1] = 0
    carve(1, 1)

    # Ensure start and end are open
    maze[1][1] = 0
    maze[-2][-2] = 0

    return maze


def _maze_to_obstacles(maze, cell_size=50):
    obstacles = []
    for r in range(len(maze)):
        for c in range(len(maze[0])):
            if maze[r][c] == 1:
                x = c * cell_size + cell_size // 2
                y = r * cell_size + cell_size // 2

                obstacles.append({
                    "x": x,
                    "y": y,
                    "radius": int(cell_size * 0.45),
                    "hp": 10**9,
                })
    return obstacles


def _cell_to_world(r, c, cell_size=50):
    return (
        c * cell_size + cell_size // 2,
        r * cell_size + cell_size // 2
    )


def _get_open_cells(maze):
    cells = []
    for r in range(len(maze)):
        for c in range(len(maze[0])):
            if maze[r][c] == 0:
                cells.append((r, c))
    return cells


# Match world (800 x 600): 15×50=750 wide, 11×50=550 tall
cell_size = 50
cols = 15  # must be odd
rows = 11  # must be odd


def _make_maze_data():
    """Generate a fresh random maze layout each call."""
    maze  = _generate_maze(cols, rows)
    obs   = _maze_to_obstacles(maze, cell_size)
    cells = _get_open_cells(maze)
    enems = []
    for r, c in random.sample(cells, min(6, len(cells))):
        x, y = _cell_to_world(r, c, cell_size)
        enems.append({
            "type": random.choice(["chase", "patrol", "drift"]),
            "x": x,
            "y": y,
        })
    return obs, enems


level4 = LevelDef(
    name             = "The Maze",
    player_start     = (cell_size + 40, cell_size + 40),
    flag_pos         = ((cols - 2) * cell_size, (rows - 2) * cell_size),
    obstacles        = [],   # filled fresh each replay by obstacle_factory
    enemies          = [],
    splashes         = [],
    player_weapon       = Shotgun(),
    obstacle_factory    = _make_maze_data,
    entity_barriers     = True,
    no_obstacle_damage  = True,
)

# ── Level 5: River of No Return (survival) ─────────────────────────────────────
level5 = LevelDef(
    name          = "No Return",
    player_start  = (650, 300),
    flag_pos      = None,           # win by surviving
    obstacles     = [
        {"x": 400, "y": 300, "radius": 35},   # central island
    ],
    enemies       = [
        {"type": "boss",      "x": 400, "y": 100},
        {"type": "chase",     "x": 400, "y": 300},
        {"type": "chase",     "x": 400, "y": 300},
        {"type": "chase",     "x": 400, "y": 300},
        {"type": "patrol",    "x": 300, "y": 200, "cx": 300, "cy": 200},
        {"type": "patrol",    "x": 300, "y": 200, "cx": 300, "cy": 200},
        {"type": "snipe",     "x": 600, "y": 100},
        {"type": "artillery", "x": 400, "y": 300},
        {"type": "artillery", "x": 400, "y": 300},
    ],
    splashes      = [
        (GRID_W * 3 // 4, GRID_H // 2, 0.02, 4),
    ],
    survival      = True,
    survival_secs = 60.0,
    current_force = 0.0,
    scroll_speed  = 0.0,
    player_weapon = Bazooka(),
)


LEVELS: list = [level1, level2, level3, level4, level5]
