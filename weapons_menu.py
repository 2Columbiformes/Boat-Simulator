import pygame
import math
from weapon import Pistol, MachineGun, Sniper, Bazooka, Shotgun
from bullet import BulletVisual
from player_visual import PlayerVisual


_WEAPONS = [
    ("Pistol",       Pistol,      "Reliable single shot. Accurate, medium range."),
    ("Machine Gun",  MachineGun,  "Fast spray. Low accuracy, high rate of fire."),
    ("Sniper",       Sniper,      "Piercing beam. Slow rate, extreme range."),
    ("Bazooka",      Bazooka,     "Explosive rocket. Area damage, slow travel."),
    ("Shotgun",      Shotgun,     "7-pellet burst. Deadly close, weak at range."),
]

_WT_KEY = {
    "Pistol":      "pistol",
    "Machine Gun": "machine_gun",
    "Sniper":      "sniper",
    "Bazooka":     "bazooka",
    "Shotgun":     "shotgun",
}

BG     = (8,  25,  60)
PANEL  = (15, 40,  90)
ACCENT = (0,  180, 220)
WHITE  = (255, 255, 255)
GRAY   = (160, 160, 160)
GREEN  = (50,  220,  80)
ORANGE = (255, 160,  30)

_RANGE_NORM = 8000.0


