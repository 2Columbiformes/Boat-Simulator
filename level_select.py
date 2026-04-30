import pygame
from water import WIDTH, HEIGHT, FPS

DARK_GRAY = ( 80,  80,  80)
BLUE      = ( 20,  60, 130)
BLUE_HOV  = ( 40, 100, 200)
BLACK     = (  0,   0,   0)
WHITE     = (255, 255, 255)
BG        = (  8,  25,  60)


class Button:
    def __init__(self, x: int, y: int, w: int, h: int,
                 text: str, unlocked: bool = True):
        self.rect     = pygame.Rect(x, y, w, h)
        self.text     = text
        self.unlocked = unlocked

    def draw(self, surface: pygame.Surface, font: pygame.font.Font,
             mx: int, my: int):
        hov   = self.unlocked and self.rect.collidepoint(mx, my)
        color = DARK_GRAY if not self.unlocked else (BLUE_HOV if hov else BLUE)
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, BLACK, self.rect, 2, border_radius=8)
        label = self.text if self.unlocked else "LOCKED"
        txt   = font.render(label, True, WHITE)
        surface.blit(txt, (self.rect.centerx - txt.get_width()  // 2,
                           self.rect.centery - txt.get_height() // 2))

    def is_clicked(self, event: pygame.event.Event) -> bool:
        return (self.unlocked
                and event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.rect.collidepoint(event.pos))


class LevelSelect:
    """Level-selection screen.  Call run() → returns 0-based level index or -1."""

    def __init__(self, level_names: list,
                 levels_unlocked: int = 1,
                 width: int = WIDTH, height: int = HEIGHT):
        if not pygame.get_init():
            pygame.init()
        self.screen = pygame.display.get_surface() or pygame.display.set_mode((width, height))
        self.clock  = pygame.time.Clock()
        self._font        = pygame.font.SysFont(None, 36)
        self._title_font  = pygame.font.SysFont(None, 60)
        self._width  = width
        self._height = height

        positions = list(self._layout(level_names, width, height))
        self._buttons = [
            Button(x, y, 200, 70, name, i < levels_unlocked)
            for i, (name, x, y) in enumerate(positions)
        ]
        self._back = Button(30, height - 70, 120, 48, "BACK", unlocked=True)

    @staticmethod
    def _layout(names: list, W: int, H: int):
        """Yield (name, x, y) for a 2-column centred grid starting at y=220."""
        cols   = 2
        btn_w  = 200
        btn_h  = 70
        gap_x  = 40
        gap_y  = 30
        total_w = cols * btn_w + (cols - 1) * gap_x
        start_x = (W - total_w) // 2
        start_y = 220
        for i, name in enumerate(names):
            col = i % cols
            row = i // cols
            yield name, start_x + col * (btn_w + gap_x), start_y + row * (btn_h + gap_y)

    def run(self) -> int:
        """Event loop.  Returns 0-based level index, or -1 on back/quit."""
        while True:
            mx, my = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return -1
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return -1
                if self._back.is_clicked(event):
                    return -1
                for i, btn in enumerate(self._buttons):
                    if btn.is_clicked(event):
                        return i

            self.screen.fill(BG)

            title = self._title_font.render("SELECT LEVEL", True, (200, 230, 255))
            self.screen.blit(title, (self._width // 2 - title.get_width() // 2, 120))

            sub = self._font.render(
                "ESC / BACK to return to main menu", True, (100, 140, 200))
            self.screen.blit(sub, (self._width // 2 - sub.get_width() // 2, 168))

            for btn in self._buttons:
                btn.draw(self.screen, self._font, mx, my)

            self._back.draw(self.screen, self._font, mx, my)

            pygame.display.flip()
            self.clock.tick(FPS)
