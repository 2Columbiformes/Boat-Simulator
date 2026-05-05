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
        
        # Center weapon at player position
        weapon_x, weapon_y = x, y
        weapon_scale = scale * 0.5  # Smaller scale for weapon
        
        def weapon_rot_p(px, py):
            spx, spy = px * weapon_scale, py * weapon_scale
            rx = spx * math.cos(angle) - spy * math.sin(angle)
            ry = spx * math.sin(angle) + spy * math.cos(angle)
            return (weapon_x + rx, weapon_y + ry)
        
        def draw_rotated_rect(color, lx, ly, w, h, width=0):
            """Draw a rotated rectangle as a polygon."""
            corners = [
                (lx, ly),
                (lx + w, ly),
                (lx + w, ly + h),
                (lx, ly + h)
            ]
            rotated = [weapon_rot_p(px, py) for px, py in corners]
            pygame.draw.polygon(screen, color, rotated, width)
        
        if wt == "pistol":
            draw_rotated_rect((70, 70, 75), -20, -2.5, 25, 12.5)
            draw_rotated_rect((100, 100, 105), 5, -2.5, 17.5, 10)
            draw_rotated_rect((160, 170, 180), 22.5, -2.5, 2, 10)
            draw_rotated_rect((40, 40, 45), -20, 10, 7.5, 15)
            for i in range(3):
                draw_rotated_rect((80, 90, 100), -19, 13.5 + i * 4, 5.5, 2)
            draw_rotated_rect((30, 30, 35), -12.5, 10, 6, 6)
            draw_rotated_rect((220, 50, 50), -10.5, 12.5, 1.5, 3)
            draw_rotated_rect((130, 130, 135), 9, -1, 2.5, 1)
            draw_rotated_rect((130, 130, 135), 15, -1, 2.5, 1)
            wx, wy = weapon_rot_p(-16, 26)
            pygame.draw.circle(screen, (200, 210, 220), (int(wx), int(wy)), int(2 * weapon_scale))
        
        elif wt == "machine_gun":
            draw_rotated_rect((50, 50, 55), -40, -2.5, 10, 12.5)
            draw_rotated_rect((30, 30, 35), -34, -6, 4, 5)
            draw_rotated_rect((55, 75, 95), -30, -2.5, 30, 22.5)
            draw_rotated_rect((75, 95, 115), -30, -2.5, 25, 4)
            draw_rotated_rect((120, 135, 145), 0, 2.5, 40, 8)
            draw_rotated_rect((150, 165, 175), 37.5, 1.25, 5, 11)
            for i in range(4):
                draw_rotated_rect((40, 55, 65), 5 + i * 7.5, 4, 3, 4)
            draw_rotated_rect((45, 65, 85), -17.5, 17.5, 6, 6)
            draw_rotated_rect((30, 30, 30), -27.5, 26, 25, 2.5)
        
        elif wt == "sniper":
            draw_rotated_rect((210, 105, 30), -47.5, 1.25, 17.5, 10)
            draw_rotated_rect((150, 75, 0), -47.5, 11.25, 5, 10)
            draw_rotated_rect((205, 127, 50), -30, -2.5, 22.5, 19)
            draw_rotated_rect((40, 40, 45), -27.5, 12.5, 6, 6)
            draw_rotated_rect((45, 45, 50), -27.5, -6, 20, 6)
            draw_rotated_rect((100, 100, 110), -20, -8, 2.5, 3)
            draw_rotated_rect((140, 150, 160), -7.5, 2.5, 55, 5)
            draw_rotated_rect((100, 110, 120), 45, -1, 4, 10)
            draw_rotated_rect((60, 60, 65), 49, 2.5, 3, 5)
            draw_rotated_rect((55, 70, 90), -15, 17.5, 6, 6)
            draw_rotated_rect((40, 50, 65), -25, 26, 25, 2.5)
        
        elif wt == "bazooka":
            draw_rotated_rect((100, 115, 130), -42.5, 1.25, 85, 15)
            draw_rotated_rect((60, 75, 90), -47.5, -2.5, 7.5, 20)
            draw_rotated_rect((60, 75, 90), 37.5, -2.5, 7.5, 20)
            draw_rotated_rect((150, 155, 160), 25, 2.5, 12.5, 10)
            draw_rotated_rect((200, 50, 50), 35, 4.25, 2, 3)
            draw_rotated_rect((55, 75, 95), -22.5, 17.5, 5, 10)
            draw_rotated_rect((55, 75, 95), 2.5, 17.5, 5, 10)
            draw_rotated_rect((30, 30, 35), -27.5, 27.5, 40, 3)
            wx, wy = weapon_rot_p(-7.5, -2.5)
            pygame.draw.circle(screen, (200, 205, 210), (int(wx), int(wy)), int(5 * weapon_scale))
            pygame.draw.line(screen, (200, 50, 50), (wx, wy), weapon_rot_p(-7.5, -7.5), int(1 * weapon_scale))
            draw_rotated_rect((30, 30, 35), 2.5, -6, 5, 9)
            draw_rotated_rect((0, 200, 255), 6, -5.5, 2, 2)
        
        elif wt == "shotgun":
            draw_rotated_rect((139, 69, 19), -42.5, 1.25, 15, 12.5)
            draw_rotated_rect((100, 50, 15), -42.5, 13.75, 7.5, 10)
            draw_rotated_rect((65, 65, 70), -27.5, -2.5, 22.5, 17.5)
            draw_rotated_rect((45, 45, 50), -27.5, 13.75, 22.5, 2)
            draw_rotated_rect((100, 100, 105), -5, 1.25, 47.5, 8)
            draw_rotated_rect((140, 140, 145), -5, 1.25, 47.5, 2)
            draw_rotated_rect((75, 75, 80), -5, 11.75, 40, 4)
            for i in range(3):
                draw_rotated_rect((180, 180, 185), 2.5 + i * 6, -1.25, 3, 1.5)
            draw_rotated_rect((40, 40, 40), -20, 17.5, 5, 7.5)
            draw_rotated_rect((30, 30, 30), -25, 27.5, 15, 3)
