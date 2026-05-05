import pygame
import math
from water import WIDTH, HEIGHT, FPS
from weapon import Pistol, MachineGun, Sniper, Bazooka, Shotgun


def make_weapon(weapon_id: str):
    """Return a fresh Weapon instance from a weapon id string."""
    mapping = {
        "pistol":      Pistol,
        "machine_gun": MachineGun,
        "sniper":      Sniper,
        "bazooka":     Bazooka,
        "shotgun":     Shotgun,
    }
    return mapping.get(weapon_id, Pistol)()


class WeaponMenu:
    """Carousel weapon selection screen that auto-reads stats with custom descriptions."""

    _BG      = (8,  25,  60)
    _TITLE   = (200, 230, 255)
    _BTN_BG  = (20,  60, 130)
    _BTN_HOV = (40, 100, 200)
    _BTN_SEL = (80, 180, 80)
    _BTN_TXT = (255, 255, 255)
    _PANEL   = (15, 35, 80)

    WEAPON_CLASSES = [
        ("pistol",      Pistol,      "Just a basic pistol for basic combat."),
        ("machine_gun", MachineGun,  "Sprays bullets everywhere. Low accuracy."),
        ("sniper",      Sniper,      "Slow, but pierces enemies with massive damage."),
        ("bazooka",     Bazooka,     "Rest in peace my granny she got hit by a bazooka."),
        ("shotgun",     Shotgun,     "Deadly at close range. Spreads 7 pellets.")
    ]

    def __init__(self, current_weapon: str = "pistol", width: int = WIDTH, height: int = HEIGHT, fps: int = FPS):
        if not pygame.get_init():
            pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Select Weapon")
        self.clock  = pygame.time.Clock()
        self.fps    = fps
        self.W, self.H = width, height

        self.current_weapon = current_weapon

        self._title_font = pygame.font.SysFont(None, 60)
        self._name_font  = pygame.font.SysFont(None, 50)
        self._desc_font  = pygame.font.SysFont(None, 26)
        self._stat_font  = pygame.font.SysFont(None, 24)
        self._btn_font   = pygame.font.SysFont(None, 40)
        self._arrow_font = pygame.font.SysFont(None, 80)

        self._generate_weapon_data()

        self.view_index = 0
        for i, w in enumerate(self.weapon_data):
            if w["id"] == self.current_weapon:
                self.view_index = i
                break

    def _generate_weapon_data(self):
        self.weapon_data = []
        for w_id, w_class, custom_desc in self.WEAPON_CLASSES:
            w_inst = w_class()
            projs  = w_inst._make_projectiles(0, 0, 0)
            if not projs:
                continue
            p = projs[0]
            raw_dmg  = p.explosion_damage if p.explodes else p.damage
            raw_rate = w_class.fire_rate
            speed    = math.hypot(p.vx, p.vy)
            raw_range = p.shotgun_range if p.shotgun else (speed * p.lifetime)
            bar_dmg   = max(1, min(10, (raw_dmg  / 60.0)   * 10))
            bar_rate  = max(1, min(10, (raw_rate  / 10.0)   * 10))
            bar_range = max(1, min(10, (raw_range / 2100.0) * 10))
            self.weapon_data.append({
                "id":        w_id,
                "name":      w_id.replace("_", " ").upper(),
                "desc":      custom_desc,
                "bar_dmg":   bar_dmg,
                "bar_rate":  bar_rate,
                "bar_range": bar_range,
                "color":     p.color,
            })

    def _draw_stat_bar(self, x, y, label, bar_value, max_bar=10):
        txt = self._stat_font.render(label, True, (180, 200, 220))
        self.screen.blit(txt, (x, y))
        bar_x, bar_w, bar_h = x + 115, 150, 14
        pygame.draw.rect(self.screen, (30, 50, 90),   (bar_x, y + 2, bar_w, bar_h))
        pygame.draw.rect(self.screen, (80, 180, 255), (bar_x, y + 2, int(bar_w * (bar_value / max_bar)), bar_h))
        pygame.draw.rect(self.screen, (200, 220, 255),(bar_x, y + 2, bar_w, bar_h), 2)

    def run(self) -> str:
        cx, cy = self.W // 2, self.H // 2

        left_arrow_rect  = pygame.Rect(cx - 250, cy - 100, 60, 60)
        right_arrow_rect = pygame.Rect(cx + 190, cy - 100, 60, 60)
        equip_rect       = pygame.Rect(cx - 100, cy + 145, 200, 50)
        back_rect        = pygame.Rect(cx - 100, self.H - 80, 200, 50)

        while True:
            mx, my = pygame.mouse.get_pos()
            weapon     = self.weapon_data[self.view_index]
            is_equipped = (weapon["id"] == self.current_weapon)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return self.current_weapon
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return self.current_weapon
                    if event.key == pygame.K_LEFT:
                        self.view_index = (self.view_index - 1) % len(self.weapon_data)
                    if event.key == pygame.K_RIGHT:
                        self.view_index = (self.view_index + 1) % len(self.weapon_data)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if back_rect.collidepoint(mx, my):
                        return self.current_weapon
                    if left_arrow_rect.collidepoint(mx, my):
                        self.view_index = (self.view_index - 1) % len(self.weapon_data)
                    if right_arrow_rect.collidepoint(mx, my):
                        self.view_index = (self.view_index + 1) % len(self.weapon_data)
                    if equip_rect.collidepoint(mx, my):
                        self.current_weapon = weapon["id"]
                        is_equipped = True

            self.screen.fill(self._BG)

            # Header
            title = self._title_font.render("ARMORY", True, self._TITLE)
            self.screen.blit(title, (cx - title.get_width() // 2, 30))

            # Center panel
            panel_rect = pygame.Rect(cx - 300, cy - 220, 600, 440)
            pygame.draw.rect(self.screen, self._PANEL, panel_rect, border_radius=15)
            pygame.draw.rect(self.screen, (50, 90, 150), panel_rect, 3, border_radius=15)

            # Name
            name_txt = self._name_font.render(weapon["name"], True, (255, 255, 255))
            self.screen.blit(name_txt, (cx - name_txt.get_width() // 2, cy - 195))

            # Weapon art box (no player base model)
            art_rect = pygame.Rect(cx - 100, cy - 120, 200, 80)
            pygame.draw.rect(self.screen, (10, 20, 40), art_rect, border_radius=10)
            w_id = weapon["id"]

            if w_id == "pistol":
                pygame.draw.rect(self.screen, (70, 70, 75),      (cx - 40, cy - 105, 50, 25))
                pygame.draw.rect(self.screen, (100, 100, 105),   (cx + 10, cy - 105, 35, 20))
                pygame.draw.rect(self.screen, (160, 170, 180),   (cx + 45, cy - 105,  4, 20))
                pygame.draw.rect(self.screen, (40, 40, 45),      (cx - 40, cy - 80,  15, 30))
                for i in range(3):
                    pygame.draw.rect(self.screen, (80, 90, 100), (cx - 38, cy - 76 + i * 8, 11, 4))
                pygame.draw.rect(self.screen, (30, 30, 35),      (cx - 25, cy - 80,  12, 12))
                pygame.draw.rect(self.screen, (220, 50, 50),     (cx - 21, cy - 77,   3,  6))
                pygame.draw.rect(self.screen, (130, 130, 135),   (cx + 18, cy - 102,  5,  2))
                pygame.draw.rect(self.screen, (130, 130, 135),   (cx + 30, cy - 102,  5,  2))
                pygame.draw.circle(self.screen, (200, 210, 220), (cx - 32, cy - 48), 4, 2)

            elif w_id == "machine_gun":
                pygame.draw.rect(self.screen, (50, 50, 55),      (cx - 80, cy - 100, 20, 25), border_radius=2)
                pygame.draw.rect(self.screen, (30, 30, 35),      (cx - 68, cy - 108,  8, 10))
                pygame.draw.rect(self.screen, (55, 75, 95),      (cx - 60, cy - 105, 60, 45), border_radius=3)
                pygame.draw.rect(self.screen, (75, 95, 115),     (cx - 60, cy - 105, 50,  8))
                pygame.draw.rect(self.screen, (120, 135, 145),   (cx,      cy -  92, 80, 16))
                pygame.draw.rect(self.screen, (150, 165, 175),   (cx + 75, cy -  95, 10, 22), border_radius=1)
                for i in range(4):
                    pygame.draw.rect(self.screen, (40, 55, 65),  (cx + 10 + i * 15, cy - 88, 6, 8))
                pygame.draw.rect(self.screen, (45, 65, 85),      (cx - 35, cy -  60, 12, 12))
                pygame.draw.rect(self.screen, (30, 30, 30),      (cx - 55, cy -  48, 50,  5), border_radius=2)

            elif w_id == "sniper":
                pygame.draw.rect(self.screen, (210, 105, 30),    (cx - 95, cy -  95, 35, 20), border_radius=2)
                pygame.draw.rect(self.screen, (150, 75, 0),      (cx - 95, cy -  80, 10, 20), border_radius=2)
                pygame.draw.arc(self.screen,  (255, 215, 0),     (cx - 100, cy - 90, 15, 30), 3.14, 4.71, 2)
                pygame.draw.rect(self.screen, (205, 127, 50),    (cx - 60, cy - 100, 45, 38), border_radius=2)
                pygame.draw.rect(self.screen, (40, 40, 45),      (cx - 55, cy -  75, 12, 12))
                pygame.draw.rect(self.screen, (45, 45, 50),      (cx - 55, cy - 112, 40, 12), border_radius=1)
                pygame.draw.rect(self.screen, (100, 100, 110),   (cx - 40, cy - 118,  5,  6))
                pygame.draw.rect(self.screen, (140, 150, 160),   (cx - 15, cy -  93,110, 10))
                pygame.draw.rect(self.screen, (100, 110, 120),   (cx + 90, cy -  98,  8, 20))
                pygame.draw.rect(self.screen, (60, 60, 65),      (cx + 98, cy -  93,  6, 10))
                pygame.draw.rect(self.screen, (55, 70, 90),      (cx - 30, cy -  62, 12, 12))
                pygame.draw.rect(self.screen, (40, 50, 65),      (cx - 50, cy -  52, 50,  5), border_radius=2)

            elif w_id == "bazooka":
                pygame.draw.rect(self.screen, (100, 115, 130),   (cx - 85, cy -  95,170, 30), border_radius=2)
                pygame.draw.rect(self.screen, (60, 75, 90),      (cx - 95, cy - 100, 15, 40), border_radius=1)
                pygame.draw.rect(self.screen, (60, 75, 90),      (cx + 75, cy - 100, 15, 40), border_radius=1)
                pygame.draw.circle(self.screen, (200, 205, 210), (cx - 15, cy - 100), 10)
                pygame.draw.line(self.screen,  (200, 50, 50),    (cx - 15, cy - 100), (cx - 15, cy - 108), 2)
                pygame.draw.rect(self.screen, (30, 30, 35),      (cx +  5, cy - 112, 10, 18))
                pygame.draw.rect(self.screen, (0, 200, 255),     (cx + 12, cy - 110,  4,  4))
                pygame.draw.rect(self.screen, (150, 155, 160),   (cx + 50, cy -  90, 25, 20))
                pygame.draw.rect(self.screen, (200, 50, 50),     (cx + 70, cy -  83,  4,  6))
                pygame.draw.rect(self.screen, (55, 75, 95),      (cx - 45, cy -  65, 10, 20))
                pygame.draw.rect(self.screen, (55, 75, 95),      (cx +  5, cy -  65, 10, 20))
                pygame.draw.rect(self.screen, (30, 30, 35),      (cx - 55, cy -  45, 80,  6), border_radius=2)

            elif w_id == "shotgun":
                pygame.draw.rect(self.screen, (139, 69, 19),     (cx - 85, cy -  95, 30, 25), border_radius=2)
                pygame.draw.rect(self.screen, (100, 50, 15),     (cx - 85, cy -  85, 15, 20), border_radius=2)
                pygame.draw.rect(self.screen, (65, 65, 70),      (cx - 55, cy - 100, 45, 35), border_radius=2)
                pygame.draw.rect(self.screen, (45, 45, 50),      (cx - 55, cy -  85, 45,  4))
                pygame.draw.rect(self.screen, (100, 100, 105),   (cx - 10, cy -  95, 95, 16))
                pygame.draw.rect(self.screen, (140, 140, 145),   (cx - 10, cy -  95, 95,  4))
                pygame.draw.rect(self.screen, (75, 75, 80),      (cx - 10, cy -  79, 80,  8))
                for i in range(3):
                    pygame.draw.rect(self.screen, (180, 180, 185), (cx + 5 + i * 12, cy - 100, 6, 3))
                pygame.draw.rect(self.screen, (40, 40, 40),      (cx - 40, cy -  65, 10, 15))
                pygame.draw.rect(self.screen, (30, 30, 30),      (cx - 50, cy -  50, 30,  6), border_radius=2)

            # Description
            desc_txt = self._desc_font.render(weapon["desc"], True, (160, 220, 180))
            self.screen.blit(desc_txt, (cx - desc_txt.get_width() // 2, cy - 20))

            # Stats
            self._draw_stat_bar(cx - 135, cy + 25,  "DAMAGE",    weapon["bar_dmg"])
            self._draw_stat_bar(cx - 135, cy + 60,  "FIRE RATE", weapon["bar_rate"])
            self._draw_stat_bar(cx - 135, cy + 95,  "RANGE",     weapon["bar_range"])

            # Navigation arrows
            for rect, symbol in ((left_arrow_rect, "<"), (right_arrow_rect, ">")):
                hov   = rect.collidepoint(mx, my)
                color = self._TITLE if hov else (100, 130, 180)
                txt   = self._arrow_font.render(symbol, True, color)
                self.screen.blit(txt, (rect.centerx - txt.get_width() // 2,
                                       rect.centery - txt.get_height() // 2))

            # Equip button
            equip_hov   = equip_rect.collidepoint(mx, my)
            equip_color = self._BTN_SEL if is_equipped else (self._BTN_HOV if equip_hov else self._BTN_BG)
            equip_label = "EQUIPPED" if is_equipped else "EQUIP"
            pygame.draw.rect(self.screen, equip_color, equip_rect, border_radius=10)
            pygame.draw.rect(self.screen, self._BTN_TXT, equip_rect, 2, border_radius=10)
            eq_txt = self._btn_font.render(equip_label, True, self._BTN_TXT)
            self.screen.blit(eq_txt, (equip_rect.centerx - eq_txt.get_width() // 2,
                                      equip_rect.centery - eq_txt.get_height() // 2))

            # Back button
            back_hov = back_rect.collidepoint(mx, my)
            pygame.draw.rect(self.screen, self._BTN_HOV if back_hov else self._BTN_BG, back_rect, border_radius=10)
            pygame.draw.rect(self.screen, self._BTN_TXT, back_rect, 2, border_radius=10)
            bk_txt = self._btn_font.render("BACK", True, self._BTN_TXT)
            self.screen.blit(bk_txt, (back_rect.centerx - bk_txt.get_width() // 2,
                                      back_rect.centery - bk_txt.get_height() // 2))

            pygame.display.flip()
            self.clock.tick(self.fps)
