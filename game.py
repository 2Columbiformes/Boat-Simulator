import math
import pygame
import numpy as np

from water import (WaterGrid, WIDTH, HEIGHT, GRID_W, GRID_H,
                   CELL_W, CELL_H, FPS,
                   WAVE_GRAD_K, DRAG_K, DISPLACE_AMP, RIPPLE_AMP,
                   SPLASH_AMP, SPLASH_R,
                   COLOR_DEEP, COLOR_SHALLOW, COLOR_CREST)
from entity import Entity
from weapon import Projectile
from enemy import Enemy

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
        self.entities.append(enemy.entity)
        return enemy

    # ── Main loop ──────────────────────────────────────────────────────────────
    def run(self) -> str:
        dt = 1.0 / self.fps
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
        pygame.quit()
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
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.QUIT):
                    waiting = False

    # ── Events & input ─────────────────────────────────────────────────────────
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
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
            new_projs = enemy.update(dt, self.player, self.water)
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
        pygame.draw.circle(self.screen, e.color, (sx, sy), r)
        if e.controllable:
            pygame.draw.circle(self.screen, (255, 255, 255), (sx, sy), r, 2)
        elif e.static:
            pygame.draw.circle(self.screen, (200, 180, 140), (sx, sy), r, 2)
        else:
            pygame.draw.circle(self.screen, (180, 180, 180), (sx, sy), r, 1)
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
        for proj in self.projectiles:
            px, py = int(proj.x), int(proj.y)
            pr = 5 if proj.explodes else 3
            for ox in ox_offsets:
                sx = px + ox
                if sx + pr < 0 or sx - pr >= self.width: continue
                for oy in (0, self.height, -self.height):
                    sy = py + oy
                    if sy + pr < 0 or sy - pr >= self.height: continue
                    pygame.draw.circle(self.screen, proj.color, (sx, sy), pr)

        # Flag
        if self.flag_pos is not None:
            fx, fy   = int(self.flag_pos[0]), int(self.flag_pos[1])
            pygame.draw.line(self.screen, (220, 220, 220), (fx, fy + 16), (fx, fy - 20), 3)
            pygame.draw.polygon(self.screen, (50, 220, 80),
                                [(fx, fy - 20), (fx + 18, fy - 13), (fx, fy - 6)])
            pulse_r = int(self.flag_radius) + 4 + int(4 * math.sin(self._frame * 0.15))
            pygame.draw.circle(self.screen, (50, 220, 80), (fx, fy), pulse_r, 2)

        # Explosion flashes
        for exp in self._explosions:
            frac = exp["t"] / exp["max_t"]
            r    = int(exp["r"] + (exp["max_r"] - exp["r"]) * (1 - frac))
            alpha = int(200 * frac)
            surf  = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 140, 20, alpha), (r, r), r)
            self.screen.blit(surf, (int(exp["x"]) - r, int(exp["y"]) - r))

        # Player weapon HUD (bottom-left)
        if self.player_weapon:
            wname  = type(self.player_weapon).__name__
            max_cd = 1.0 / max(self.player_weapon.fire_rate, 1e-9)
            frac   = 1.0 - min(self.player_weapon._cooldown / max_cd, 1.0)
            bar_w, bar_h = 120, 8
            bx = 10;  by = self.height - 30
            pygame.draw.rect(self.screen, (40, 40, 40),    (bx, by, bar_w, bar_h))
            fill_c = (50, 220, 80) if self.player_weapon.ready else (220, 160, 30)
            pygame.draw.rect(self.screen, fill_c,           (bx, by, int(bar_w * frac), bar_h))
            pygame.draw.rect(self.screen, (150, 150, 150),  (bx, by, bar_w, bar_h), 1)
            lbl = self._font.render(wname, True, (220, 220, 220))
            self.screen.blit(lbl, (bx, by - 16))

        # Survival HUD
        if self.survival:
            mins  = int(self._survival_t) // 60
            secs  = int(self._survival_t) % 60
            tc    = (255, 80, 80) if self._survival_t < 30 else (255, 220, 80)
            hud   = self._font.render(f"Survive: {mins}:{secs:02d}", True, tc)
            self.screen.blit(hud, (self.width // 2 - hud.get_width() // 2, 8))
            # Left-edge danger vignette when player is close to the deadly left boundary
            if self.player and self.player.x < 150:
                alpha = int(180 * max(0.0, 1.0 - self.player.x / 150.0))
                edge  = pygame.Surface((60, self.height), pygame.SRCALPHA)
                edge.fill((200, 20, 20, alpha))
                self.screen.blit(edge, (0, 0))

        pygame.display.flip()
