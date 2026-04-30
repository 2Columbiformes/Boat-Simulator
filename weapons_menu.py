import pygame
import math
from water import WIDTH, HEIGHT, FPS

# Import your actual weapons so we can read their stats!
from weapon import Pistol, MachineGun, Sniper, Bazooka, Shotgun

class WeaponMenu:
    """Carousel weapon selection screen that auto-reads stats with custom descriptions."""

    _BG      = (8,  25,  60)
    _TITLE   = (200, 230, 255)
    _BTN_BG  = (20,  60, 130)
    _BTN_HOV = (40, 100, 200)
    _BTN_SEL = (80, 180, 80)
    _BTN_TXT = (255, 255, 255)
    _PANEL   = (15, 35, 80)

    # TYPE YOUR CUSTOM DESCRIPTIONS HERE! 
    # Keep them somewhat brief so they fit nicely on the screen.
    WEAPON_CLASSES = [
        ("pistol", Pistol, "Just your basic pistol shooting basic bullets."),
        ("machine_gun", MachineGun, "Sprays bullets everywhere. Low accuracy."),
        ("sniper", Sniper, "Slow, but pierces enemies with massive damage."),
        ("bazooka", Bazooka, "Fires an explosive shell. Watch the blast radius!"),
        ("shotgun", Shotgun, "Deadly at close range. Weak at long range.")
    ]

    def __init__(self, current_weapon: str, width: int = WIDTH, height: int = HEIGHT, fps: int = FPS):
        if not pygame.get_init():
            pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Select Weapon")
        self.clock = pygame.time.Clock()
        self.fps = fps
        self.W, self.H = width, height

        self.current_weapon = current_weapon
        
        self._title_font = pygame.font.SysFont(None, 60)
        self._name_font  = pygame.font.SysFont(None, 50)
        self._desc_font  = pygame.font.SysFont(None, 26) # Font for the description
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
        """Silently fires a dummy projectile to auto-calculate stats for the UI."""
        self.weapon_data = []
        
        # Now loops through 3 items to grab your custom description!
        for w_id, w_class, custom_desc in self.WEAPON_CLASSES:
            w_inst = w_class()
            projs = w_inst._make_projectiles(0, 0, 0)
            
            if not projs:
                continue
                
            p = projs[0] 

            raw_dmg = p.explosion_damage if p.explodes else p.damage
            raw_rate = w_class.fire_rate
            
            speed = math.hypot(p.vx, p.vy)
            raw_range = p.shotgun_range if p.shotgun else (speed * p.lifetime)

            bar_dmg   = max(1, min(10, (raw_dmg / 60.0) * 10))
            bar_rate  = max(1, min(10, (raw_rate / 10.0) * 10))
            bar_range = max(1, min(10, (raw_range / 2100.0) * 10))
            
            self.weapon_data.append({
                "id": w_id,
                "name": w_id.replace("_", " ").upper(),
                "desc": custom_desc, # Uses your typed text here
                "bar_dmg": bar_dmg,
                "bar_rate": bar_rate,
                "bar_range": bar_range,
                "color": p.color 
            })

    def _draw_stat_bar(self, x, y, label, bar_value, max_bar=10):
        """Draws the stat text and the progress bar (numbers removed)."""
        txt = self._stat_font.render(label, True, (180, 200, 220))
        self.screen.blit(txt, (x, y))
        
        bar_x = x + 115
        bar_w = 150
        bar_h = 14
        pygame.draw.rect(self.screen, (30, 50, 90), (bar_x, y + 2, bar_w, bar_h)) 
        pygame.draw.rect(self.screen, (80, 180, 255), (bar_x, y + 2, int(bar_w * (bar_value / max_bar)), bar_h)) 
        pygame.draw.rect(self.screen, (200, 220, 255), (bar_x, y + 2, bar_w, bar_h), 2) 

    def run(self) -> str:
        cx, cy = self.W // 2, self.H // 2

        left_arrow_rect  = pygame.Rect(cx - 250, cy - 100, 60, 60)
        right_arrow_rect = pygame.Rect(cx + 190, cy - 100, 60, 60)
        equip_rect       = pygame.Rect(cx - 100, cy + 145, 200, 50)
        back_rect        = pygame.Rect(cx - 100, self.H - 80, 200, 50)

        while True:
            mx, my = pygame.mouse.get_pos()
            
            weapon = self.weapon_data[self.view_index]
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

            self.screen.fill(self._BG)

            # --- HEADER ---
            title = self._title_font.render("ARMORY", True, self._TITLE)
            self.screen.blit(title, (cx - title.get_width() // 2, 30))

            # --- CENTER PANEL ---
            panel_rect = pygame.Rect(cx - 300, cy - 220, 600, 440)
            pygame.draw.rect(self.screen, self._PANEL, panel_rect, border_radius=15)
            pygame.draw.rect(self.screen, (50, 90, 150), panel_rect, 3, border_radius=15)

            # Name
            name_txt = self._name_font.render(weapon["name"], True, (255, 255, 255))
            self.screen.blit(name_txt, (cx - name_txt.get_width() // 2, cy - 195))

            # Visual Box
            art_rect = pygame.Rect(cx - 120, cy - 140, 240, 100)
            pygame.draw.rect(self.screen, (10, 20, 40), art_rect, border_radius=10)
            pygame.draw.ellipse(self.screen, weapon["color"], (cx - 60, cy - 100, 120, 30))
            pygame.draw.rect(self.screen, weapon["color"], (cx - 40, cy - 85, 20, 40)) 

            # Custom Typed Description
            desc_txt = self._desc_font.render(weapon["desc"], True, (160, 220, 180))
            self.screen.blit(desc_txt, (cx - desc_txt.get_width() // 2, cy - 20))

            # Auto-Stats
            self._draw_stat_bar(cx - 135, cy + 25, "DAMAGE", weapon["bar_dmg"])
            self._draw_stat_bar(cx - 135, cy + 60, "FIRE RATE", weapon["bar_rate"])
            self._draw_stat_bar(cx - 135, cy + 95, "RANGE", weapon["bar_range"])

            # --- NAVIGATION ARROWS ---
            for rect, symbol in ((left_arrow_rect, "<"), (right_arrow_rect, ">")):
                hov = rect.collidepoint(mx, my)
                color = self._TITLE if hov else (100, 130, 180)
                txt = self._arrow_font.render(symbol, True, color)
                self.screen.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))

            # --- EQUIP BUTTON ---
            equip_hov = equip_rect.collidepoint(mx, my)
            if is_equipped:
                equip_color = self._BTN_SEL
                equip_label = "EQUIPPED"
            else:
                equip_color = self._BTN_HOV if equip_hov else self._BTN_BG
                equip_label = "EQUIP"

            pygame.draw.rect(self.screen, equip_color, equip_rect, border_radius=10)
            pygame.draw.rect(self.screen, self._BTN_TXT, equip_rect, 2, border_radius=10)
            eq_txt = self._btn_font.render(equip_label, True, self._BTN_TXT)
            self.screen.blit(eq_txt, (equip_rect.centerx - eq_txt.get_width() // 2, equip_rect.centery - eq_txt.get_height() // 2))

            # --- BACK BUTTON ---
            back_hov = back_rect.collidepoint(mx, my)
            pygame.draw.rect(self.screen, self._BTN_HOV if back_hov else self._BTN_BG, back_rect, border_radius=10)
            pygame.draw.rect(self.screen, self._BTN_TXT, back_rect, 2, border_radius=10)
            bk_txt = self._btn_font.render("BACK", True, self._BTN_TXT)
            self.screen.blit(bk_txt, (back_rect.centerx - bk_txt.get_width() // 2, back_rect.centery - bk_txt.get_height() // 2))

            pygame.display.flip()
            self.clock.tick(self.fps)