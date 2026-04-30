import pygame
import math

class PlayerVisual:
    @staticmethod
    def draw(screen, x, y, angle, weapon_type="pistol"):
        """Draws the base boat hull and layers the equipped weapon on top."""
        
        # 1. Draw the base hull (The Boat)
        PlayerVisual._draw_base_hull(screen, x, y, angle)
        
        # 2. Draw the specific weapon turret on top (Mapping menu designs to top-down perspective)
        w_type = (weapon_type or "pistol").lower()
        
        if w_type == "pistol":
            PlayerVisual._draw_pistol_turret(screen, x, y, angle)
        elif w_type in ["machine_gun", "machine gun", "machinegun"]:
            PlayerVisual._draw_machine_gun_turret(screen, x, y, angle)
        elif w_type == "sniper":
            PlayerVisual._draw_sniper_turret(screen, x, y, angle)
        elif w_type == "shotgun":
            PlayerVisual._draw_shotgun_turret(screen, x, y, angle)
        elif w_type in ["rocket_launcher", "bazooka", "rocketlauncher"]:
            PlayerVisual._draw_bazooka_turret(screen, x, y, angle)
        else:
            PlayerVisual._draw_pistol_turret(screen, x, y, angle)

    @staticmethod
    def _transform(points, x, y, angle, scale=1.0):
        """Helper to scale, rotate, and translate geometry points."""
        scaled_pts = []
        # Offset angle by 90 degrees (pi/2) so 0 radians faces "up" naturally in vector space
        draw_angle = angle + math.pi / 2 
        for px, py in points:
            spx, spy = px * scale, py * scale
            rx = spx * math.cos(draw_angle) - spy * math.sin(draw_angle)
            ry = spx * math.sin(draw_angle) + spy * math.cos(draw_angle)
            scaled_pts.append((int(x + rx), int(y + ry)))
        return scaled_pts

    @staticmethod
    def _draw_polygon_safe(screen, color, points):
        """Helper to safely draw polygons across different Pygame versions."""
        try:
            pygame.draw.polygon(screen, color, points)
        except TypeError:
            pygame.draw.polygon(screen, color[:3], points)

    @staticmethod
    def _rect_to_poly(dx, dy, w, h, pivot_dx, pivot_dy):
        """Maps a 2D side-profile rect from the menu to a top-down rotatable polygon."""
        x_old = dx - pivot_dx
        y_old = dy - pivot_dy
        return [
            (y_old, -x_old),                  # top-left
            (y_old, -(x_old + w)),            # top-right
            (y_old + h, -(x_old + w)),        # bottom-right
            (y_old + h, -x_old)               # bottom-left
        ]

    @staticmethod
    def _draw_menu_rect(screen, color, dx, dy, w, h, x, y, angle, pivot_dx, pivot_dy, scale):
        """Converts and draws a menu rectangle onto the boat turret."""
        pts = PlayerVisual._rect_to_poly(dx, dy, w, h, pivot_dx, pivot_dy)
        PlayerVisual._draw_polygon_safe(screen, color, PlayerVisual._transform(pts, x, y, angle, scale))

    @staticmethod
    def _draw_base_hull(screen, x, y, angle):
        """Draws the dark grey geometric shield/hexagon hull with cyan accents."""
        hull_pts = [(0, -18), (12, -6), (12, 10), (6, 16), (-6, 16), (-12, 10), (-12, -6)]
        accent_pts = [(0, -12), (8, -4), (8, 6), (4, 10), (-4, 10), (-8, 6), (-8, -4)]
        engine_pts = [(-4, 16), (4, 16), (2, 20), (-2, 20)]

        color_hull = (35, 45, 50)
        color_accent = (0, 235, 195)
        color_engine = (0, 150, 255)
        color_outline = (20, 25, 30)

        PlayerVisual._draw_polygon_safe(screen, color_engine, PlayerVisual._transform(engine_pts, x, y, angle))
        PlayerVisual._draw_polygon_safe(screen, color_outline, PlayerVisual._transform(hull_pts, x, y, angle, scale=1.1))
        PlayerVisual._draw_polygon_safe(screen, color_hull, PlayerVisual._transform(hull_pts, x, y, angle))
        
        accent_transformed = PlayerVisual._transform(accent_pts, x, y, angle)
        pygame.draw.lines(screen, color_accent, True, accent_transformed, 2)

    # =========================================================================
    # WEAPON DESIGNS (Imported dynamically from weapons_menu.py coordinates)
    # =========================================================================

    @staticmethod
    def _draw_pistol_turret(screen, x, y, angle):
        p_dx, p_dy = -15, -90 # Pivot center
        scale = 0.35 # Scale down for the boat
        draw = lambda color, dx, dy, w, h: PlayerVisual._draw_menu_rect(screen, color, dx, dy, w, h, x, y, angle, p_dx, p_dy, scale)

        draw((70, 70, 75), -40, -105, 50, 25)      # Slide Back
        draw((100, 100, 105), 10, -105, 35, 20)    # Slide Front
        draw((160, 170, 180), 45, -105, 4, 20)     # Muzzle
        draw((40, 40, 45), -40, -80, 15, 30)       # Grip
        for i in range(3):
            draw((80, 90, 100), -38, -76 + (i * 8), 11, 4) # Grip Details
        draw((30, 30, 35), -25, -80, 12, 12)       # Trigger Guard
        draw((220, 50, 50), -21, -77, 3, 6)        # Trigger
        draw((130, 130, 135), 18, -102, 5, 2)      # Slide Detail 1
        draw((130, 130, 135), 30, -102, 5, 2)      # Slide Detail 2
        draw((200, 210, 220), -34, -50, 4, 4)      # Ring (Square representation)

    @staticmethod
    def _draw_machine_gun_turret(screen, x, y, angle):
        p_dx, p_dy = -30, -80
        scale = 0.35
        draw = lambda color, dx, dy, w, h: PlayerVisual._draw_menu_rect(screen, color, dx, dy, w, h, x, y, angle, p_dx, p_dy, scale)

        draw((50, 50, 55), -80, -100, 20, 25)      # Rear Stock
        draw((30, 30, 35), -68, -108, 8, 10)       # Iron Sight
        draw((55, 75, 95), -60, -105, 60, 45)      # Main Receiver
        draw((75, 95, 115), -60, -105, 50, 8)      # Receiver Shine
        draw((120, 135, 145), 0, -92, 80, 16)      # Perforated Barrel
        draw((150, 165, 175), 75, -95, 10, 22)     # Muzzle Tip
        for i in range(4):
            draw((40, 55, 65), 10 + (i * 15), -88, 6, 8) # Cooling Holes
        draw((45, 65, 85), -35, -60, 12, 12)       # Vertical Handle
        draw((30, 30, 30), -55, -48, 50, 5)        # Flat Base Stand

    @staticmethod
    def _draw_sniper_turret(screen, x, y, angle):
        p_dx, p_dy = -25, -90
        scale = 0.35
        draw = lambda color, dx, dy, w, h: PlayerVisual._draw_menu_rect(screen, color, dx, dy, w, h, x, y, angle, p_dx, p_dy, scale)

        draw((210, 105, 30), -95, -95, 35, 20)     # Stock
        draw((150, 75, 0), -95, -80, 10, 20)       # Butt Pad
        draw((255, 215, 0), -100, -90, 4, 15)      # Yellow Wire/Detail
        draw((205, 127, 50), -60, -100, 45, 38)    # Main Receiver
        draw((40, 40, 45), -55, -75, 12, 12)       # Trigger Grip
        draw((45, 45, 50), -55, -112, 40, 12)      # Scope Body
        draw((100, 100, 110), -40, -118, 5, 6)     # Scope Dial
        draw((140, 150, 160), -15, -93, 110, 10)   # Precision Barrel
        draw((100, 110, 120), 90, -98, 8, 20)      # Muzzle Brake 1
        draw((60, 60, 65), 98, -93, 6, 10)         # Muzzle Brake 2
        draw((55, 70, 90), -30, -62, 12, 12)       # Stand Neck
        draw((40, 50, 65), -50, -52, 50, 5)        # Stand Base

    @staticmethod
    def _draw_bazooka_turret(screen, x, y, angle):
        p_dx, p_dy = -15, -95
        scale = 0.35
        draw = lambda color, dx, dy, w, h: PlayerVisual._draw_menu_rect(screen, color, dx, dy, w, h, x, y, angle, p_dx, p_dy, scale)

        draw((100, 115, 130), -85, -95, 170, 30)   # Main Launch Tube
        draw((60, 75, 90), -95, -100, 15, 40)      # Tube End Cap 1
        draw((60, 75, 90), 75, -100, 15, 40)       # Tube End Cap 2
        draw((200, 205, 210), -25, -110, 20, 20)   # Round Gauge Base
        draw((200, 50, 50), -16, -108, 2, 8)       # Gauge Needle
        draw((30, 30, 35), 5, -112, 10, 18)        # Periscope Sight
        draw((0, 200, 255), 12, -110, 4, 4)        # Blue Lens
        draw((150, 155, 160), 50, -90, 25, 20)     # Rear Mechanism
        draw((200, 50, 50), 70, -83, 4, 6)         # Red Indicator
        draw((55, 75, 95), -45, -65, 10, 20)       # Front Leg
        draw((55, 75, 95), 5, -65, 10, 20)         # Back Leg
        draw((30, 30, 35), -55, -45, 80, 6)        # Base Plate

    @staticmethod
    def _draw_shotgun_turret(screen, x, y, angle):
        p_dx, p_dy = -30, -90
        scale = 0.35
        draw = lambda color, dx, dy, w, h: PlayerVisual._draw_menu_rect(screen, color, dx, dy, w, h, x, y, angle, p_dx, p_dy, scale)

        draw((139, 69, 19), -85, -95, 30, 25)      # Wooden Stock
        draw((100, 50, 15), -85, -85, 15, 20)      # Stock Butt
        draw((65, 65, 70), -55, -100, 45, 35)      # Heavy Receiver
        draw((45, 45, 50), -55, -85, 45, 4)        # Receiver Line
        draw((100, 100, 105), -10, -95, 95, 16)    # Main Top Barrel
        draw((140, 140, 145), -10, -95, 95, 4)     # Barrel Shine
        draw((75, 75, 80), -10, -79, 80, 8)        # Bottom Tube
        for i in range(3):
            draw((180, 180, 185), 5 + (i * 12), -100, 6, 3) # Cooling Vents
        draw((40, 40, 40), -40, -65, 10, 15)       # Vertical Foregrip Neck
        draw((30, 30, 30), -50, -50, 30, 6)        # Foregrip Base