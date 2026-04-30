import math
import pygame
import sys
import numpy as np
import random

from water import (WaterGrid, WIDTH, HEIGHT, GRID_W, GRID_H,
                   CELL_W, CELL_H, FPS,
                   WAVE_GRAD_K, DRAG_K, DISPLACE_AMP, RIPPLE_AMP,
                   SPLASH_AMP, SPLASH_R,
                   COLOR_DEEP, COLOR_SHALLOW, COLOR_CREST)
from entity import Entity
from weapon import Projectile
from enemy import Enemy
from bullet import BulletVisual
from player_visual import PlayerVisual    # Use your custom dynamic weapon base
from assets import EnemyVisual            # Only get the enemies from assets
from bullet import BulletVisual           # Get the glowing bullets

# ── Collision constants (kept here as they belong to the game loop) ────────────
RESTITUTION      = 1.0
COLLISION_DMG_K  = 0.25
COLLISION_SPLASH = 1.0


class WaterGame:
    """
    Pygame orchestrator.

    Quick-start
    -----------
    game = WaterGame()
    game.add_entity(x=200, y=300, mass=2, color=(50,220,80), controllable=True)
    game.add_enemy(make_chaser(x=500, y=200))
    game.run()
    """

    def __init__(self, width: int = WIDTH, height: int = HEIGHT, fps: int = FPS,
                 flag_pos=None, flag_radius: float = 30,
                 survival: bool = False, survival_secs: float = 120.0,
                 current_force: float = 90.0, scroll_speed: float = 5.0):
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Boat Simulator — WASD/arrows to move, click to splash")
        self.clock   = pygame.time.Clock()
        self.fps     = fps
        self.width   = width
        self.height  = height
        self.running = True

        self.water       = WaterGrid(GRID_H, GRID_W)
        self.entities:   list[Entity]     = []
        self.enemies:    list[Enemy]      = []
        self.projectiles: list[Projectile] = []
        self._explosions: list[dict]       = []   # {x,y,r,max_r,t,max_t}
        self.player: Entity | None = None

        self._pixel_buf  = np.zeros((width, height, 3), dtype=np.uint8)
        self._water_surf = pygame.Surface((width, height))
        self._font       = pygame.font.SysFont(None, 18)
        self._frame      = 0

        # Flag / goal
        self.flag_pos    = flag_pos
        self.flag_radius = flag_radius

        # Survival mode
        self.survival       = survival
        self._survival_t    = float(survival_secs)
        self._current_force = float(current_force)
        self._scroll_speed  = float(scroll_speed)
        self._scroll_accum  = 0.0

        self._result: str | None = None

        # Player weapon (assigned externally before run())
        self.player_weapon = None

    # ── Public API ─────────────────────────────────────────────────────────────
    def add_entity(self, x: float, y: float, **kwargs) -> Entity:
        """
        Add a bare entity (player, static obstacle, etc.).
        kwargs: mass, radius, color, vx, vy, max_hp, static, controllable, name
        """
        e = Entity(x=x, y=y, **kwargs)
        if e.static:
            gx = x / CELL_W;  gy = y / CELL_H
            self.water.set_obstacle(gx, gy, e.radius / max(CELL_W, CELL_H) + 1)
        if e.controllable:
            self.player = e
        self.entities.append(e)
        return e

    def add_enemy(self, enemy: Enemy) -> Enemy:
        """Register an Enemy; its inner Entity is automatically added to physics."""
        self.enemies.append(enemy)
        self.entities.append(enemy)
        return enemy

    # ── Main loop ──────────────────────────────────────────────────────────────
    def run(self) -> str:
        dt = 1.0 / self.fps
        pygame.event.clear()
        while self.running:
            self._handle_events()
            self._handle_input()
            if self.player_weapon:
                self.player_weapon.tick(dt)
            self.water.step()
            if self.survival:
                self._update_survival(dt)
            self._couple_entities()
            self._integrate_entities()
            self._resolve_collisions()
            self._update_enemies(dt)
            self._update_projectiles(dt)
            self._update_explosions(dt)
            self._check_end_conditions()
            self._render()
            self._frame += 1
            if self._frame % self.fps == 0:
                self._print_positions()
            self.clock.tick(self.fps)
            
        # pygame.quit() is gone from here so the window stays alive for the menu!
        return self._result or "quit"

    # ── Per-frame printing ─────────────────────────────────────────────────────
    def _print_positions(self):
        t = self._frame // self.fps
        print(f"[t={t:>4}s]", end="")
        for i, e in enumerate(self.entities):
            tag    = "player" if e.controllable else (e.name or (f"obstacle" if e.static else f"entity{i}"))
            status = f"hp={e.hp:.0f}/{e.max_hp:.0f}" if not e.static else "static"
            print(f"  {tag}:({e.x:.0f},{e.y:.0f}) {status}", end="")
        print()

    # ── Survival mode ─────────────────────────────────────────────────────────
    def _update_survival(self, dt: float):
        """Apply leftward current (player only), scroll water grid, tick timer."""
        if self.player and self.player.alive:
            self.player.ax -= self._current_force

        self._scroll_accum += self._scroll_speed * dt
        while self._scroll_accum >= 1.0:
            self.water.h      = np.roll(self.water.h,      -1, axis=1)
            self.water.h_prev = np.roll(self.water.h_prev, -1, axis=1)
            self._scroll_accum -= 1.0

        self._survival_t -= dt
        if self._survival_t <= 0:
            self._survival_t = 0.0
            self._result  = "win"
            self.running  = False
            self._show_overlay("SURVIVED!", (40, 200, 80))

    # ── End conditions ─────────────────────────────────────────────────────────
    def _check_end_conditions(self):
        if self.player is None or self._result is not None:
            return
        if not self.player.alive:
            self._result = "lose"
            self.running = False
            self._show_overlay("GAME OVER", (200, 40, 40))
            return
        if self.flag_pos is not None:
            dx = self.player.x - self.flag_pos[0]
            dy = self.player.y - self.flag_pos[1]
            dx -= self.width  * round(dx / self.width)
            dy -= self.height * round(dy / self.height)
            if math.hypot(dx, dy) < self.flag_radius:
                self._result = "win"
                self.running = False
                self._show_overlay("YOU WIN!", (40, 200, 80))

    def _show_overlay(self, text: str, color: tuple):
        """Dark overlay with centered text; waits for any key/click before returning."""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        big  = pygame.font.SysFont(None, 90)
        sub  = pygame.font.SysFont(None, 34)
        lbl  = big.render(text, True, color)
        hint = sub.render("Press any key to continue", True, (200, 200, 200))
        self.screen.blit(lbl,  (self.width // 2 - lbl.get_width()  // 2,
                                 self.height // 2 - lbl.get_height() // 2 - 30))
        self.screen.blit(hint, (self.width // 2 - hint.get_width()  // 2,
                                 self.height // 2 + 50))
        pygame.display.flip()
        pygame.time.wait(400)
        
        # Clear the queue so we don't accidentally skip the menu
        pygame.event.clear() 
        
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    waiting = False
        
        # Crucial: Clear again so the next level doesn't "see" the click 
        # that closed this overlay as a "fire" or "click" command.
        pygame.event.clear()

    # ── Events & input ─────────────────────────────────────────────────────────
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit() # Cleanly shut down pygame
                sys.exit()    # Kill the entire Python process
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                # Left click fires the player weapon (if any); right click always splashes
                if event.button != 1 or self.player_weapon is None:
                    self.water.splash(mx / CELL_W, my / CELL_H, SPLASH_AMP, SPLASH_R)

    def _handle_input(self):
        if self.player is None or not self.player.alive:
            return
        keys  = pygame.key.get_pressed()
        accel = 300.0
        dt    = 1.0 / self.fps
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: self.player.vx -= accel * dt
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.player.vx += accel * dt
        if keys[pygame.K_UP]    or keys[pygame.K_w]: self.player.vy -= accel * dt
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: self.player.vy += accel * dt
        spd = math.hypot(self.player.vx, self.player.vy)
        if spd > 200.0:
            self.player.vx *= 200.0 / spd
            self.player.vy *= 200.0 / spd

        # Hold left mouse button to fire weapon toward cursor
        if (self.player_weapon and self.player.alive
                and pygame.mouse.get_pressed()[0]):
            mx, my = pygame.mouse.get_pos()
            angle  = math.atan2(my - self.player.y, mx - self.player.x)
            projs  = self.player_weapon.fire(self.player.x, self.player.y, angle)
            for p in projs:
                p.hits.add(id(self.player))   # can't damage yourself
            self.projectiles.extend(projs)

    # ── Water–entity coupling ──────────────────────────────────────────────────
    def _couple_entities(self):
        dt = 1.0 / self.fps
        for e in self.entities:
            if e.static or not e.alive:
                continue
            gx = e.x / CELL_W;  gy = e.y / CELL_H
            gr = e.radius / max(CELL_W, CELL_H)
            self.water.splash(gx, gy, -DISPLACE_AMP * e.mass, gr)
            spd = math.hypot(e.vx, e.vy)
            if spd > 5.0:
                self.water.splash(gx, gy, RIPPLE_AMP * spd * dt, max(gr * 0.6, 0.5))
            dx_w, dy_w = self.water.gradient_at(gx, gy)
            e.ax += -WAVE_GRAD_K * dx_w / e.mass
            e.ay += -WAVE_GRAD_K * dy_w / e.mass
            e.vx *= 1.0 - DRAG_K
            e.vy *= 1.0 - DRAG_K

    def _integrate_entities(self):
        dt = 1.0 / self.fps
        for e in self.entities:
            if e.static or not e.alive:
                e.ax = e.ay = 0.0;  continue
            e.vx += e.ax * dt;  e.vy += e.ay * dt
            if self.survival:
                e.x += e.vx * dt
                e.y  = (e.y + e.vy * dt) % self.height
                if e.x < 0:
                    e.hp = 0.0          # swept off the left edge → dead
                elif e.x > self.width:
                    e.x = float(self.width)
            else:
                e.x = (e.x + e.vx * dt) % self.width
                e.y = (e.y + e.vy * dt) % self.height
            e.ax = 0.0;  e.ay = 0.0

    def _resolve_collisions(self):
        for i, a in enumerate(self.entities):
            if not a.alive: continue
            for b in self.entities[i + 1:]:
                if not b.alive: continue
                ddx = b.x - a.x;  ddx -= self.width  * round(ddx / self.width)
                ddy = b.y - a.y;  ddy -= self.height * round(ddy / self.height)
                dist = math.hypot(ddx, ddy)
                min_dist = a.radius + b.radius
                if dist >= min_dist or dist < 1e-6: continue
                nx = ddx / dist;  ny = ddy / dist
                overlap = min_dist - dist
                if not a.static:
                    a.x = (a.x - nx * overlap * (0.5 if not b.static else 1.0)) % self.width
                    a.y = (a.y - ny * overlap * (0.5 if not b.static else 1.0)) % self.height
                if not b.static:
                    b.x = (b.x + nx * overlap * (0.5 if not a.static else 1.0)) % self.width
                    b.y = (b.y + ny * overlap * (0.5 if not a.static else 1.0)) % self.height
                rel_vn = (b.vx - a.vx) * nx + (b.vy - a.vy) * ny
                if rel_vn >= 0: continue
                impact = abs(rel_vn)
                if a.static:
                    b.vx -= (1 + RESTITUTION) * rel_vn * nx
                    b.vy -= (1 + RESTITUTION) * rel_vn * ny
                elif b.static:
                    a.vx += (1 + RESTITUTION) * rel_vn * nx
                    a.vy += (1 + RESTITUTION) * rel_vn * ny
                else:
                    j = -(1 + RESTITUTION) * rel_vn / (1 / a.mass + 1 / b.mass)
                    a.vx -= j / a.mass * nx;  a.vy -= j / a.mass * ny
                    b.vx += j / b.mass * nx;  b.vy += j / b.mass * ny
                dmg = impact * COLLISION_DMG_K
                if not a.static: a.hp = max(0.0, a.hp - dmg)
                if not b.static: b.hp = max(0.0, b.hp - dmg)
                cx = (a.x + ddx * 0.5) % self.width
                cy = (a.y + ddy * 0.5) % self.height
                self.water.splash(cx / CELL_W, cy / CELL_H, impact * COLLISION_SPLASH, 3)

    # ── Enemy AI ───────────────────────────────────────────────────────────────
    def _update_enemies(self, dt: float):
        for enemy in self.enemies:
            # Only update living enemies
            if enemy.alive:
                # Call the new tick_ai method we wrote in enemy.py
                new_projs = enemy.tick_ai(self.player, dt)
                self.projectiles.extend(new_projs)

    # ── Projectiles ────────────────────────────────────────────────────────────
    def _torus_dist(self, ax, ay, bx, by) -> float:
        dx = bx - ax;  dx -= self.width  * round(dx / self.width)
        dy = by - ay;  dy -= self.height * round(dy / self.height)
        return math.hypot(dx, dy)

    def _update_projectiles(self, dt: float):
        alive = []
        for proj in self.projectiles:
            proj.lifetime -= dt
            if proj.lifetime <= 0:
                if proj.explodes:
                    self._do_explosion(proj)
                continue

            # Move — torus wrap in normal mode; hard boundary in survival
            proj.x += proj.vx * dt
            proj.y += proj.vy * dt
            if self.survival:
                if proj.x < 0 or proj.x > self.width:
                    if proj.explodes:
                        self._do_explosion(proj)
                    continue
                proj.y %= self.height
            else:
                proj.x %= self.width
                proj.y %= self.height

            # Hit-test against all living non-static entities
            killed = False
            for e in self.entities:
                if not e.alive or e.static or id(e) in proj.hits:
                    continue
                if self._torus_dist(proj.x, proj.y, e.x, e.y) <= e.radius:
                    # Compute actual damage
                    if proj.shotgun:
                        traveled = self._torus_dist(proj.origin_x, proj.origin_y,
                                                    proj.x, proj.y)
                        dmg = proj.damage * max(0.1, 1.0 - traveled / proj.shotgun_range)
                    else:
                        dmg = proj.damage
                    e.hp = max(0.0, e.hp - dmg)
                    proj.hits.add(id(e))
                    # Wave ripple at impact
                    self.water.splash(proj.x / CELL_W, proj.y / CELL_H, 0.8, 2)
                    if not proj.pierce:
                        killed = True
                        if proj.explodes:
                            self._do_explosion(proj)
                        break

            if not killed:
                alive.append(proj)

        self.projectiles = alive

    def _do_explosion(self, proj: Projectile):
        """Apply AoE damage, water splash, and schedule a visual flash."""
        for e in self.entities:
            if not e.alive or e.static:
                continue
            d = self._torus_dist(proj.x, proj.y, e.x, e.y)
            if d < proj.explosion_radius:
                dmg = proj.explosion_damage * max(0.0, 1.0 - d / proj.explosion_radius)
                e.hp = max(0.0, e.hp - dmg)
        self.water.splash(proj.x / CELL_W, proj.y / CELL_H, 3.0, 12)
        self._explosions.append({
            "x": proj.x, "y": proj.y,
            "r": 4, "max_r": int(proj.explosion_radius),
            "t": 0.35, "max_t": 0.35,
        })

    def _update_explosions(self, dt: float):
        self._explosions = [e for e in self._explosions
                            if (e.__setitem__("t", e["t"] - dt) or True) and e["t"] > 0]

    # ── Rendering ──────────────────────────────────────────────────────────────
    def _draw_entity_at(self, e: Entity, sx: int, sy: int):
        r = int(e.radius)
        if not e.alive:
            pygame.draw.circle(self.screen, (80, 80, 80), (sx, sy), r)
            pygame.draw.circle(self.screen, (50, 50, 50), (sx, sy), r, 2)
            return
            
        # --- Handle Visuals ---
        if e.controllable:
            # Player Boat
            mx, my = pygame.mouse.get_pos()
            aim_angle = math.atan2(my - sy, mx - sx)
            weapon_name = type(self.player_weapon).__name__ if self.player_weapon else "pistol"
            
            PlayerVisual.draw(self.screen, sx, sy, aim_angle, weapon_name)
            
        else:
            # Custom Enemy Boat
            is_custom = EnemyVisual.draw(self.screen, e.name, sx, sy, r, e.vx, e.vy)
            
            # Fallback for un-designed entities or bullets
            # Fallback for un-designed entities or bullets
            if not is_custom:
                name_lower = (e.name or "").lower()
                is_bullet = any(word in name_lower for word in ["bullet", "projectile", "shot", "pellet", "shell", "laser", "rocket"])
                
                # 1. Define it up here so it ALWAYS exists, no matter what!
                w_type = "pistol" 
                
                if is_bullet:
                    # 1. FORCE the variable to exist right here!
                    w_type = "pistol" 
                    
                    # 2. Check the names to see if we need to change it
                    if "sniper" in name_lower:
                        w_type = "sniper"
                    elif "machine" in name_lower or "gunner" in name_lower:
                        w_type = "machine_gun"
                    elif "rocket" in name_lower or "bazooka" in name_lower:
                        w_type = "rocket_launcher"
                    elif "shotgun" in name_lower or "pellet" in name_lower or "breacher" in name_lower:
                        w_type = "shotgun"

                    # 3. Draw the bullet!
                    BulletVisual.draw(self.screen, sx, sy, e.color, r, (e.vx, e.vy), False, w_type)
                else:
                    # 4. Standard basic shapes for obstacles or unknown objects
                    pygame.draw.circle(self.screen, e.color, (sx, sy), r)
                    if e.static:
                        pygame.draw.circle(self.screen, (200, 180, 140), (sx, sy), r, 2)
                    else:
                        pygame.draw.circle(self.screen, (180, 180, 180), (sx, sy), r, 1)

        # --- Health Bars and Names ---
        if not e.static:
            bar_w = max(r * 2, 20);  bar_h = 5
            bx    = sx - bar_w // 2;  by = sy - r - 12
            pygame.draw.rect(self.screen, (60, 15, 15), (bx-1, by-1, bar_w+2, bar_h+2))
            frac   = e.hp / e.max_hp;  fill_w = max(0, int(bar_w * frac))
            color  = (30,200,30) if frac > 0.5 else (230,160,0) if frac > 0.25 else (210,30,30)
            if fill_w > 0:
                pygame.draw.rect(self.screen, color, (bx, by, fill_w, bar_h))
            if e.name:
                lbl = self._font.render(e.name, True, (220, 220, 220))
                self.screen.blit(lbl, (sx - lbl.get_width()//2, by - 14))

    def _render(self):
        # Water surface
        h_norm = np.clip(self.water.h / SPLASH_AMP, -1.0, 1.0) * 0.5 + 0.5
        t_low  = np.clip(h_norm * 2.0,         0.0, 1.0)[..., np.newaxis]
        t_high = np.clip((h_norm - 0.5) * 2.0, 0.0, 1.0)[..., np.newaxis]
        color_grid = (
            (1.0 - t_low) * COLOR_DEEP + t_low * COLOR_SHALLOW
            - t_high * COLOR_SHALLOW   + t_high * COLOR_CREST
        ).astype(np.uint8)
        upscaled = np.repeat(np.repeat(color_grid, CELL_H, axis=0), CELL_W, axis=1)
        np.copyto(self._pixel_buf, upscaled.transpose(1, 0, 2))
        pygame.surfarray.blit_array(self._water_surf, self._pixel_buf)
        self.screen.blit(self._water_surf, (0, 0))

        # Entities — full torus ghosts normally; Y-only in survival (no left/right wrap)
        ox_offsets = (0,) if self.survival else (0, self.width, -self.width)
        for e in self.entities:
            cx, cy = int(e.x), int(e.y);  r = int(e.radius)
            for ox in ox_offsets:
                sx = cx + ox
                if sx + r < 0 or sx - r >= self.width: continue
                for oy in (0, self.height, -self.height):
                    sy = cy + oy
                    if sy + r < 0 or sy - r >= self.height: continue
                    self._draw_entity_at(e, sx, sy)

        # Projectiles — same ghost logic
        # --- (Inside _render method) ---
        # Projectiles — Rendered using specialized visuals from bullet.py
        # Projectiles — Rendered using specialized visuals from bullet.py
        for proj in self.projectiles:
            px, py = proj.x, proj.y
            pr = int(proj.radius or 3)
            p_color = proj.color or (255, 255, 255)

            # Look up the weapon type from the Projectile dataclass
            fired_by = getattr(proj, "weapon_type", "standard") 

            for ox in ox_offsets:
                for oy in (0, self.height, -self.height):
                    sx, sy = px + ox, py + oy
                    if -20 < sx < self.width + 20 and -20 < sy < self.height + 20:
                        
                        # Fix: We must use p_color, pr, proj.vx/vy, and fired_by here!
                        BulletVisual.draw(
                            self.screen, 
                            sx, sy, 
                            p_color, 
                            pr, 
                            (proj.vx, proj.vy), 
                            False, 
                            fired_by
                        )

            for ox in ox_offsets:
                for oy in (0, self.height, -self.height):
                    sx, sy = px + ox, py + oy
                    if -20 < sx < self.width + 20 and -20 < sy < self.height + 20:
                        
                        # Fix: explicitly set is_explosion=False so the custom rocket draws!
                        BulletVisual.draw(self.screen, sx, sy, p_color, pr, (proj.vx, proj.vy), False, fired_by)

        # Explosions — Re-designed to match the vector burst pattern from image_0075f5.png
        # Layers: Translucent Cyan splinters -> Red spikes -> Orange spikes -> Hot core
        for ex in self._explosions:
            progress = 1.0 - (ex["t"] / ex["max_t"])
            alpha = max(0, min(255, int(255 * (ex["t"] / ex["max_t"]))))
            
            # The burst extends slightly past the max radius due to jagged points
            draw_max_r = int(ex["max_r"] * 1.3)
            s = pygame.Surface((draw_max_r * 2, draw_max_r * 2), pygame.SRCALPHA)
            cx, cy = draw_max_r, draw_max_r # Local center on surface

            # Colors from the digital burst image
            color_cyan = (0, 220, 255)
            color_red = (220, 40, 20)
            color_orange = (255, 140, 0)
            color_white_hot = (255, 255, 230)

            # --- LAYER 1: Cyan splinters (Outer Translucent Spikes) ---
            r1 = int(ex["r"] + (ex["max_r"] - ex["r"]) * progress)
            # Lines fade out slightly slower than filled areas
            line_alpha = max(0, min(255, int(alpha * 1.2))) 
            
            num_splinters = 20
            pygame.draw.circle(s, (color_cyan[0], color_cyan[1], color_cyan[2], alpha // 10), (cx, cy), r1)
            
            # Use fixed random angles per explosion ID/time to prevent vibration (using t as seed)
            rng_seed = int(ex["x"] * 1000 + ex["y"]) # Create a mostly unique integer seed
            random.seed(rng_seed) 
            
            for _ in range(num_splinters):
                angle = random.uniform(0, 2 * math.pi)
                # Deviate length of each splinter
                l_dev = random.uniform(0.7, 1.2)
                l = int(r1 * l_dev)
                ex_pt = (cx + math.cos(angle) * l, cy + math.sin(angle) * l)
                
                # Deviate start distance from core
                s_dev = random.uniform(0.1, 0.4)
                sl = int(r1 * s_dev)
                st_pt = (cx + math.cos(angle) * sl, cy + math.sin(angle) * sl)
                
                # Outer cyan lines (thinner)
                pygame.draw.line(s, (color_cyan[0], color_cyan[1], color_cyan[2], line_alpha // 2), st_pt, ex_pt, 2)
                
                # Inner segment is orange (matching image where base of splinters is hot)
                il = int(r1 * (s_dev + random.uniform(0.1, 0.3)))
                in_pt = (cx + math.cos(angle) * il, cy + math.sin(angle) * il)
                pygame.draw.line(s, (color_orange[0], color_orange[1], color_orange[2], line_alpha), st_pt, in_pt, 2)

            # Reset random for filled shapes to maintain static jaggedness
            random.seed(rng_seed) 

            # --- LAYER 2: Main Fireball (Jagged Polygon for Red/Orange Core) ---
            # Using polygons instead of circles creates the digital vector fire look
            num_jagged = 16
            
            def get_jagged_pts(base_r, irregularity):
                """Helper to make an irregular polygon."""
                pts = []
                for i in range(num_jagged):
                    t_angle = i * (2 * math.pi / num_jagged)
                    dev = random.uniform(1.0 - irregularity, 1.0 + irregularity)
                    tr = max(2, int(base_r * dev))
                    tx = cx + math.cos(t_angle) * tr
                    ty = cy + math.sin(t_angle) * tr
                    pts.append((tx, ty))
                return pts

            # Outer jagged Fire (Red)
            r_red = max(1, int(r1 * 0.8))
            red_pts = get_jagged_pts(r_red, 0.25)
            if len(red_pts) > 2:
                pygame.draw.polygon(s, (color_red[0], color_red[1], color_red[2], alpha), red_pts)

            # Mid jagged Fire (Orange)
            r_orange = max(1, int(r1 * 0.6))
            orange_pts = get_jagged_pts(r_orange, 0.2)
            if len(orange_pts) > 2:
                pygame.draw.polygon(s, (color_orange[0], color_orange[1], color_orange[2], alpha), orange_pts)

            # Reset random one last time for core
            random.seed(rng_seed) 

            # --- LAYER 3: White Hot Core ---
            # Concentrated white hot energy center, fades faster than smoke
            core_alpha = int(255 * max(0.0, min(1.0, 1.5 - (progress * 2.5))))
            if core_alpha > 0:
                r_core = max(1, int(r1 * 0.35))
                pygame.draw.circle(s, (color_white_hot[0], color_white_hot[1], color_white_hot[2], core_alpha), (cx, cy), r_core)
                
                # Small spike detail for core (White)
                num_spikes = 6
                sl_core = int(r_core * 1.5)
                for _ in range(num_spikes):
                    angle = random.uniform(0, 2 * math.pi)
                    pt_far = (cx + math.cos(angle) * sl_core, cy + math.sin(angle) * sl_core)
                    pygame.draw.line(s, (color_white_hot[0], color_white_hot[1], color_white_hot[2], core_alpha), (cx, cy), pt_far, 3)

            # Draw to screen (with proper screen-wrap offset self-managed by surface size)
            # Because surface is now larger (draw_max_r), use that to offset blit
            self.screen.blit(s, (int(ex["x"]) - draw_max_r, int(ex["y"]) - draw_max_r))

        # Flag / Goal
        if self.flag_pos:
            fx, fy = self.flag_pos
            pygame.draw.circle(self.screen, (255, 255, 0), (int(fx), int(fy)), int(self.flag_radius), 2)

        # UI Overlay (Timer/Score)
        if self.survival:
            timer_text = self._font.render(f"TIME: {int(self._survival_t)}s", True, (255, 255, 255))
            self.screen.blit(timer_text, (20, 20))

        # IMPORTANT: This must be at the very end of the loop in run() or end of _render
        pygame.display.flip()