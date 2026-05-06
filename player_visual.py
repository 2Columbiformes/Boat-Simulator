import pygame
import math


class PlayerVisual:
    @staticmethod
    def draw(screen, x, y, angle, weapon_type="pistol", radius=20):
        scale = float(radius) / 20.0
        PlayerVisual._draw_base_hull(screen, x, y, angle, scale)

        w_type = (weapon_type or "pistol").lower()

        if w_type == "pistol":
            PlayerVisual._draw_pistol_turret(screen, x, y, angle, scale)
        elif w_type in ["machine_gun", "machine gun", "machinegun"]:
            PlayerVisual._draw_machine_gun_turret(screen, x, y, angle, scale)
        elif w_type == "sniper":
            PlayerVisual._draw_sniper_turret(screen, x, y, angle, scale)
        elif w_type == "shotgun":
            PlayerVisual._draw_shotgun_turret(screen, x, y, angle, scale)
        elif w_type in ["rocket_launcher", "bazooka", "rocketlauncher"]:
            PlayerVisual._draw_bazooka_turret(screen, x, y, angle, scale)
        else:
            PlayerVisual._draw_pistol_turret(screen, x, y, angle, scale)

    @staticmethod
    def _transform(points, x, y, angle, scale=1.0):
        """Scale, rotate (with +90° offset so 0 rad faces right), and translate points."""
        draw_angle = angle + math.pi / 2
        result = []
        for px, py in points:
            spx, spy = px * scale, py * scale
            rx = spx * math.cos(draw_angle) - spy * math.sin(draw_angle)
            ry = spx * math.sin(draw_angle) + spy * math.cos(draw_angle)
            result.append((int(x + rx), int(y + ry)))
        return result

    @staticmethod
    def _draw_polygon_safe(screen, color, points):
        try:
            pygame.draw.polygon(screen, color, points)
        except TypeError:
            pygame.draw.polygon(screen, color[:3], points)

    @staticmethod
    def _rect_to_poly(dx, dy, w, h, pivot_dx, pivot_dy):
        x_old = dx - pivot_dx
        y_old = dy - pivot_dy
        return [
            (y_old, -x_old),
            (y_old, -(x_old + w)),
            (y_old + h, -(x_old + w)),
            (y_old + h, -x_old),
        ]

    @staticmethod
    def _draw_menu_rect(screen, color, dx, dy, w, h, x, y, angle, pivot_dx, pivot_dy, scale):
        pts = PlayerVisual._rect_to_poly(dx, dy, w, h, pivot_dx, pivot_dy)
        PlayerVisual._draw_polygon_safe(
            screen, color, PlayerVisual._transform(pts, x, y, angle, scale)
        )

    @staticmethod
    def _draw_base_hull(screen, x, y, angle, scale=1.0):
        hull_pts   = [(0, -18), (12, -6), (12, 10), (6, 16), (-6, 16), (-12, 10), (-12, -6)]
        accent_pts = [(0, -12), (8, -4),  (8, 6),   (4, 10), (-4, 10), (-8, 6),   (-8, -4)]
        engine_pts = [(-4, 16), (4, 16),  (2, 20),  (-2, 20)]

        color_hull    = (35, 45, 50)
        color_accent  = (0, 235, 195)
        color_engine  = (0, 150, 255)
        color_outline = (20, 25, 30)

        PlayerVisual._draw_polygon_safe(
            screen, color_engine,
            PlayerVisual._transform(engine_pts, x, y, angle, scale)
        )
        PlayerVisual._draw_polygon_safe(
            screen, color_outline,
            PlayerVisual._transform(hull_pts, x, y, angle, scale * 1.1)
        )
        PlayerVisual._draw_polygon_safe(
            screen, color_hull,
            PlayerVisual._transform(hull_pts, x, y, angle, scale)
        )
        accent_transformed = PlayerVisual._transform(accent_pts, x, y, angle, scale)
        pygame.draw.lines(screen, color_accent, True, accent_transformed, 2)

    # --- shared weapon helpers ---

    @staticmethod
    def _weapon_rot(x, y, angle, ws):
        """Return a closure that rotates+scales a local point to screen coords."""
        def rot(px, py):
            spx, spy = px * ws, py * ws
            rx = spx * math.cos(angle) - spy * math.sin(angle)
            ry = spx * math.sin(angle) + spy * math.cos(angle)
            return (x + rx, y + ry)
        return rot

    @staticmethod
    def _wrect(screen, color, lx, ly, w, h, rot):
        corners = [(lx, ly), (lx + w, ly), (lx + w, ly + h), (lx, ly + h)]
        pygame.draw.polygon(screen, color, [rot(px, py) for px, py in corners])

    # --- turret methods ---

    @staticmethod
    def _draw_pistol_turret(screen, x, y, angle, scale=1.0):
        ws = scale * 0.5
        rot = PlayerVisual._weapon_rot(x, y, angle, ws)
        r = PlayerVisual._wrect
        r(screen, (70, 70, 75),       -20,  -2.5,  25,   12.5, rot)
        r(screen, (100, 100, 105),      5,  -2.5,  17.5, 10,   rot)
        r(screen, (160, 170, 180),     22.5, -2.5,   2,   10,   rot)
        r(screen, (40, 40, 45),       -20,   10,    7.5,  15,   rot)
        for i in range(3):
            r(screen, (80, 90, 100),  -19,  13.5 + i * 4, 5.5, 2, rot)
        r(screen, (30, 30, 35),       -12.5, 10,    6,    6,    rot)
        r(screen, (220, 50, 50),      -10.5, 12.5,  1.5,  3,    rot)
        r(screen, (130, 130, 135),      9,   -1,    2.5,  1,    rot)
        r(screen, (130, 130, 135),     15,   -1,    2.5,  1,    rot)
        wx, wy = rot(-16, 26)
        pygame.draw.circle(screen, (200, 210, 220), (int(wx), int(wy)), max(1, int(2 * ws)))

    @staticmethod
    def _draw_machine_gun_turret(screen, x, y, angle, scale=1.0):
        ws = scale * 0.5
        rot = PlayerVisual._weapon_rot(x, y, angle, ws)
        r = PlayerVisual._wrect
        r(screen, (50, 50, 55),       -40,  -2.5,  10,   12.5, rot)
        r(screen, (30, 30, 35),       -34,  -6,     4,    5,    rot)
        r(screen, (55, 75, 95),       -30,  -2.5,  30,   22.5, rot)
        r(screen, (75, 95, 115),      -30,  -2.5,  25,    4,   rot)
        r(screen, (120, 135, 145),      0,   2.5,  40,    8,   rot)
        r(screen, (150, 165, 175),     37.5,  1.25,  5,   11,   rot)
        for i in range(4):
            r(screen, (40, 55, 65),    5 + i * 7.5, 4, 3, 4, rot)
        r(screen, (45, 65, 85),       -17.5, 17.5,  6,    6,   rot)
        r(screen, (30, 30, 30),       -27.5, 26,   25,    2.5, rot)

    @staticmethod
    def _draw_sniper_turret(screen, x, y, angle, scale=1.0):
        ws = scale * 0.5
        rot = PlayerVisual._weapon_rot(x, y, angle, ws)
        r = PlayerVisual._wrect
        r(screen, (210, 105, 30),     -47.5,  1.25, 17.5, 10,  rot)
        r(screen, (150, 75, 0),       -47.5, 11.25,  5,   10,  rot)
        r(screen, (205, 127, 50),     -30,   -2.5,  22.5, 19,  rot)
        r(screen, (40, 40, 45),       -27.5, 12.5,   6,    6,  rot)
        r(screen, (45, 45, 50),       -27.5, -6,    20,    6,  rot)
        r(screen, (100, 100, 110),    -20,   -8,     2.5,  3,  rot)
        r(screen, (140, 150, 160),     -7.5,  2.5,  55,    5,  rot)
        r(screen, (100, 110, 120),     45,   -1,     4,   10,  rot)
        r(screen, (60, 60, 65),        49,    2.5,   3,    5,  rot)
        r(screen, (55, 70, 90),       -15,   17.5,   6,    6,  rot)
        r(screen, (40, 50, 65),       -25,   26,    25,    2.5, rot)

    @staticmethod
    def _draw_shotgun_turret(screen, x, y, angle, scale=1.0):
        ws = scale * 0.5
        rot = PlayerVisual._weapon_rot(x, y, angle, ws)
        r = PlayerVisual._wrect
        r(screen, (139, 69, 19),      -42.5,  1.25, 15,   12.5, rot)
        r(screen, (100, 50, 15),      -42.5, 13.75,  7.5, 10,   rot)
        r(screen, (65, 65, 70),       -27.5, -2.5,  22.5, 17.5, rot)
        r(screen, (45, 45, 50),       -27.5, 13.75, 22.5,  2,   rot)
        r(screen, (100, 100, 105),     -5,    1.25, 47.5,  8,   rot)
        r(screen, (140, 140, 145),     -5,    1.25, 47.5,  2,   rot)
        r(screen, (75, 75, 80),        -5,   11.75, 40,    4,   rot)
        for i in range(3):
            r(screen, (180, 180, 185), 2.5 + i * 6, -1.25, 3, 1.5, rot)
        r(screen, (40, 40, 40),       -20,   17.5,   5,    7.5, rot)
        r(screen, (30, 30, 30),       -25,   27.5,  15,    3,   rot)

    @staticmethod
    def _draw_bazooka_turret(screen, x, y, angle, scale=1.0):
        ws = scale * 0.5
        rot = PlayerVisual._weapon_rot(x, y, angle, ws)
        r = PlayerVisual._wrect
        r(screen, (100, 115, 130),    -42.5,  1.25, 85,   15,  rot)
        r(screen, (60, 75, 90),       -47.5, -2.5,   7.5, 20,  rot)
        r(screen, (60, 75, 90),        37.5, -2.5,   7.5, 20,  rot)
        r(screen, (150, 155, 160),     25,    2.5,  12.5, 10,  rot)
        r(screen, (200, 50, 50),       35,    4.25,  2,    3,  rot)
        r(screen, (55, 75, 95),       -22.5, 17.5,   5,   10,  rot)
        r(screen, (55, 75, 95),         2.5, 17.5,   5,   10,  rot)
        r(screen, (30, 30, 35),       -27.5, 27.5,  40,    3,  rot)
        wx, wy = rot(-7.5, -2.5)
        pygame.draw.circle(screen, (200, 205, 210), (int(wx), int(wy)), max(1, int(5 * ws)))
        pygame.draw.line(screen, (200, 50, 50), (wx, wy), rot(-7.5, -7.5), max(1, int(1 * ws)))
        r(screen, (30, 30, 35),         2.5, -6,     5,    9,  rot)
        r(screen, (0, 200, 255),         6,  -5.5,   2,    2,  rot)
