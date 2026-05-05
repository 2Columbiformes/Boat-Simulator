import pygame
import math


class PlayerVisual:
    @staticmethod
    def draw(screen, x, y, angle, weapon_type="pistol", radius: int = 20):
        scale = float(radius) / 20.0

        def rot_p(px, py):
            spx, spy = px * scale, py * scale
            rx = spx * math.cos(angle) - spy * math.sin(angle)
            ry = spx * math.sin(angle) + spy * math.cos(angle)
            return (x + rx, y + ry)

        hull_points = [(20, 0), (-15, 12), (-10, 0), (-15, -12)]
        rotated_hull = [rot_p(px, py) for px, py in hull_points]
        pygame.draw.polygon(screen, (50, 150, 255), rotated_hull)
        pygame.draw.polygon(screen, (20, 100, 200), rotated_hull, 2)

        cabin_points = [(5, -6), (5, 6), (-8, 6), (-8, -6)]
        rotated_cabin = [rot_p(px, py) for px, py in cabin_points]
        pygame.draw.polygon(screen, (100, 110, 120), rotated_cabin)
        pygame.draw.polygon(screen, (60, 70, 80), rotated_cabin, 2)

        wt = (weapon_type or "pistol").lower()
        
        # Position weapon at the front of the boat
        weapon_x, weapon_y = rot_p(25, 0)
        weapon_scale = scale * 0.5  # Smaller scale for weapon
        
        def weapon_rot_p(px, py):
            spx, spy = px * weapon_scale, py * weapon_scale
            rx = spx * math.cos(angle) - spy * math.sin(angle)
            ry = spx * math.sin(angle) + spy * math.cos(angle)
            return (weapon_x + rx, weapon_y + ry)
        
        if wt == "pistol":
            # Scaled down pistol design
            wx, wy = weapon_rot_p(-20, -2.5)
            pygame.draw.rect(screen, (70, 70, 75),      (wx, wy, 25 * weapon_scale, 12.5 * weapon_scale))
            wx, wy = weapon_rot_p(5, -2.5)
            pygame.draw.rect(screen, (100, 100, 105),   (wx, wy, 17.5 * weapon_scale, 10 * weapon_scale))
            wx, wy = weapon_rot_p(22.5, -2.5)
            pygame.draw.rect(screen, (160, 170, 180),   (wx, wy, 2 * weapon_scale, 10 * weapon_scale))
            wx, wy = weapon_rot_p(-20, 10)
            pygame.draw.rect(screen, (40, 40, 45),      (wx, wy, 7.5 * weapon_scale, 15 * weapon_scale))
            for i in range(3):
                wx, wy = weapon_rot_p(-19, 13.5 + i * 4)
                pygame.draw.rect(screen, (80, 90, 100), (wx, wy, 5.5 * weapon_scale, 2 * weapon_scale))
            wx, wy = weapon_rot_p(-12.5, 10)
            pygame.draw.rect(screen, (30, 30, 35),      (wx, wy, 6 * weapon_scale, 6 * weapon_scale))
            wx, wy = weapon_rot_p(-10.5, 12.5)
            pygame.draw.rect(screen, (220, 50, 50),     (wx, wy, 1.5 * weapon_scale, 3 * weapon_scale))
            wx, wy = weapon_rot_p(9, -1)
            pygame.draw.rect(screen, (130, 130, 135),   (wx, wy, 2.5 * weapon_scale, 1 * weapon_scale))
            wx, wy = weapon_rot_p(15, -1)
            pygame.draw.rect(screen, (130, 130, 135),   (wx, wy, 2.5 * weapon_scale, 1 * weapon_scale))
            wx, wy = weapon_rot_p(-16, 26)
            pygame.draw.circle(screen, (200, 210, 220), (int(wx), int(wy)), int(2 * weapon_scale), int(1 * weapon_scale))
        
        elif wt == "machine_gun":
            wx, wy = weapon_rot_p(-40, -2.5)
            pygame.draw.rect(screen, (50, 50, 55),      (wx, wy, 10 * weapon_scale, 12.5 * weapon_scale), border_radius=int(1 * weapon_scale))
            wx, wy = weapon_rot_p(-34, -6)
            pygame.draw.rect(screen, (30, 30, 35),      (wx, wy, 4 * weapon_scale, 5 * weapon_scale))
            wx, wy = weapon_rot_p(-30, -2.5)
            pygame.draw.rect(screen, (55, 75, 95),      (wx, wy, 30 * weapon_scale, 22.5 * weapon_scale), border_radius=int(1.5 * weapon_scale))
            wx, wy = weapon_rot_p(-30, -2.5)
            pygame.draw.rect(screen, (75, 95, 115),     (wx, wy, 25 * weapon_scale, 4 * weapon_scale))
            wx, wy = weapon_rot_p(0, 2.5)
            pygame.draw.rect(screen, (120, 135, 145),   (wx, wy, 40 * weapon_scale, 8 * weapon_scale))
            wx, wy = weapon_rot_p(37.5, 1.25)
            pygame.draw.rect(screen, (150, 165, 175),   (wx, wy, 5 * weapon_scale, 11 * weapon_scale), border_radius=int(0.5 * weapon_scale))
            for i in range(4):
                wx, wy = weapon_rot_p(5 + i * 7.5, 4)
                pygame.draw.rect(screen, (40, 55, 65),  (wx, wy, 3 * weapon_scale, 4 * weapon_scale))
            wx, wy = weapon_rot_p(-17.5, 17.5)
            pygame.draw.rect(screen, (45, 65, 85),      (wx, wy, 6 * weapon_scale, 6 * weapon_scale))
            wx, wy = weapon_rot_p(-27.5, 26)
            pygame.draw.rect(screen, (30, 30, 30),      (wx, wy, 25 * weapon_scale, 2.5 * weapon_scale), border_radius=int(1 * weapon_scale))
        
        elif wt == "sniper":
            wx, wy = weapon_rot_p(-47.5, 1.25)
            pygame.draw.rect(screen, (210, 105, 30),    (wx, wy, 17.5 * weapon_scale, 10 * weapon_scale), border_radius=int(1 * weapon_scale))
            wx, wy = weapon_rot_p(-47.5, 11.25)
            pygame.draw.rect(screen, (150, 75, 0),      (wx, wy, 5 * weapon_scale, 10 * weapon_scale), border_radius=int(1 * weapon_scale))
            wx, wy = weapon_rot_p(-50, 0)
            pygame.draw.arc(screen,  (255, 215, 0),     (wx, wy, 7.5 * weapon_scale, 15 * weapon_scale), 3.14, 4.71, int(1 * weapon_scale))
            wx, wy = weapon_rot_p(-30, -2.5)
            pygame.draw.rect(screen, (205, 127, 50),    (wx, wy, 22.5 * weapon_scale, 19 * weapon_scale), border_radius=int(1 * weapon_scale))
            wx, wy = weapon_rot_p(-27.5, 12.5)
            pygame.draw.rect(screen, (40, 40, 45),      (wx, wy, 6 * weapon_scale, 6 * weapon_scale))
            wx, wy = weapon_rot_p(-27.5, -6)
            pygame.draw.rect(screen, (45, 45, 50),      (wx, wy, 20 * weapon_scale, 6 * weapon_scale), border_radius=int(0.5 * weapon_scale))
            wx, wy = weapon_rot_p(-20, -8)
            pygame.draw.rect(screen, (100, 100, 110),   (wx, wy, 2.5 * weapon_scale, 3 * weapon_scale))
            wx, wy = weapon_rot_p(-7.5, 2.5)
            pygame.draw.rect(screen, (140, 150, 160),   (wx, wy, 55 * weapon_scale, 5 * weapon_scale))
            wx, wy = weapon_rot_p(45, -1)
            pygame.draw.rect(screen, (100, 110, 120),   (wx, wy, 4 * weapon_scale, 10 * weapon_scale))
            wx, wy = weapon_rot_p(49, 2.5)
            pygame.draw.rect(screen, (60, 60, 65),      (wx, wy, 3 * weapon_scale, 5 * weapon_scale))
            wx, wy = weapon_rot_p(-15, 17.5)
            pygame.draw.rect(screen, (55, 70, 90),      (wx, wy, 6 * weapon_scale, 6 * weapon_scale))
            wx, wy = weapon_rot_p(-25, 26)
            pygame.draw.rect(screen, (40, 50, 65),      (wx, wy, 25 * weapon_scale, 2.5 * weapon_scale), border_radius=int(1 * weapon_scale))
        
        elif wt == "bazooka":
            pygame.draw.rect(screen, (100, 115, 130),   weapon_rot_p(-42.5, 1.25), (85 * weapon_scale, 15 * weapon_scale), border_radius=int(1 * weapon_scale))
            pygame.draw.rect(screen, (60, 75, 90),      weapon_rot_p(-47.5, -2.5), (7.5 * weapon_scale, 20 * weapon_scale), border_radius=int(0.5 * weapon_scale))
            pygame.draw.rect(screen, (60, 75, 90),      weapon_rot_p(37.5, -2.5), (7.5 * weapon_scale, 20 * weapon_scale), border_radius=int(0.5 * weapon_scale))
            pygame.draw.circle(screen, (200, 205, 210), weapon_rot_p(-7.5, -2.5), 5 * weapon_scale)
            pygame.draw.line(screen,  (200, 50, 50),    weapon_rot_p(-7.5, -2.5), weapon_rot_p(-7.5, -7.5), int(1 * weapon_scale))
            pygame.draw.rect(screen, (30, 30, 35),      weapon_rot_p(2.5, -6), (5 * weapon_scale, 9 * weapon_scale))
            pygame.draw.rect(screen, (0, 200, 255),     weapon_rot_p(6, -5.5), (2 * weapon_scale, 2 * weapon_scale))
            pygame.draw.rect(screen, (150, 155, 160),   weapon_rot_p(25, 2.5), (12.5 * weapon_scale, 10 * weapon_scale))
            pygame.draw.rect(screen, (200, 50, 50),     weapon_rot_p(35, 4.25), (2 * weapon_scale, 3 * weapon_scale))
            pygame.draw.rect(screen, (55, 75, 95),      weapon_rot_p(-22.5, 17.5), (5 * weapon_scale, 10 * weapon_scale))
            pygame.draw.rect(screen, (55, 75, 95),      weapon_rot_p(2.5, 17.5), (5 * weapon_scale, 10 * weapon_scale))
            pygame.draw.rect(screen, (30, 30, 35),      weapon_rot_p(-27.5, 27.5), (40 * weapon_scale, 3 * weapon_scale), border_radius=int(1 * weapon_scale))
        
        elif wt == "shotgun":
            wx, wy = weapon_rot_p(-42.5, 1.25)
            pygame.draw.rect(screen, (139, 69, 19),     (wx, wy, 15 * weapon_scale, 12.5 * weapon_scale), border_radius=int(1 * weapon_scale))
            wx, wy = weapon_rot_p(-42.5, 13.75)
            pygame.draw.rect(screen, (100, 50, 15),     (wx, wy, 7.5 * weapon_scale, 10 * weapon_scale), border_radius=int(1 * weapon_scale))
            wx, wy = weapon_rot_p(-27.5, -2.5)
            pygame.draw.rect(screen, (65, 65, 70),      (wx, wy, 22.5 * weapon_scale, 17.5 * weapon_scale), border_radius=int(1 * weapon_scale))
            wx, wy = weapon_rot_p(-27.5, 13.75)
            pygame.draw.rect(screen, (45, 45, 50),      (wx, wy, 22.5 * weapon_scale, 2 * weapon_scale))
            wx, wy = weapon_rot_p(-5, 1.25)
            pygame.draw.rect(screen, (100, 100, 105),   (wx, wy, 47.5 * weapon_scale, 8 * weapon_scale))
            wx, wy = weapon_rot_p(-5, 1.25)
            pygame.draw.rect(screen, (140, 140, 145),   (wx, wy, 47.5 * weapon_scale, 2 * weapon_scale))
            wx, wy = weapon_rot_p(-5, 11.75)
            pygame.draw.rect(screen, (75, 75, 80),      (wx, wy, 40 * weapon_scale, 4 * weapon_scale))
            for i in range(3):
                wx, wy = weapon_rot_p(2.5 + i * 6, -1.25)
                pygame.draw.rect(screen, (180, 180, 185), (wx, wy, 3 * weapon_scale, 1.5 * weapon_scale))
            wx, wy = weapon_rot_p(-20, 17.5)
            pygame.draw.rect(screen, (40, 40, 40),      (wx, wy, 5 * weapon_scale, 7.5 * weapon_scale))
            wx, wy = weapon_rot_p(-25, 27.5)
            pygame.draw.rect(screen, (30, 30, 30),      (wx, wy, 15 * weapon_scale, 3 * weapon_scale), border_radius=int(1 * weapon_scale))
