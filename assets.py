import pygame
import math

class PlayerVisual:
    @staticmethod
    def draw(screen, x, y, angle, weapon_type):
        """Draws the player's boat and turret based on aim angle."""
        def rot_p(px, py):
            rx = px * math.cos(angle) - py * math.sin(angle)
            ry = px * math.sin(angle) + py * math.cos(angle)
            return (x + rx, y + ry)

        # Hull
        hull_points = [(20, 0), (-15, 12), (-10, 0), (-15, -12)]
        rotated_hull = [rot_p(px, py) for px, py in hull_points]
        pygame.draw.polygon(screen, (50, 150, 255), rotated_hull)     
        pygame.draw.polygon(screen, (20, 100, 200), rotated_hull, 2)  

        # Cabin
        cabin_points = [(5, -6), (5, 6), (-8, 6), (-8, -6)]
        rotated_cabin = [rot_p(px, py) for px, py in cabin_points]
        pygame.draw.polygon(screen, (100, 110, 120), rotated_cabin)
        pygame.draw.polygon(screen, (60, 70, 80), rotated_cabin, 2)

        # Barrels
        if weapon_type.lower() == "shotgun":
            b_start_1, b_end_1 = rot_p(5, -3), rot_p(22, -3)
            b_start_2, b_end_2 = rot_p(5, 3), rot_p(22, 3)
            pygame.draw.line(screen, (40, 40, 40), b_start_1, b_end_1, 3)
            pygame.draw.line(screen, (40, 40, 40), b_start_2, b_end_2, 3)
        elif weapon_type.lower() == "sniper":
            b_start, b_end = rot_p(5, 0), rot_p(30, 0)
            pygame.draw.line(screen, (30, 30, 30), b_start, b_end, 3)
        else:
            b_start, b_end = rot_p(5, 0), rot_p(20, 0)
            pygame.draw.line(screen, (40, 40, 40), b_start, b_end, 4)

