import pygame
from water import WIDTH, HEIGHT, FPS

class MainMenu:
    """Simple title screen. Call run() → returns 'play', 'weapons', or 'quit'."""

    _BG      = (8,  25,  60)
    _TITLE   = (200, 230, 255)
    _BTN_BG  = (20,  60, 130)
    _BTN_HOV = (40, 100, 200)
    _BTN_TXT = (255, 255, 255)

    def __init__(self, width: int = WIDTH, height: int = HEIGHT, fps: int = FPS):
        if not pygame.get_init():
            pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Boat Simulator")
        self.clock  = pygame.time.Clock()
        self.fps    = fps
        self.W, self.H = width, height

        self._title_font = pygame.font.SysFont(None, 80)
        self._sub_font   = pygame.font.SysFont(None, 30)
        self._btn_font   = pygame.font.SysFont(None, 46)

    def run(self) -> str:
        btn_w, btn_h = 200, 56
        cx = self.W // 2
        
        # We now have 3 buttons, so we adjust their Y positions to fit nicely
        play_rect = pygame.Rect(cx - btn_w // 2, self.H // 2 - 20,  btn_w, btn_h)
        weap_rect = pygame.Rect(cx - btn_w // 2, self.H // 2 + 60,  btn_w, btn_h)
        quit_rect = pygame.Rect(cx - btn_w // 2, self.H // 2 + 140, btn_w, btn_h)

        while True:
            mx, my = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    return "play"
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if play_rect.collidepoint(mx, my):
                        return "play"
                    if weap_rect.collidepoint(mx, my):
                        return "weapons"  # This tells main.py to open the weapon menu
                    if quit_rect.collidepoint(mx, my):
                        return "quit"

            self.screen.fill(self._BG)

            # Animated wave hint — draw a few sine arcs
            for i in range(5):
                pts = []
                for px in range(0, self.W, 4):
                    import math
                    py = int(self.H * 0.78 + 18 * math.sin((px + i * 40) / 60.0))
                    pts.append((px, py))
                if len(pts) > 1:
                    pygame.draw.lines(self.screen, (30, 80, 160), False, pts, 2)

            # Title
            title = self._title_font.render("BOAT SIMULATOR", True, self._TITLE)
            self.screen.blit(title, (cx - title.get_width() // 2, self.H // 2 - 150))
            sub = self._sub_font.render("WASD/arrows to move  •  Click to splash", True, (130, 170, 220))
            self.screen.blit(sub, (cx - sub.get_width() // 2, self.H // 2 - 80))

            # Draw all three Buttons
            for rect, label in ((play_rect, "PLAY"), (weap_rect, "WEAPONS"), (quit_rect, "QUIT")):
                hov = rect.collidepoint(mx, my)
                pygame.draw.rect(self.screen, self._BTN_HOV if hov else self._BTN_BG,
                                 rect, border_radius=10)
                pygame.draw.rect(self.screen, self._BTN_TXT, rect, 2, border_radius=10)
                txt = self._btn_font.render(label, True, self._BTN_TXT)
                self.screen.blit(txt, (rect.centerx - txt.get_width() // 2,
                                       rect.centery - txt.get_height() // 2))

            pygame.display.flip()
            self.clock.tick(self.fps)