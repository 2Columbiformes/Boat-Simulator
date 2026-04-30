import pygame
import math

class BulletVisual:
    @staticmethod
    def draw(screen, x, y, color, radius, velocity, is_explosion=False, weapon_type="pistol"):
        """Draws the bullet using specialized designs based on the weapon."""
        
        # Determine the visual design based on the weapon type, defaulting to 'pistol'
        weapon_lower = (weapon_type or "pistol").lower()

        # Handle the specialized designs if the projectile is not meant to be an explosion itself.
        if not is_explosion:
            if weapon_lower == "pistol":
                BulletVisual._draw_pistol_digital_dart(screen, x, y, velocity)
                return
            elif weapon_lower in ["machine_gun", "machine gun", "machinegun"]:
                BulletVisual._draw_machine_gun_digital_dart(screen, x, y, velocity)
                return
            elif weapon_lower == "sniper":
                BulletVisual._draw_sniper_digital_dart(screen, x, y, velocity)
                return
            elif weapon_lower in ["rocket_launcher", "rocket launcher", "rocketlauncher", "bazooka"]:
                # Force is_explosion=False to ensure the projectile itself is drawn, not a generic explosion circle.
                # (The explosion is handled by the weapon code upon impact)
                BulletVisual._draw_rocket_launcher_digital_dart(screen, x, y, velocity)
                return
            elif weapon_lower == "shotgun":
                BulletVisual._draw_shotgun_digital_dart(screen, x, y, velocity)
                return

        # Fallback design: a glowing sphere (used for generic or future weapon types)
        # 1. Draw motion trail (if moving)
        if velocity != (0, 0):
            vx, vy = velocity
            speed = math.hypot(vx, vy)
            trail_len = min(15, speed * 0.05)
            # Use the passed-in color, ignoring alpha for the trail
            target_rgb = color[:3] if len(color) > 3 else color
            pygame.draw.line(screen, target_rgb, (x, y), (x - (vx/speed)*trail_len, y - (vy/speed)*trail_len), 2)
            
        # 2. Draw the glowing core
        # Standard white core for standard bullets, yellow core for explosive-type bullets.
        main_color = (255, 255, 255) if not is_explosion else (255, 200, 50)
        pygame.draw.circle(screen, main_color, (int(x), int(y)), radius)
        # Inner white intensity core
        pygame.draw.circle(screen, (255, 255, 255), (int(x), int(y)), radius // 2)

    @staticmethod
    def _draw_pistol_digital_dart(screen, x, y, velocity):
        """Draws the blocky, tri-color rectangular design for the pistol."""
        vx, vy = velocity
        speed = math.hypot(vx, vy)
        if speed < 1.0: return # Skip if stopped

        angle = math.atan2(vy, vx) + math.pi / 2
        
        # 1. Define points for stacked colored blocks (relative to center-point x, y)
        outline_pts = [(-3, -7), (3, -7), (3, 7), (-3, 7)] # Overall dark border shape
        seg1_pts = [(-2, -6), (2, -6), (2, -2), (-2, -2)]   # Front (Muted Blue) block
        seg2_pts = [(-2, -2), (2, -2), (2, 4), (-2, 4)]     # Mid (Orange) block
        seg3_pts = [(-2, 4), (2, 4), (2, 6), (-2, 6)]       # Tail (Light Grey) block

        SCALE = 1.0 
        all_segments = [outline_pts, seg1_pts, seg2_pts, seg3_pts]
        scaled_pts = []
        
        # 2. Scale, Rotate, and Translate each set of points
        for segment in all_segments:
            rot_seg = []
            for px, py in segment:
                # Scale
                spx, spy = px * SCALE, py * SCALE
                # Rotate
                rx = spx * math.cos(angle) - spy * math.sin(angle)
                ry = spx * math.sin(angle) + spy * math.cos(angle)
                # Translate to screen position
                rot_seg.append((int(x + rx), int(y + ry)))
            scaled_pts.append(rot_seg)

        # 3. Apply specific colors (ignoring alpha to ensure solid vector appearance)
        outline_color = (25, 35, 35) # Dark charcoal outline
        seg1_color = (85, 105, 135)   # Muted Blue
        seg2_color = (200, 125, 45)   # Orange
        seg3_color = (165, 175, 185)  # Light Grey

        # 4. Draw each polygon in order (bottom layer to top layer)
        try:
            pygame.draw.polygon(screen, outline_color, scaled_pts[0]) # Draw the entire border shape
            pygame.draw.polygon(screen, seg1_color, scaled_pts[1])    # Draw front block
            pygame.draw.polygon(screen, seg2_color, scaled_pts[2])    # Draw mid block
            pygame.draw.polygon(screen, seg3_color, scaled_pts[3])    # Draw tail block
        except TypeError:
            # Fallback for old pygame versions that don't support RGBA in polygons well
            pygame.draw.polygon(screen, outline_color[:3], scaled_pts[0])
            pygame.draw.polygon(screen, seg1_color[:3], scaled_pts[1])
            pygame.draw.polygon(screen, seg2_color[:3], scaled_pts[2])
            pygame.draw.polygon(screen, seg3_color[:3], scaled_pts[3])

    @staticmethod
    def _draw_machine_gun_digital_dart(screen, x, y, velocity):
        """Draws the elongated, quad-color rectangular design for the machine gun."""
        vx, vy = velocity
        speed = math.hypot(vx, vy)
        if speed < 1.0: return 

        angle = math.atan2(vy, vx) + math.pi / 2

        # 1. Define points for stacked colored blocks (longer proportions)
        # Overall dark border shape
        outline_pts = [(-3, -11), (3, -11), (3, 10), (-3, 10)]
        # Stacked blocks
        seg_red_pts = [(-2, -10), (2, -10), (2, -7), (-2, -7)]   # Red Tip block
        seg_blue_pts = [(-2, -7), (2, -7), (2, -4), (-2, -4)]    # Muted Blue block
        seg_orange_pts = [(-2, -4), (2, -4), (2, 7), (-2, 7)]    # Large Orange block
        seg_grey_pts = [(-2, 7), (2, 7), (2, 9), (-2, 9)]        # Tail (Light Grey) block

        SCALE = 1.0 
        all_segments = [outline_pts, seg_red_pts, seg_blue_pts, seg_orange_pts, seg_grey_pts]
        scaled_pts = []
        
        # 2. Scale, Rotate, and Translate each set of points
        for segment in all_segments:
            rot_seg = []
            for px, py in segment:
                spx, spy = px * SCALE, py * SCALE
                rx = spx * math.cos(angle) - spy * math.sin(angle)
                ry = spx * math.sin(angle) + spy * math.cos(angle)
                rot_seg.append((int(x + rx), int(y + ry)))
            scaled_pts.append(rot_seg)

        # 3. Apply specific colors
        outline_color = (25, 35, 35)  # Dark outline
        color_red = (220, 70, 60)      # Bright Red
        color_blue = (85, 105, 135)    # Muted Blue
        color_orange = (200, 125, 45)  # Orange
        color_grey = (165, 175, 185)   # Light Grey

        # 4. Draw each polygon in order
        try:
            pygame.draw.polygon(screen, outline_color, scaled_pts[0]) 
            pygame.draw.polygon(screen, color_red, scaled_pts[1])      
            pygame.draw.polygon(screen, color_blue, scaled_pts[2])     
            pygame.draw.polygon(screen, color_orange, scaled_pts[3])   
            pygame.draw.polygon(screen, color_grey, scaled_pts[4])     
        except TypeError:
            pygame.draw.polygon(screen, outline_color[:3], scaled_pts[0])
            pygame.draw.polygon(screen, color_red[:3], scaled_pts[1])
            pygame.draw.polygon(screen, color_blue[:3], scaled_pts[2])
            pygame.draw.polygon(screen, color_orange[:3], scaled_pts[3])
            pygame.draw.polygon(screen, color_grey[:3], scaled_pts[4])

    @staticmethod
    def _draw_sniper_digital_dart(screen, x, y, velocity):
        """Draws the sniper bullet with a pointed tip and reflective dot."""
        vx, vy = velocity
        speed = math.hypot(vx, vy)
        if speed < 1.0: return 

        angle = math.atan2(vy, vx) + math.pi / 2

        # Define specialized points including a pointed tip and wide tail base
        seg_tip_pts = [(-2, -2), (2, -2), (2, -5), (0, -7), (-2, -5)] # Blue Pointed Tip
        seg_body_pts = [(-3, -2), (3, -2), (3, 8), (-3, 8)]           # Orange Body block
        seg_tail_pts = [(-3, 8), (3, 8), (3, 10), (-3, 10)]           # Grey Tail block
        # Define specific point for a light glint on the tip
        seg_dot_pts = [(0.5, -4.5), (1.5, -4.5), (1.5, -3.5), (0.5, -3.5)] # Glint Dot

        # Overall border shape (continuous outline polygon)
        outline_pts = [(-3, -2), (3, -2), (3, -5), (0, -8), (-3, -5), (-3, 8), (3, 8), (3, 10), (-3, 10)]

        SCALE = 1.0 
        all_segments = [outline_pts, seg_tip_pts, seg_body_pts, seg_tail_pts, seg_dot_pts]
        scaled_pts = []
        
        # Scale, Rotate, Translate
        for segment in all_segments:
            rot_seg = []
            for px, py in segment:
                spx, spy = px * SCALE, py * SCALE
                rx = spx * math.cos(angle) - spy * math.sin(angle)
                ry = spx * math.sin(angle) + spy * math.cos(angle)
                rot_seg.append((int(x + rx), int(y + ry)))
            scaled_pts.append(rot_seg)

        # Colors (ignoring alpha)
        color_tip = (85, 105, 135)     # Muted Blue
        color_body = (200, 125, 45)    # Orange
        color_tail = (165, 175, 185)   # Light Grey
        color_dot = (140, 160, 175)    # Lighter glint color
        color_outline = (25, 35, 35)   # Dark charcoal outline

        try:
            # Draw border first
            pygame.draw.polygon(screen, color_outline, scaled_pts[0])
            # Then stacked colors
            pygame.draw.polygon(screen, color_tip, scaled_pts[1])
            pygame.draw.polygon(screen, color_body, scaled_pts[2])
            pygame.draw.polygon(screen, color_tail, scaled_pts[3])
            # Draw glint last so it renders on top
            pygame.draw.polygon(screen, color_dot, scaled_pts[4]) 
        except TypeError:
            pygame.draw.polygon(screen, color_outline[:3], scaled_pts[0])
            pygame.draw.polygon(screen, color_tip[:3], scaled_pts[1])
            pygame.draw.polygon(screen, color_body[:3], scaled_pts[2])
            pygame.draw.polygon(screen, color_tail[:3], scaled_pts[3])
            pygame.draw.polygon(screen, color_dot[:3], scaled_pts[4])

    @staticmethod
    def _draw_rocket_launcher_digital_dart(screen, x, y, velocity):
        """
        Draws the complex, multi-segment, heavy rocket launcher projectile.
        New visual design based on image uploaded:image_010937.png.
        """
        vx, vy = velocity
        speed = math.hypot(vx, vy)
        if speed < 1.0: return 

        angle = math.atan2(vy, vx) + math.pi / 2

        # 1. Geometry based on the detailed rocket launcher reference (clockwise, relative points)
        
        # OVERALL CONTINUOUS OUTLINE POLYGON (behind everything)
        outline_continuous_pts = [
            (0, -11.5),      # Tip point
            (4, -9.5),       # Charcoal Body Top-Right chamfer start
            (5, -8.5),       # Charcoal Body side start
            (5, -3),         # Charcoal Body side end
            (4.5, -2.5),     # Recess top, shared with charcoal
            (5.5, -1.5),     # Deep Bronze side top
            (5.5, 4),        # Deep Bronze side bottom
            (5, 5),          # Grey base chamfer top
            (6, 6),          # Grey Tail side top
            (6, 10),         # Grey Tail side bottom
            (4, 12),         # Tail bottom corner chamfer start
            (-4, 12),        # Tail bottom corner chamfer end
            (-6, 10),        # Tail side bottom
            (-6, 6),         # Tail side top
            (-5, 5),         # Grey base chamfer top
            (-5.5, 4),       # Deep Bronze side bottom
            (-5.5, -1.5),    # Deep Bronze side top
            (-4.5, -2.5),    # Recess top, shared with charcoal
            (-5, -3),        # Charcoal Body side end
            (-5, -8.5),      # Charcoal Body side start
            (-4, -9.5),      # Charcoal Body top chamfer end
            (0, -11.5)       # Tip (close polygon)
        ]

        # STACKED COLORED POLYGON SEGMENTS
        seg_tip_pts = [(0, -11), (-3.5, -9), (3.5, -9)] 

        seg_body_1_charcoal_pts = [
            (-3.5, -9), (3.5, -9),      
            (4.5, -8), (4.5, -3.5),     
            (3.5, -2.5), (-3.5, -2.5),  
            (-4.5, -3.5), (-4.5, -8)     
        ]

        seg_recessed_band_pts = [(-3.5, -2.5), (3.5, -2.5), (3.5, -1), (-3.5, -1)]

        seg_body_2_deep_bronze_pts = [
            (-5, -1), (5, -1),         
            (5, 4.5), (4.5, 5),        
            (-4.5, 5), (-5, 4.5)       
        ]

        seg_base_and_tail_pts = [
            (-4.5, 5), (4.5, 5),       
            (6, 6.5), (6, 10),         
            (4, 11.5), (-4, 11.5),     
            (-6, 10), (-6, 6.5)        
        ]

        seg_dot_pts = [(0, -2), (1, -2), (1, -1), (0, -1)] 

        # --- SCALED UP FROM 1.0 TO 1.8 ---
        SCALE = 1.8 
        # ---------------------------------
        
        all_segments = [outline_continuous_pts, seg_recessed_band_pts, seg_body_1_charcoal_pts, seg_tip_pts, seg_body_2_deep_bronze_pts, seg_base_and_tail_pts, seg_dot_pts]
        scaled_pts = []
        
        # 2. Scale, Rotate, and Translate each set of points
        for segment in all_segments:
            rot_seg = []
            for px, py in segment:
                spx, spy = px * SCALE, py * SCALE
                rx = spx * math.cos(angle) - spy * math.sin(angle)
                ry = spx * math.sin(angle) + spy * math.cos(angle)
                rot_seg.append((int(x + rx), int(y + ry)))
            scaled_pts.append(rot_seg)

        # 3. Apply specific colors
        outline_color = (25, 35, 35)     
        color_charcoal_top = (45, 50, 55) 
        color_recessed_blue = (85, 105, 135) 
        color_deep_bronze = (165, 150, 130)  
        color_light_grey = (175, 185, 195)  
        color_dot_glint = (140, 160, 175) 

        # 4. Draw each polygon in correct stacking order
        try:
            pygame.draw.polygon(screen, outline_color, scaled_pts[0]) 
            pygame.draw.polygon(screen, color_recessed_blue, scaled_pts[1]) 
            pygame.draw.polygon(screen, color_charcoal_top, scaled_pts[2]) 
            pygame.draw.polygon(screen, color_charcoal_top, scaled_pts[3]) 
            pygame.draw.polygon(screen, color_deep_bronze, scaled_pts[4]) 
            pygame.draw.polygon(screen, color_light_grey, scaled_pts[5]) 
            pygame.draw.polygon(screen, color_dot_glint, scaled_pts[6]) 
        except TypeError:
            pygame.draw.polygon(screen, outline_color[:3], scaled_pts[0])
            pygame.draw.polygon(screen, color_recessed_blue[:3], scaled_pts[1]) 
            pygame.draw.polygon(screen, color_charcoal_top[:3], scaled_pts[2]) 
            pygame.draw.polygon(screen, color_charcoal_top[:3], scaled_pts[3]) 
            pygame.draw.polygon(screen, color_deep_bronze[:3], scaled_pts[4]) 
            pygame.draw.polygon(screen, color_light_grey[:3], scaled_pts[5]) 
            pygame.draw.polygon(screen, color_dot_glint[:3], scaled_pts[6]) 

    @staticmethod
    def _draw_shotgun_digital_dart(screen, x, y, velocity):
        """Draws a chunky, wide digital pellet using the standard dart color palette."""
        vx, vy = velocity
        # Prevent math errors if velocity is 0
        if vx == 0 and vy == 0:
            return
            
        angle = math.atan2(vy, vx)
        
        # Shotgun pellet geometry (Chunky, flat-nosed, and wide)
        seg_tip_pts = [(3, -1.5), (3, 1.5), (1, 2.5), (1, -2.5)]
        seg_body_pts = [(1, 2.5), (1, -2.5), (-2, -2.5), (-2, 2.5)]
        seg_tail_pts = [(-2, -2.5), (-2, 2.5), (-4, 3.5), (-4, -3.5)]

        # Slightly smaller scale since the shotgun fires 7 of them at once
        SCALE = 1.2 
        
        all_segments = [seg_tip_pts, seg_body_pts, seg_tail_pts]
        scaled_pts = []
        
        # Rotate and scale the points based on velocity angle
        for segment in all_segments:
            rot_seg = []
            for px, py in segment:
                spx, spy = px * SCALE, py * SCALE
                rx = spx * math.cos(angle) - spy * math.sin(angle)
                ry = spx * math.sin(angle) + spy * math.cos(angle)
                rot_seg.append((int(x + rx), int(y + ry)))
            scaled_pts.append(rot_seg)

        # Standard Digital Dart Colors (to match your other bullets)
        color_tip = (85, 105, 135)     # Muted Blue
        color_body = (200, 125, 45)    # Orange
        color_tail = (165, 175, 185)   # Light Grey

        # Draw the segments from back to front
        try:
            pygame.draw.polygon(screen, color_tail, scaled_pts[2])
            pygame.draw.polygon(screen, color_body, scaled_pts[1])
            pygame.draw.polygon(screen, color_tip, scaled_pts[0])
            
            # Draw a subtle speed-trail behind the pellet
            speed = math.hypot(vx, vy)
            trail_len = min(8, speed * 0.03)
            pygame.draw.line(screen, color_body, (int(x), int(y)), (int(x - (vx/speed)*trail_len), int(y - (vy/speed)*trail_len)), 1)
            
        except TypeError:
            # Fallback for older Pygame versions
            pygame.draw.polygon(screen, color_tail[:3], scaled_pts[2])
            pygame.draw.polygon(screen, color_body[:3], scaled_pts[1])
            pygame.draw.polygon(screen, color_tip[:3], scaled_pts[0])