class EnemyVisual:
    @staticmethod
    def draw(screen, name, sx, sy, r, vx, vy):
        """Draws specific enemy designs."""
        angle = math.atan2(vy, vx) if (vx != 0 or vy != 0) else 0
        speed = math.hypot(vx, vy)

        def rot_p(px, py):
            rx = px * math.cos(angle) - py * math.sin(angle)
            ry = px * math.sin(angle) + py * math.cos(angle)
            return (sx + rx, sy + ry)

        if name == "Chaser":
            points = [(r, 0), (-r, r * 0.8), (-r * 0.4, 0), (-r, -r * 0.8)]
            rotated_points = [rot_p(px, py) for px, py in points]
            pygame.draw.polygon(screen, (160, 40, 40), rotated_points)
            pygame.draw.polygon(screen, (255, 140, 0), rotated_points, 2)
            ecx, ecy = rot_p(-r * 0.6, 0)
            pygame.draw.circle(screen, (0, 200, 255), (int(ecx), int(ecy)), 3)
            return True

        elif name == "Bomber":
            color_body, color_seg, color_spike = (50, 50, 55), (35, 35, 40), (120, 120, 125)
            pygame.draw.circle(screen, color_body, (sx, sy), r)
            pygame.draw.line(screen, color_seg, (sx - r, sy), (sx + r, sy), 2)
            pygame.draw.line(screen, color_seg, (sx, sy - r), (sx, sy + r), 2)
            diag = r * 0.707
            pygame.draw.line(screen, color_seg, (sx - diag, sy - diag), (sx + diag, sy + diag), 2)
            pygame.draw.line(screen, color_seg, (sx + diag, sy - diag), (sx - diag, sy + diag), 2)
            for i in range(8):
                sa = i * (2 * math.pi / 8)
                sl = r * 0.6
                spike_pts = [
                    (sx + (r + sl) * math.cos(sa), sy + (r + sl) * math.sin(sa)),
                    (sx + (r * 0.9) * math.cos(sa - 0.2), sy + (r * 0.9) * math.sin(sa - 0.2)),
                    (sx + (r * 0.9) * math.cos(sa + 0.2), sy + (r * 0.9) * math.sin(sa + 0.2))
                ]
                pygame.draw.polygon(screen, color_spike, spike_pts)
                pygame.draw.polygon(screen, (80, 80, 85), spike_pts, 1)
            cr = r * 0.4
            pygame.draw.circle(screen, (0, 150, 180), (sx, sy), cr)
            pygame.draw.circle(screen, (0, 255, 255), (sx, sy), cr * 0.6)
            pygame.draw.circle(screen, (255, 255, 255), (sx - cr * 0.3, sy - cr * 0.3), cr * 0.2)
            return True

        elif name == "Pistol Grunt":
            moving = speed > 5.0
            hull_pts = [(r * 0.9, -r * 0.4), (r * 0.9, r * 0.4), (r * 0.4, r * 0.85), (-r * 0.9, r * 0.85), (-r * 0.9, -r * 0.85), (r * 0.4, -r * 0.85)]
            pygame.draw.polygon(screen, (200, 205, 210), [rot_p(px, py) for px, py in hull_pts])
            pygame.draw.polygon(screen, (90, 95, 100), [rot_p(px, py) for px, py in hull_pts], 2)
            deck_pts = [(r * 0.6, -r * 0.3), (r * 0.6, r * 0.3), (r * 0.2, r * 0.6), (-r * 0.7, r * 0.6), (-r * 0.7, -r * 0.6), (r * 0.2, -r * 0.6)]
            pygame.draw.polygon(screen, (150, 155, 160), [rot_p(px, py) for px, py in deck_pts])
            cabin_pts = [(r * 0.3, -r * 0.4), (r * 0.3, r * 0.4), (-r * 0.5, r * 0.4), (-r * 0.5, -r * 0.4)]
            pygame.draw.polygon(screen, (110, 115, 120), [rot_p(px, py) for px, py in cabin_pts])
            for my in [-r * 0.65, r * 0.65]: 
                m_pts = [(-r * 0.7, my - r * 0.25), (-r * 1.1, my - r * 0.25), (-r * 1.1, my + r * 0.25), (-r * 0.7, my + r * 0.25)]
                pygame.draw.polygon(screen, (220, 40, 40), [rot_p(px, py) for px, py in m_pts])
                if moving:
                    pygame.draw.line(screen, (255, 200, 0), rot_p(-r * 1.1, my), rot_p(-r * 1.8, my), 3)
            gtx, gty = rot_p(r * 0.4, 0)
            pygame.draw.line(screen, (60, 60, 65), rot_p(r * 0.4, 0), rot_p(r * 1.2, 0), 4)
            pygame.draw.circle(screen, (130, 135, 140), (int(gtx), int(gty)), int(r * 0.35))
            return True

        elif name == "Gunner":
            moving = speed > 5.0
            hull_pts = [(r * 0.9, -r * 0.5), (r * 0.9, r * 0.5), (r * 0.4, r * 1.0), (-r * 0.9, r * 1.0), (-r * 0.9, -r * 1.0), (r * 0.4, -r * 1.0)]
            pygame.draw.polygon(screen, (80, 110, 60), [rot_p(px, py) for px, py in hull_pts])
            pygame.draw.polygon(screen, (40, 50, 30), [rot_p(px, py) for px, py in hull_pts], 2)
            deck_pts = [(r * 0.6, -r * 0.4), (r * 0.6, r * 0.4), (r * 0.2, r * 0.8), (-r * 0.7, r * 0.8), (-r * 0.7, -r * 0.8), (r * 0.2, -r * 0.8)]
            pygame.draw.polygon(screen, (140, 145, 150), [rot_p(px, py) for px, py in deck_pts])
            cabin_pts = [(r * 0.3, -r * 0.5), (r * 0.3, r * 0.5), (-r * 0.6, r * 0.5), (-r * 0.6, -r * 0.5)]
            pygame.draw.polygon(screen, (110, 115, 120), [rot_p(px, py) for px, py in cabin_pts])
            for my in [-r * 0.8, r * 0.8]: 
                m_pts = [(-r * 0.7, my - r * 0.25), (-r * 1.1, my - r * 0.25), (-r * 1.1, my + r * 0.25), (-r * 0.7, my + r * 0.25)]
                pygame.draw.polygon(screen, (220, 40, 40), [rot_p(px, py) for px, py in m_pts])
                if moving:
                    pygame.draw.line(screen, (255, 200, 0), rot_p(-r * 1.1, my), rot_p(-r * 1.8, my), 3)
            bs = r * 0.25
            pygame.draw.line(screen, (40, 40, 45), rot_p(r * 0.3, -bs / 2), rot_p(r * 1.4, -bs / 2), 4)
            pygame.draw.line(screen, (40, 40, 45), rot_p(r * 0.3, bs / 2), rot_p(r * 1.4, bs / 2), 4)
            gc_pts = [(r * 0.4, -r * 0.25), (r * 0.4, r * 0.25), (-r * 0.1, r * 0.25), (-r * 0.1, -r * 0.25)]
            pygame.draw.polygon(screen, (90, 95, 100), [rot_p(px, py) for px, py in gc_pts])
            return True

        elif name == "Sniper":
            moving = speed > 2.0
            hull_pts = [(r * 1.4, 0), (r * 0.5, r * 0.4), (-r * 0.9, r * 0.4), (-r * 0.9, -r * 0.4), (r * 0.5, -r * 0.4)]
            pygame.draw.polygon(screen, (90, 40, 150), [rot_p(px, py) for px, py in hull_pts])
            for sign in [-1, 1]:
                p_pts = [(r * 0.8, sign * r * 0.4), (r * 0.2, sign * r * 0.8), (-r * 0.9, sign * r * 0.8), (-r * 0.9, sign * r * 0.4)]
                pygame.draw.polygon(screen, (110, 60, 180), [rot_p(px, py) for px, py in p_pts])
            c_pts = [(r * 0.2, -r * 0.3), (r * 0.5, 0), (r * 0.2, r * 0.3), (-r * 0.6, r * 0.3), (-r * 0.6, -r * 0.3)]
            pygame.draw.polygon(screen, (40, 40, 45), [rot_p(px, py) for px, py in c_pts])
            pygame.draw.line(screen, (30, 30, 35), rot_p(r * 0.4, 0), rot_p(r * 2.2, 0), 4)
            for my in [-r * 0.6, r * 0.6]:
                m_pts = [(-r * 0.9, my - r * 0.2), (-r * 1.2, my - r * 0.2), (-r * 1.2, my + r * 0.2), (-r * 0.9, my + r * 0.2)]
                pygame.draw.polygon(screen, (255, 20, 147), [rot_p(px, py) for px, py in m_pts])
                if moving:
                    pygame.draw.line(screen, (255, 100, 200), rot_p(-r * 1.2, my), rot_p(-r * 2.0, my), 3)
            return True

        elif name == "Rocketeer":
            moving = speed > 2.0
            hull_pts = [(r * 0.8, -r * 0.7), (r * 0.8, r * 0.7), (r * 0.3, r * 0.9), (-r * 0.8, r * 0.9), (-r * 0.8, -r * 0.9), (r * 0.3, -r * 0.9)]
            pygame.draw.polygon(screen, (55, 60, 65), [rot_p(px, py) for px, py in hull_pts])  
            box_pts = [(r * 0.7, -r * 0.45), (r * 0.7, r * 0.45), (r * 0.1, r * 0.45), (r * 0.1, -r * 0.45)]
            pygame.draw.polygon(screen, (80, 85, 90), [rot_p(px, py) for px, py in box_pts])
            for ty in [-r * 0.25, 0, r * 0.25]:
                tx, ty_rot = rot_p(r * 0.7, ty)
                pygame.draw.circle(screen, (220, 50, 50), (int(tx), int(ty_rot)), int(r * 0.12))
            for my in [-r * 0.6, r * 0.6]:
                m_pts = [(-r * 0.8, my - r * 0.3), (-r * 1.2, my - r * 0.3), (-r * 1.2, my + r * 0.3), (-r * 0.8, my + r * 0.3)]
                pygame.draw.polygon(screen, (200, 60, 20), [rot_p(px, py) for px, py in m_pts])
                if moving:
                    pygame.draw.line(screen, (255, 150, 0), rot_p(-r * 1.2, my), rot_p(-r * 2.2, my), 4)
            return True

        elif name == "Breacher":
            moving = speed > 2.0
            hull_pts = [(r * 0.7, -r * 0.8), (r * 0.7, r * 0.8), (-r * 0.8, r * 0.9), (-r * 0.8, -r * 0.9)]
            pygame.draw.polygon(screen, (160, 70, 40), [rot_p(px, py) for px, py in hull_pts])  
            c_pts = [(r * 0.1, -r * 0.4), (r * 0.1, r * 0.4), (-r * 0.4, r * 0.4), (-r * 0.4, -r * 0.4)]
            pygame.draw.polygon(screen, (60, 60, 65), [rot_p(px, py) for px, py in c_pts])
            for ba in [-0.4, -0.2, 0, 0.2, 0.4]:
                bx, by = rot_p(r * 0.1, 0)
                ex = sx + r * 1.3 * math.cos(angle + ba)
                ey = sy + r * 1.3 * math.sin(angle + ba)
                pygame.draw.line(screen, (50, 50, 55), (bx, by), (ex, ey), 4)
            for my_offset in [-r * 0.6, 0, r * 0.6]: 
                m_pts = [(-r * 0.8, my_offset - r * 0.2), (-r * 1.1, my_offset - r * 0.2), (-r * 1.1, my_offset + r * 0.2), (-r * 0.8, my_offset + r * 0.2)]
                pygame.draw.polygon(screen, (100, 100, 100), [rot_p(px, py) for px, py in m_pts])
                if moving:
                    pygame.draw.line(screen, (255, 100, 0), rot_p(-r * 1.1, my_offset), rot_p(-r * 1.7, my_offset), 3)
            return True

        return False