class WeaponMenu:
    def __init__(self, width: int = 800, height: int = 600, fps: int = 60):
        self.screen   = pygame.display.get_surface()
        self.clock    = pygame.time.Clock()
        self.fps      = fps
        self.W, self.H = width, height
        self._idx     = 0
        self._tick    = 0   # animation counter
        self._font_title = pygame.font.SysFont(None, 64)
        self._font_name  = pygame.font.SysFont(None, 48)
        self._font_desc  = pygame.font.SysFont(None, 26)
        self._font_stat  = pygame.font.SysFont(None, 24)
        self._instances  = [cls() for _, cls, _ in _WEAPONS]

    def run(self) -> str:
        """Returns the selected weapon display name."""
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return _WEAPONS[self._idx][0]
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        self._idx = (self._idx - 1) % len(_WEAPONS)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self._idx = (self._idx + 1) % len(_WEAPONS)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                        return _WEAPONS[self._idx][0]
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx = event.pos[0]
                    if mx < self.W // 2 - 160:
                        self._idx = (self._idx - 1) % len(_WEAPONS)
                    elif mx > self.W // 2 + 160:
                        self._idx = (self._idx + 1) % len(_WEAPONS)
                    else:
                        return _WEAPONS[self._idx][0]

            self._tick += 1
            self._draw()
            pygame.display.flip()
            self.clock.tick(self.fps)

    # ── Layout constants ─────────────────────────────────────────────────────
    _TITLE_Y   = 28
    _NAME_Y    = 90
    _PREVIEW_Y = 140   # preview box top
    _PREVIEW_H = 90
    _DESC_Y    = 244
    _STATS_Y   = 272
    _STATS_H   = 120
    _ARROW_Y   = 410
    _DOTS_Y    = 455
    _HINT_Y    = 480

    def _draw(self):
        self.screen.fill(BG)
        name, _, desc = _WEAPONS[self._idx]
        inst = self._instances[self._idx]
        cx   = self.W // 2

        # ── Title
        t = self._font_title.render("CHOOSE WEAPON", True, (200, 230, 255))
        self.screen.blit(t, (cx - t.get_width() // 2, self._TITLE_Y))

        # ── Weapon name
        n = self._font_name.render(name, True, ACCENT)
        self.screen.blit(n, (cx - n.get_width() // 2, self._NAME_Y))

        # ── Live preview
        self._draw_preview(name, cx, self._PREVIEW_Y, self._PREVIEW_H)

        # ── Description
        d = self._font_desc.render(desc, True, GRAY)
        self.screen.blit(d, (cx - d.get_width() // 2, self._DESC_Y))

        # ── Stats panel
        panel_x = cx - 180
        pygame.draw.rect(self.screen, PANEL,
                         (panel_x, self._STATS_Y, 360, self._STATS_H), border_radius=10)
        pygame.draw.rect(self.screen, ACCENT,
                         (panel_x, self._STATS_Y, 360, self._STATS_H), 2, border_radius=10)
        sy = self._STATS_Y + 12
        for label, frac, color in self._get_stats(inst, name):
            lbl = self._font_stat.render(label, True, WHITE)
            self.screen.blit(lbl, (panel_x + 12, sy))
            bar_x, bar_w, bar_h = panel_x + 120, 220, 14
            pygame.draw.rect(self.screen, (40, 40, 40), (bar_x, sy, bar_w, bar_h))
            fill = max(2, int(bar_w * min(frac, 1.0)))
            pygame.draw.rect(self.screen, color, (bar_x, sy, fill, bar_h))
            pygame.draw.rect(self.screen, GRAY, (bar_x, sy, bar_w, bar_h), 1)
            sy += 26

        # ── Navigation arrows
        ay = self._ARROW_Y
        pygame.draw.polygon(self.screen, WHITE,
                            [(cx - 220, ay), (cx - 180, ay - 20), (cx - 180, ay + 20)])
        pygame.draw.polygon(self.screen, WHITE,
                            [(cx + 220, ay), (cx + 180, ay - 20), (cx + 180, ay + 20)])

        # ── Carousel dots
        for i in range(len(_WEAPONS)):
            c = ACCENT if i == self._idx else GRAY
            pygame.draw.circle(self.screen, c,
                               (cx - (len(_WEAPONS) - 1) * 14 + i * 28, self._DOTS_Y), 7)

        # ── Hint
        hint = self._font_desc.render("Click / ENTER to select  •  ← → to browse", True, GRAY)
        self.screen.blit(hint, (cx - hint.get_width() // 2, self._HINT_Y))

    def _draw_preview(self, name: str, cx: int, top: int, h: int):
        """Preview box: player boat (left) firing sample bullets (right)."""
        box_w = 360
        bx = cx - box_w // 2
        pygame.draw.rect(self.screen, (10, 30, 72), (bx, top, box_w, h), border_radius=8)
        pygame.draw.rect(self.screen, ACCENT,       (bx, top, box_w, h), 2, border_radius=8)

        wt     = _WT_KEY.get(name, "pistol")
        boat_x = bx + 60
        boat_y = top + h // 2

        # Boat with correct turret, pointing right (angle = 0)
        PlayerVisual.draw(self.screen, boat_x, boat_y, 0.0, wt, radius=int(0.8 * 52.0))

        # Animated bullets streaming from the barrel tip area
        #self._draw_preview_bullets(name, wt, bx, top, h, boat_x, boat_y)

    def _draw_preview_bullets(self, name, wt, bx, top, h, boat_x, boat_y):
        """Draw sample moving bullets in the preview box; animated via self._tick."""
        right_edge = bx + 360 - 8
        t = self._tick

        if name == "Shotgun":
            # 5 pellets fanning out from barrel
            spread_angles = [-0.25, -0.12, 0.0, 0.12, 0.25]
            for k, spread in enumerate(spread_angles):
                offset = ((t * 3 + k * 18) % 100)
                bul_x  = boat_x + 30 + offset
                bul_y  = boat_y + int(offset * math.tan(spread))
                if bx + 6 < bul_x < right_edge:
                    BulletVisual.draw(self.screen, bul_x, bul_y,
                                      (255, 140, 60), 3, (1, math.tan(spread)), False, wt)

        elif name == "Sniper":
            # Single long beam that sweeps across
            offset = (t * 5) % 110
            bul_x  = boat_x + 30 + offset
            if bx + 6 < bul_x < right_edge:
                BulletVisual.draw(self.screen, bul_x, boat_y,
                                  (180, 80, 255), 4, (200, 0), False, wt)

        elif name == "Machine Gun":
            # Fast small bursts, 3 bullets
            for k in range(3):
                offset = (t * 4 + k * 30) % 100
                bul_x  = boat_x + 30 + offset
                bul_y  = boat_y + (k - 1) * 2
                if bx + 6 < bul_x < right_edge:
                    BulletVisual.draw(self.screen, bul_x, bul_y,
                                      (255, 200, 80), 3, (100, 0), False, wt)

        elif name == "Bazooka":
            # Slow rocket
            offset = (t * 2) % 110
            bul_x  = boat_x + 30 + offset
            if bx + 6 < bul_x < right_edge:
                BulletVisual.draw(self.screen, bul_x, boat_y,
                                  (255, 100, 30), 6, (60, 0), False, wt)

        else:  # Pistol
            offset = (t * 3) % 100
            bul_x  = boat_x + 30 + offset
            if bx + 6 < bul_x < right_edge:
                BulletVisual.draw(self.screen, bul_x, boat_y,
                                  (200, 255, 220), 4, (100, 0), False, wt)

    def _get_stats(self, inst, name):
        fire_rate_frac = min(inst.fire_rate / 10.0, 1.0)
        stats_table = {
            "Pistol":       (20,  1000, 1000 * 2.5),
            "Machine Gun":  (8,   1120, 1120 * 1.8),
            "Sniper":       (55,  2800, 2800 * 3.0),
            "Bazooka":      (600, 640,  640  * 5.0),
            "Shotgun":      (30,  960,  1120.0),
        }
        dmg, spd, rng = stats_table.get(name, (20, 800, 1600))
        return [
            ("Fire Rate", fire_rate_frac,              GREEN),
            ("Damage",    min(dmg  / 600.0,  1.0),     ORANGE),
            ("Speed",     min(spd  / 3000.0, 1.0),     (100, 180, 255)),
            ("Range",     min(rng  / _RANGE_NORM, 1.0),(180, 100, 255)),
        ]


def make_weapon(name: str):
    """Return a fresh Weapon instance from a display name string."""
    mapping = {
        "Pistol":      Pistol,
        "Machine Gun": MachineGun,
        "Sniper":      Sniper,
        "Bazooka":     Bazooka,
        "Shotgun":     Shotgun,
    }
    return mapping.get(name, Pistol)()
