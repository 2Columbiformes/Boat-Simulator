import math
import random
import pygame
import numpy as np

from water import (WaterGrid, WIDTH, HEIGHT, WORLD_W, WORLD_H,
                   GRID_W, GRID_H, CELL_W, CELL_H, FPS,
                   WAVE_GRAD_K, DRAG_K, DISPLACE_AMP, RIPPLE_AMP,
                   SPLASH_AMP, SPLASH_R,
                   COLOR_DEEP, COLOR_MID, COLOR_SHALLOW, COLOR_FOAM, COLOR_CREST)
from entity import Entity
from weapon import Projectile
from enemy import (Enemy,
                   make_drift, make_chaser, make_sniper, make_artillery, make_patrol,
                   make_boss)
from bullet import BulletVisual
from player_visual import PlayerVisual

_SPAWN_FACTORIES = {
    "drift":     make_drift,
    "chase":     make_chaser,
    "snipe":     make_sniper,
    "artillery": make_artillery,
    "patrol":    make_patrol,
}

# ── Collision constants (kept here as they belong to the game loop) ────────────
RESTITUTION      = 0.35
COLLISION_DMG_K  = 0.25
COLLISION_SPLASH = 0.001


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
                 current_force: float = 90.0, scroll_speed: float = 5.0,
                 enemy_budget: int = 0, spawn_pool=None,
                 topology: str = "torus",
                 entity_barriers: bool = False,
                 no_obstacle_damage: bool = False):
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
        self.zoom        = 1.0          # 1.0 = normal; >1 = zoomed in

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
        self._obstacle_cells: dict = {}   # id(entity) -> (gx, gy, gr)

        # World / camera (world is larger than the viewport)
        self.world_w = WORLD_W
        self.world_h = WORLD_H
        self.cam_x   = 0.0
        self.cam_y   = 0.0

        # Player weapon (assigned externally before run())
        self.player_weapon = None

        # Topology: "torus" = wrap-around edges; "bounded" = solid walls
        self.topology           = topology
        self.entity_barriers    = entity_barriers
        self.no_obstacle_damage = no_obstacle_damage
        self._splash_cooldown   = 0.0

        # Continuous enemy spawning
        self.enemy_budget = enemy_budget
        self.spawn_pool   = list(spawn_pool) if spawn_pool else []
        self._spawn_timer = 3.0   # seconds until first auto-spawn

    # ── Public API ─────────────────────────────────────────────────────────────
    def add_entity(self, x: float, y: float, **kwargs) -> Entity:
        """
        Add a bare entity (player, static obstacle, etc.).
        kwargs: mass, radius, color, vx, vy, max_hp, static, controllable, name, wave_grad_k
        """
        e = Entity(x=x, y=y, **kwargs)
        if e.static:
            gx = x / CELL_W;  gy = y / CELL_H
            gr = e.radius / max(CELL_W, CELL_H) + 1
            self.water.set_obstacle(gx, gy, gr)
            self._obstacle_cells[id(e)] = (gx, gy, gr)
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
            self._cleanup_dead_enemies()
            self._cleanup_dead_obstacles()
            self._maybe_spawn_enemy(dt)
            self._update_projectiles(dt)
            self._update_explosions(dt)
            self._check_end_conditions()
            self._update_camera()
            self._render()
            self._frame += 1
            if self._frame % self.fps == 0:
                self._print_positions()
            self.clock.tick(self.fps)
        return self._result or "quit"

    # ── Per-frame printing ─────────────────────────────────────────────────────
    def _print_positions(self):
        t = self._frame // self.fps
        print(f"[t={t:>4}s]", end="")
        for i, e in enumerate(self.entities):
            tag    = "player" if e.controllable else (e.name or (f"obstacle" if e.static else f"entity{i}"))
            status = f"hp={e.hp:.0f}/{e.max_hp:.0f}" if not e.static else "static"
            print(f"  {tag}:({e.x:.0f},{e.y:.0f}) {status}", end="")
        # Water diagnostics: print min/max height every second to detect blowup
        try:
            hmin = float(self.water.h.min())
            hmax = float(self.water.h.max())
            print(f"  water:hmin={hmin:.6g},hmax={hmax:.6g}")
            # flag unusually large values
            if abs(hmin) > 0.5 or abs(hmax) > 0.5:
                print("  WARNING: large water heights detected — possible numerical blowup")
        except Exception:
            print()

    # ── Camera ────────────────────────────────────────────────────────────────
    def _update_camera(self):
        if self.player is None:
            return
        min_zoom = max(self.width / self.world_w, self.height / self.world_h)
        half_w   = self.width  / (2.0 * self.zoom)
        half_h   = self.height / (2.0 * self.zoom)
        if self.survival and self._current_force > 0:
            # Classic scrolling survival: clamp x so player can't go off the right
            target_x = max(0.0, min(self.player.x - half_w,
                                    self.world_w - self.width / self.zoom))
            target_y = self.player.y - half_h
            self.cam_x += (target_x - self.cam_x) * 0.08
            self.cam_y += (target_y - self.cam_y) * 0.08
        elif self.zoom <= min_zoom * 1.001:
            self.cam_x += (0.0 - self.cam_x) * 0.08
            self.cam_y += (0.0 - self.cam_y) * 0.08
        elif self.topology == "bounded" or self.entity_barriers:
            max_cam_x = max(0.0, self.world_w - self.width  / self.zoom)
            max_cam_y = max(0.0, self.world_h - self.height / self.zoom)
            target_x = max(0.0, min(self.player.x - half_w, max_cam_x))
            target_y = max(0.0, min(self.player.y - half_h, max_cam_y))
            self.cam_x += (target_x - self.cam_x) * 0.08
            self.cam_y += (target_y - self.cam_y) * 0.08
        else:  # torus (and survival-without-current): wrapping camera
            target_x = self.player.x - half_w
            target_y = self.player.y - half_h
            dx = target_x - self.cam_x
            dy = target_y - self.cam_y
            dx -= self.world_w * round(dx / self.world_w)
            dy -= self.world_h * round(dy / self.world_h)
            self.cam_x += dx * 0.08
            self.cam_y += dy * 0.08

    def _w2s(self, wx: float, wy: float):
        """World → screen (float) coords."""
        if self.survival and self._current_force > 0:
            sx = wx - self.cam_x
            sy = (wy - self.cam_y) % self.world_h
        elif self.topology == "bounded" or self.entity_barriers:
            sx = wx - self.cam_x
            sy = wy - self.cam_y
        else:  # torus (and survival-without-current)
            sx = (wx - self.cam_x) % self.world_w
            sy = (wy - self.cam_y) % self.world_h
        return sx * self.zoom, sy * self.zoom

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
            if self.topology != "bounded" and not self.entity_barriers:
                dx -= self.world_w * round(dx / self.world_w)
                dy -= self.world_h * round(dy / self.world_h)
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
            elif event.type == pygame.MOUSEWHEEL:
                factor = 1.1 if event.y > 0 else (1.0 / 1.1)
                min_zoom = max(self.width / self.world_w, self.height / self.world_h)
                self.zoom = max(min_zoom, min(4.0, self.zoom * factor))
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                # Left click without a weapon → one-shot splash
                if event.button == 1 and self.player_weapon is None:
                    wx = ((mx / self.zoom) + self.cam_x) % self.world_w
                    wy = ((my / self.zoom) + self.cam_y) % self.world_h
                    self.water.splash(wx / CELL_W, wy / CELL_H, SPLASH_AMP, SPLASH_R)

    def _handle_input(self):
        if self.player is None or not self.player.alive:
            return
        keys  = pygame.key.get_pressed()
        accel = 150.0
        dt    = 1.0 / self.fps
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: self.player.vx -= accel * dt
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.player.vx += accel * dt
        if keys[pygame.K_UP]    or keys[pygame.K_w]: self.player.vy -= accel * dt
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: self.player.vy += accel * dt
        spd = math.hypot(self.player.vx, self.player.vy)
        if spd > 200.0:
            self.player.vx *= 200.0 / spd
            self.player.vy *= 200.0 / spd

        # Right mouse button held: splash every 0.5 s
        self._splash_cooldown -= dt
        if pygame.mouse.get_pressed()[2] and self._splash_cooldown <= 0:
            mx, my = pygame.mouse.get_pos()
            wx = ((mx / self.zoom) + self.cam_x) % self.world_w
            wy = ((my / self.zoom) + self.cam_y) % self.world_h
            self.water.splash(wx / CELL_W, wy / CELL_H, SPLASH_AMP, SPLASH_R)
            self._splash_cooldown = 0.1

        # Hold left mouse button to fire weapon toward cursor
        if (self.player_weapon and self.player.alive
                and pygame.mouse.get_pressed()[0]):
            mx, my = pygame.mouse.get_pos()
            # Direction: compute player's screen position using _w2s and aim toward mouse
            psx, psy = self._w2s(self.player.x, self.player.y)
            angle  = math.atan2(my - psy, mx - psx)
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
            gx = e.x / CELL_W;  
            gy = e.y / CELL_H
            gr = e.radius / max(CELL_W, CELL_H)
            self.water.splash(gx, gy, -DISPLACE_AMP * e.mass, gr)
            spd = math.hypot(e.vx, e.vy)
            # Enemies create much weaker ripples to avoid saturating the grid
            ripple = RIPPLE_AMP #* (1.0 if e.controllable else 0.12)
            if spd > 5.0:
                self.water.splash(gx, gy, ripple * spd * dt, max(gr * 0.6, 0.5))
            dx_w, dy_w = self.water.gradient_at(gx, gy)
            # Use per-entity wave coupling strength
            grad_k = WAVE_GRAD_K * e.wave_grad_k
            e.ax += -grad_k * dx_w / e.mass
            e.ay += -grad_k * dy_w / e.mass
            e.vx *= 1.0 - DRAG_K
            e.vy *= 1.0 - DRAG_K

    def _integrate_entities(self):
        dt = 1.0 / self.fps
        for e in self.entities:
            if e.static or not e.alive:
                e.ax = e.ay = 0.0;  continue
            e.vx += e.ax * dt;  e.vy += e.ay * dt
            if self.survival and self._current_force > 0:
                # u
                e.x  = (e.x + e.vx * dt) % self.world_w
                e.y  = (e.y + e.vy * dt) % self.world_h
                if e.x < 0:
                    e.x = float(self.world_w)
                elif e.x > self.world_w:
                    e.x = float(self.world_w)
            elif self.topology == "bounded" or self.entity_barriers:
                e.x += e.vx * dt;  e.y += e.vy * dt
                if e.x < e.radius:              
                    e.x = e.radius
                    e.vx = abs(e.vx)
                elif e.x > self.world_w - e.radius: 
                    e.x = self.world_w - e.radius
                    e.vx = -abs(e.vx)
                if e.y < e.radius:              
                    e.y = e.radius
                    e.vy = abs(e.vy)
                elif e.y > self.world_h - e.radius: e.y = self.world_h - e.radius; e.vy = -abs(e.vy)
            else:  # wrap both axes
                e.x = (e.x + e.vx * dt) % self.world_w
                e.y = (e.y + e.vy * dt) % self.world_h
            e.ax = 0.0;  e.ay = 0.0

    def _resolve_collisions(self):
        torus = self.topology != "bounded" and not (self.survival and self._current_force > 0)
        for i, a in enumerate(self.entities):
            if not a.alive: continue
            for b in self.entities[i + 1:]:
                if not b.alive: continue
                ddx = b.x - a.x
                ddy = b.y - a.y
                if torus:
                    ddx -= self.world_w * round(ddx / self.world_w)
                    ddy -= self.world_h * round(ddy / self.world_h)
                dist = math.hypot(ddx, ddy)
                min_dist = a.radius + b.radius
                if dist >= min_dist or dist < 1e-6: continue
                nx = ddx / dist;  ny = ddy / dist
                overlap = min_dist - dist
                if not a.static:
                    if torus:
                        a.x = (a.x - nx * overlap * (0.5 if not b.static else 1.0)) % self.world_w
                        a.y = (a.y - ny * overlap * (0.5 if not b.static else 1.0)) % self.world_h
                    else:
                        a.x -= nx * overlap * (0.5 if not b.static else 1.0)
                        a.y -= ny * overlap * (0.5 if not b.static else 1.0)
                if not b.static:
                    if torus:
                        b.x = (b.x + nx * overlap * (0.5 if not a.static else 1.0)) % self.world_w
                        b.y = (b.y + ny * overlap * (0.5 if not a.static else 1.0)) % self.world_h
                    else:
                        b.x += nx * overlap * (0.5 if not a.static else 1.0)
                        b.y += ny * overlap * (0.5 if not a.static else 1.0)
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
                obstacle_pair = a.static or b.static
                if not a.static: a.hp = max(0.0, a.hp - (0 if obstacle_pair and self.no_obstacle_damage else dmg))
                if not b.static: b.hp = max(0.0, b.hp - (0 if obstacle_pair and self.no_obstacle_damage else dmg))
                cx = (a.x + ddx * 0.5) % self.world_w
                cy = (a.y + ddy * 0.5) % self.world_h
                self.water.splash(cx / CELL_W, cy / CELL_H, impact * COLLISION_SPLASH, 3)

    # ── Enemy AI ───────────────────────────────────────────────────────────────
    def _update_enemies(self, dt: float):
        for enemy in self.enemies:
            new_projs = enemy.update(dt, self.player, self.water)
            self.projectiles.extend(new_projs)

    # ── Projectiles ────────────────────────────────────────────────────────────
    def _torus_dist(self, ax, ay, bx, by) -> float:
        dx = bx - ax;  dy = by - ay
        if self.topology != "bounded":
            dx -= self.world_w * round(dx / self.world_w)
            dy -= self.world_h * round(dy / self.world_h)
        return math.hypot(dx, dy)

    def _update_projectiles(self, dt: float):
        alive = []
        for proj in self.projectiles:
            proj.lifetime -= dt
            if proj.lifetime <= 0:
                if proj.explodes:
                    self._do_explosion(proj)
                continue

            # Move — wrap (torus), despawn at edge (bounded/survival)
            proj.x += proj.vx * dt
            proj.y += proj.vy * dt
            if self.survival:
                if proj.x < 0 or proj.x > self.world_w:
                    if proj.explodes:
                        self._do_explosion(proj)
                    continue
                proj.y %= self.world_h
            elif self.topology == "bounded":
                if (proj.x < 0 or proj.x > self.world_w or
                        proj.y < 0 or proj.y > self.world_h):
                    if proj.explodes:
                        self._do_explosion(proj)
                    continue
            else:
                proj.x %= self.world_w
                proj.y %= self.world_h

            # Hit-test against all living non-static entities
            killed = False
            for e in self.entities:
                if not e.alive or id(e) in proj.hits:
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
                    self.water.splash(proj.x / CELL_W, proj.y / CELL_H, 0.008, 2)
                    if not proj.pierce:
                        killed = True
                        if proj.explodes:
                            proj.hits.discard(id(e))  # let AoE hit the direct target too
                            self._do_explosion(proj)
                        break

            if not killed:
                alive.append(proj)

        self.projectiles = alive

    def _do_explosion(self, proj: Projectile):
        """Apply AoE damage, water splash, and schedule a visual flash."""
        for e in self.entities:
            if not e.alive or id(e) in proj.hits:
                continue
            d = self._torus_dist(proj.x, proj.y, e.x, e.y)
            if d < proj.explosion_radius:
                dmg = proj.explosion_damage * max(0.0, 1.0 - d / proj.explosion_radius)
                e.hp = max(0.0, e.hp - dmg)
        self.water.splash(proj.x / CELL_W, proj.y / CELL_H, 0.04, 8)
        self._explosions.append({
            "x": proj.x, "y": proj.y,
            "r": 4, "max_r": int(proj.explosion_radius),
            "t": 0.35, "max_t": 0.35,
        })

    def _update_explosions(self, dt: float):
        self._explosions = [e for e in self._explosions
                            if (e.__setitem__("t", e["t"] - dt) or True) and e["t"] > 0]

    # ── Enemy lifecycle ────────────────────────────────────────────────────────

    def _cleanup_dead_enemies(self):
        """Remove dead enemy entities from both lists to prevent unbounded growth."""
        dead_ids = {id(en.entity) for en in self.enemies if not en.entity.alive}
        if not dead_ids:
            return
        self.enemies  = [en for en in self.enemies if en.entity.alive]
        self.entities = [e  for e  in self.entities
                         if e.controllable or e.static or id(e) not in dead_ids]

    def _cleanup_dead_obstacles(self):
        """Remove destroyed obstacles and unpin their water grid cells."""
        dead = [e for e in self.entities if e.static and not e.alive]
        if not dead:
            return
        for e in dead:
            cell = self._obstacle_cells.pop(id(e), None)
            if cell:
                gx, gy, gr = cell
                self.water.unset_obstacle(gx, gy, gr)
        dead_ids = {id(e) for e in dead}
        self.entities = [e for e in self.entities if id(e) not in dead_ids]

    def _maybe_spawn_enemy(self, dt: float):
        """Spawn one enemy if living count is below budget."""
        if not self.spawn_pool or self.enemy_budget <= 0:
            return
        living = sum(1 for en in self.enemies if en.entity.alive)
        if living >= self.enemy_budget:
            return
        self._spawn_timer -= dt
        if self._spawn_timer > 0:
            return
        self._spawn_timer = 2.0   # one spawn every 2 s once deficit exists

        # Find a position at least 600 world-px from the player
        for _ in range(30):
            if self.survival:
                sx = self.world_w - random.uniform(80, 480)
                sy = random.uniform(200, self.world_h - 200)
            else:
                sx = random.uniform(0, self.world_w)
                sy = random.uniform(0, self.world_h)
            if (self.player is None or
                    self._torus_dist(sx, sy, self.player.x, self.player.y) > self.world_w // 4):
                break

        self.add_enemy(_SPAWN_FACTORIES[random.choice(self.spawn_pool)](sx, sy))

    # ── Rendering ──────────────────────────────────────────────────────────────
    _NAME_MAP = {
        "drifter":   "Pistol Grunt",
        "chaser":    "Chaser",
        "sniper":    "Sniper",
        "artillery": "Rocketeer",
        "patrol":    "Gunner",
        "boss":      "Bomber",
    }

    def _draw_enemy_shape(self, e: Entity, sx: int, sy: int, r: int):
        """Draw enemy using old-style boat/ship designs."""
        vis_name = self._NAME_MAP.get((e.name or "").lower(), "Pistol Grunt")
        vx, vy = e.vx, e.vy
        angle = math.atan2(vy, vx) if (vx != 0 or vy != 0) else 0
        speed = math.hypot(vx, vy)
        moving = speed > 5.0

        def rot_p(px, py):
            rx = px * math.cos(angle) - py * math.sin(angle)
            ry = px * math.sin(angle) + py * math.cos(angle)
            return (sx + rx, sy + ry)

        if vis_name == "Chaser":
            points = [(r, 0), (-r, r * 0.8), (-r * 0.4, 0), (-r, -r * 0.8)]
            rpts = [rot_p(px, py) for px, py in points]
            pygame.draw.polygon(self.screen, (160, 40, 40), rpts)
            pygame.draw.polygon(self.screen, (255, 140, 0), rpts, 2)
            ecx, ecy = rot_p(-r * 0.6, 0)
            pygame.draw.circle(self.screen, (0, 200, 255), (int(ecx), int(ecy)), 3)

        elif vis_name == "Bomber":
            pygame.draw.circle(self.screen, (50, 50, 55), (sx, sy), r)
            diag = r * 0.707
            for dx2, dy2 in [(r, 0), (-r, 0), (0, r), (0, -r),
                              (diag, diag), (-diag, diag), (diag, -diag), (-diag, -diag)]:
                pygame.draw.line(self.screen, (35, 35, 40), (sx, sy), (sx + dx2, sy + dy2), 2)
            for i in range(8):
                sa = i * (2 * math.pi / 8)
                sl = r * 0.6
                spike_pts = [
                    (sx + (r + sl) * math.cos(sa), sy + (r + sl) * math.sin(sa)),
                    (sx + r * 0.9 * math.cos(sa - 0.2), sy + r * 0.9 * math.sin(sa - 0.2)),
                    (sx + r * 0.9 * math.cos(sa + 0.2), sy + r * 0.9 * math.sin(sa + 0.2)),
                ]
                pygame.draw.polygon(self.screen, (120, 120, 125), spike_pts)
            cr = int(r * 0.4)
            pygame.draw.circle(self.screen, (0, 150, 180), (sx, sy), cr)
            pygame.draw.circle(self.screen, (0, 255, 255), (sx, sy), max(1, int(cr * 0.6)))

        elif vis_name == "Pistol Grunt":
            hull_pts = [(r*0.9,-r*0.4),(r*0.9,r*0.4),(r*0.4,r*0.85),(-r*0.9,r*0.85),(-r*0.9,-r*0.85),(r*0.4,-r*0.85)]
            pygame.draw.polygon(self.screen, (200,205,210), [rot_p(px,py) for px,py in hull_pts])
            pygame.draw.polygon(self.screen, (90,95,100),   [rot_p(px,py) for px,py in hull_pts], 2)
            deck_pts = [(r*0.6,-r*0.3),(r*0.6,r*0.3),(r*0.2,r*0.6),(-r*0.7,r*0.6),(-r*0.7,-r*0.6),(r*0.2,-r*0.6)]
            pygame.draw.polygon(self.screen, (150,155,160), [rot_p(px,py) for px,py in deck_pts])
            cabin_pts = [(r*0.3,-r*0.4),(r*0.3,r*0.4),(-r*0.5,r*0.4),(-r*0.5,-r*0.4)]
            pygame.draw.polygon(self.screen, (110,115,120), [rot_p(px,py) for px,py in cabin_pts])
            for my in [-r*0.65, r*0.65]:
                m_pts = [(-r*0.7,my-r*0.25),(-r*1.1,my-r*0.25),(-r*1.1,my+r*0.25),(-r*0.7,my+r*0.25)]
                pygame.draw.polygon(self.screen, (220,40,40), [rot_p(px,py) for px,py in m_pts])
                if moving:
                    pygame.draw.line(self.screen, (255,200,0), rot_p(-r*1.1,my), rot_p(-r*1.8,my), 3)
            gtx, gty = rot_p(r*0.4, 0)
            pygame.draw.line(self.screen, (60,60,65), rot_p(r*0.4,0), rot_p(r*1.2,0), 4)
            pygame.draw.circle(self.screen, (130,135,140), (int(gtx),int(gty)), int(r*0.35))

        elif vis_name == "Gunner":
            hull_pts = [(r*0.9,-r*0.5),(r*0.9,r*0.5),(r*0.4,r*1.0),(-r*0.9,r*1.0),(-r*0.9,-r*1.0),(r*0.4,-r*1.0)]
            pygame.draw.polygon(self.screen, (80,110,60),  [rot_p(px,py) for px,py in hull_pts])
            pygame.draw.polygon(self.screen, (40,50,30),   [rot_p(px,py) for px,py in hull_pts], 2)
            deck_pts = [(r*0.6,-r*0.4),(r*0.6,r*0.4),(r*0.2,r*0.8),(-r*0.7,r*0.8),(-r*0.7,-r*0.8),(r*0.2,-r*0.8)]
            pygame.draw.polygon(self.screen, (140,145,150), [rot_p(px,py) for px,py in deck_pts])
            cabin_pts = [(r*0.3,-r*0.5),(r*0.3,r*0.5),(-r*0.6,r*0.5),(-r*0.6,-r*0.5)]
            pygame.draw.polygon(self.screen, (110,115,120), [rot_p(px,py) for px,py in cabin_pts])
            for my in [-r*0.8, r*0.8]:
                m_pts = [(-r*0.7,my-r*0.25),(-r*1.1,my-r*0.25),(-r*1.1,my+r*0.25),(-r*0.7,my+r*0.25)]
                pygame.draw.polygon(self.screen, (220,40,40), [rot_p(px,py) for px,py in m_pts])
                if moving:
                    pygame.draw.line(self.screen, (255,200,0), rot_p(-r*1.1,my), rot_p(-r*1.8,my), 3)
            bs = r * 0.25
            pygame.draw.line(self.screen, (40,40,45), rot_p(r*0.3,-bs/2), rot_p(r*1.4,-bs/2), 4)
            pygame.draw.line(self.screen, (40,40,45), rot_p(r*0.3, bs/2), rot_p(r*1.4, bs/2), 4)
            gc_pts = [(r*0.4,-r*0.25),(r*0.4,r*0.25),(-r*0.1,r*0.25),(-r*0.1,-r*0.25)]
            pygame.draw.polygon(self.screen, (90,95,100), [rot_p(px,py) for px,py in gc_pts])

        elif vis_name == "Sniper":
            hull_pts = [(r*1.4,0),(r*0.5,r*0.4),(-r*0.9,r*0.4),(-r*0.9,-r*0.4),(r*0.5,-r*0.4)]
            pygame.draw.polygon(self.screen, (90,40,150), [rot_p(px,py) for px,py in hull_pts])
            for sign in [-1, 1]:
                p_pts = [(r*0.8,sign*r*0.4),(r*0.2,sign*r*0.8),(-r*0.9,sign*r*0.8),(-r*0.9,sign*r*0.4)]
                pygame.draw.polygon(self.screen, (110,60,180), [rot_p(px,py) for px,py in p_pts])
            c_pts = [(r*0.2,-r*0.3),(r*0.5,0),(r*0.2,r*0.3),(-r*0.6,r*0.3),(-r*0.6,-r*0.3)]
            pygame.draw.polygon(self.screen, (40,40,45), [rot_p(px,py) for px,py in c_pts])
            pygame.draw.line(self.screen, (30,30,35), rot_p(r*0.4,0), rot_p(r*2.2,0), 4)
            for my in [-r*0.6, r*0.6]:
                m_pts = [(-r*0.9,my-r*0.2),(-r*1.2,my-r*0.2),(-r*1.2,my+r*0.2),(-r*0.9,my+r*0.2)]
                pygame.draw.polygon(self.screen, (255,20,147), [rot_p(px,py) for px,py in m_pts])
                if moving:
                    pygame.draw.line(self.screen, (255,100,200), rot_p(-r*1.2,my), rot_p(-r*2.0,my), 3)

        else:  # Rocketeer (artillery / fallback)
            hull_pts = [(r*0.8,-r*0.7),(r*0.8,r*0.7),(r*0.3,r*0.9),(-r*0.8,r*0.9),(-r*0.8,-r*0.9),(r*0.3,-r*0.9)]
            pygame.draw.polygon(self.screen, (55,60,65),  [rot_p(px,py) for px,py in hull_pts])
            box_pts = [(r*0.7,-r*0.45),(r*0.7,r*0.45),(r*0.1,r*0.45),(r*0.1,-r*0.45)]
            pygame.draw.polygon(self.screen, (80,85,90), [rot_p(px,py) for px,py in box_pts])
            for ty in [-r*0.25, 0, r*0.25]:
                tx, ty_r = rot_p(r*0.7, ty)
                pygame.draw.circle(self.screen, (220,50,50), (int(tx),int(ty_r)), max(2,int(r*0.12)))
            for my in [-r*0.6, r*0.6]:
                m_pts = [(-r*0.8,my-r*0.3),(-r*1.2,my-r*0.3),(-r*1.2,my+r*0.3),(-r*0.8,my+r*0.3)]
                pygame.draw.polygon(self.screen, (200,60,20), [rot_p(px,py) for px,py in m_pts])
                if moving:
                    pygame.draw.line(self.screen, (255,150,0), rot_p(-r*1.2,my), rot_p(-r*2.2,my), 4)

    def _draw_entity_at(self, e: Entity, sx: int, sy: int, draw_r: int = 0):
        r = draw_r if draw_r > 0 else int(e.radius)
        if not e.alive:
            pygame.draw.circle(self.screen, (80, 80, 80), (sx, sy), r)
            return

        if e.controllable:
            mx, my = pygame.mouse.get_pos()
            psx, psy = self._w2s(e.x, e.y)
            angle = math.atan2(my - psy, mx - psx)
            _wt_map = {
                "pistol":      "pistol",
                "machinegun":  "machine_gun",
                "sniper":      "sniper",
                "bazooka":     "bazooka",
                "shotgun":     "shotgun",
            }
            wt = _wt_map.get(type(self.player_weapon).__name__.lower(), "pistol") if self.player_weapon else "pistol"
            PlayerVisual.draw(self.screen, sx, sy, angle, wt, radius=r)
            bar_w = max(r * 2, 20);  bar_h = 5
            bx = sx - bar_w // 2;  by = sy - r - 12
            frac = e.hp / e.max_hp;  fill_w = max(0, int(bar_w * frac))
            color = (30,200,30) if frac > 0.5 else (230,160,0) if frac > 0.25 else (210,30,30)
            pygame.draw.rect(self.screen, (60, 15, 15), (bx-1, by-1, bar_w+2, bar_h+2))
            if fill_w > 0:
                pygame.draw.rect(self.screen, color, (bx, by, fill_w, bar_h))
            return

        if e.static:
            frac = e.hp / e.max_hp if e.max_hp > 0 else 1.0
            base = e.color
            red_mix = int((1.0 - frac) * 200)
            tinted = (min(255, base[0] + red_mix),
                      max(0, base[1] - red_mix // 2),
                      max(0, base[2] - red_mix // 2))
            pygame.draw.circle(self.screen, tinted, (sx, sy), r)
            pygame.draw.circle(self.screen, (200, 180, 140), (sx, sy), r, 2)
            if frac < 1.0:
                bar_w = max(r * 2, 16);  bar_h = 4
                bx = sx - bar_w // 2;  by = sy - r - 8
                pygame.draw.rect(self.screen, (60, 15, 15), (bx-1, by-1, bar_w+2, bar_h+2))
                fill_w = max(0, int(bar_w * frac))
                fc = (30,200,30) if frac > 0.5 else (230,160,0) if frac > 0.25 else (210,30,30)
                if fill_w > 0:
                    pygame.draw.rect(self.screen, fc, (bx, by, fill_w, bar_h))
            return

        # Non-player, non-static entities (enemies)
        self._draw_enemy_shape(e, sx, sy, r)
        bar_w = max(r * 2, 20);  bar_h = 5
        bx = sx - bar_w // 2;  by = sy - r - 12
        pygame.draw.rect(self.screen, (60, 15, 15), (bx-1, by-1, bar_w+2, bar_h+2))
        frac = e.hp / e.max_hp;  fill_w = max(0, int(bar_w * frac))
        color = (30,200,30) if frac > 0.5 else (230,160,0) if frac > 0.25 else (210,30,30)
        if fill_w > 0:
            pygame.draw.rect(self.screen, color, (bx, by, fill_w, bar_h))
        if e.name:
            lbl = self._font.render(e.name, True, (220, 220, 220))
            self.screen.blit(lbl, (sx - lbl.get_width()//2, by - 14))

    def _draw_flag_arrow(self, sx: float, sy: float):
        """Arrow at the screen edge pointing toward the off-screen flag."""
        cx = self.width  // 2
        cy = self.height // 2
        dx, dy = sx - cx, sy - cy
        if dx == 0 and dy == 0:
            return
        ln = math.hypot(dx, dy)
        ndx, ndy = dx / ln, dy / ln

        margin = 24
        ts = []
        if ndx > 1e-9:
            t = (self.width  - margin - cx) / ndx
            if margin <= cy + t * ndy <= self.height - margin: ts.append(t)
        elif ndx < -1e-9:
            t = (margin - cx) / ndx
            if margin <= cy + t * ndy <= self.height - margin: ts.append(t)
        if ndy > 1e-9:
            t = (self.height - margin - cy) / ndy
            if margin <= cx + t * ndx <= self.width - margin: ts.append(t)
        elif ndy < -1e-9:
            t = (margin - cy) / ndy
            if margin <= cx + t * ndx <= self.width - margin: ts.append(t)
        if not ts:
            return

        t  = min(ts)
        ax = int(cx + ndx * t)
        ay = int(cy + ndy * t)
        al, aw = 18, 10    # arrow length, half-width
        tip = (ax, ay)
        bl  = (ax - int(ndx * al) - int(ndy * aw),
               ay - int(ndy * al) + int(ndx * aw))
        br  = (ax - int(ndx * al) + int(ndy * aw),
               ay - int(ndy * al) - int(ndx * aw))
        pygame.draw.polygon(self.screen, (50, 220, 80),   [tip, bl, br])
        pygame.draw.polygon(self.screen, (200, 255, 200), [tip, bl, br], 2)

    def _render(self):
        # ── Water: extract camera-relative slice from the grid ──
        cam_gx  = self.cam_x / CELL_W
        cam_gy  = self.cam_y / CELL_H
        off_x   = int(cam_gx) % GRID_W
        off_y   = int(cam_gy) % GRID_H
        frac_px = int((cam_gx % 1.0) * CELL_W)
        frac_py = int((cam_gy % 1.0) * CELL_H)
        # Number of grid cells needed depends on zoom (zoom-out → see more cells)
        cells_x = int(math.ceil(self.width  / (CELL_W * self.zoom))) + 2
        cells_y = int(math.ceil(self.height / (CELL_H * self.zoom))) + 2
        h_view  = np.roll(np.roll(self.water.h, -off_y, axis=0), -off_x, axis=1)
        # Use modular indexing so extreme zoom-out wraps correctly
        row_idx = np.arange(cells_y) % GRID_H
        col_idx = np.arange(cells_x) % GRID_W
        h_sl    = h_view[np.ix_(row_idx, col_idx)]
        h_norm  = np.clip(h_sl / SPLASH_AMP, -1.0, 1.0) * 0.5 + 0.5
        # multi-stop palette blending: deep -> mid -> shallow -> foam/crest
        c = h_norm
        # regions: [0,0.33], (0.33,0.66], (0.66,1.0]
        w1 = np.clip((0.33 - c) / 0.33, 0.0, 1.0)[..., np.newaxis]
        w2 = np.clip((c - 0.33) / 0.33, 0.0, 1.0)[..., np.newaxis] * np.clip((0.66 - c) / 0.33, 0.0, 1.0)[..., np.newaxis]
        w3 = np.clip((c - 0.66) / 0.34, 0.0, 1.0)[..., np.newaxis]
        # build color by blending contributions
        color_sl = (
            w1 * COLOR_DEEP +
            (1.0 - w1 - w2 - w3) * COLOR_MID +
            w2 * COLOR_SHALLOW +
            w3 * COLOR_FOAM
        ).astype(np.uint8)
        big     = np.repeat(np.repeat(color_sl, CELL_H, axis=0), CELL_W, axis=1)
        vis_w   = int(math.ceil(self.width  / self.zoom)) + CELL_W
        vis_h   = int(math.ceil(self.height / self.zoom)) + CELL_H
        view    = big[frac_py : frac_py + vis_h, frac_px : frac_px + vis_w]
        raw_surf = pygame.Surface((view.shape[1], view.shape[0]))
        pygame.surfarray.blit_array(raw_surf, view.transpose(1, 0, 2))
        self.screen.blit(pygame.transform.scale(raw_surf, (self.width, self.height)), (0, 0))

        # ── Entities ──
        for e in self.entities:
            sx, sy = self._w2s(e.x, e.y)
            draw_r = max(1, int(e.radius * self.zoom))
            if sx + draw_r >= 0 and sx - draw_r < self.width and sy + draw_r >= 0 and sy - draw_r < self.height:
                self._draw_entity_at(e, int(sx), int(sy), draw_r)

        # ── Projectiles ──
        for proj in self.projectiles:
            sx, sy = self._w2s(proj.x, proj.y)
            pr = max(1, int((5 if proj.explodes else 3) * self.zoom))
            if sx + pr >= 0 and sx - pr < self.width and sy + pr >= 0 and sy - pr < self.height:
                BulletVisual.draw(self.screen, int(sx), int(sy), proj.color, pr,
                                  (proj.vx, proj.vy), proj.explodes, proj.weapon_type)

        # ── Flag ──
        if self.flag_pos is not None:
            fsx, fsy = self._w2s(self.flag_pos[0], self.flag_pos[1])
            fx, fy = int(fsx), int(fsy)
            if 0 <= fx < self.width and 0 <= fy < self.height:
                z = self.zoom
                pygame.draw.line(self.screen, (220, 220, 220),
                                 (fx, fy + int(16 * z)), (fx, fy - int(20 * z)),
                                 max(1, int(3 * z)))
                pygame.draw.polygon(self.screen, (50, 220, 80),
                                    [(fx, fy - int(20 * z)),
                                     (fx + int(18 * z), fy - int(13 * z)),
                                     (fx, fy - int(6 * z))])
                pulse_r = max(2, int((36 + int(6 * math.sin(self._frame * 0.15))) * z))
                pygame.draw.circle(self.screen, (50, 220, 80), (fx, fy), pulse_r, 2)
            else:
                self._draw_flag_arrow(fsx, fsy)

        # ── Explosion flashes ──
        for exp in self._explosions:
            sx, sy = self._w2s(exp["x"], exp["y"])
            frac = exp["t"] / exp["max_t"]
            r    = max(1, int((exp["r"] + (exp["max_r"] - exp["r"]) * (1 - frac)) * self.zoom))
            alpha = int(200 * frac)
            if sx + r >= 0 and sx - r < self.width and sy + r >= 0 and sy - r < self.height:
                surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, (255, 140, 20, alpha), (r, r), r)
                self.screen.blit(surf, (int(sx) - r, int(sy) - r))

        # ── Player weapon HUD (bottom-left) ──
        if self.player_weapon:
            wname  = type(self.player_weapon).__name__
            max_cd = 1.0 / max(self.player_weapon.fire_rate, 1e-9)
            frac   = 1.0 - min(self.player_weapon._cooldown / max_cd, 1.0)
            bar_w, bar_h = 120, 8
            bx, by = 10, self.height - 30
            pygame.draw.rect(self.screen, (40, 40, 40),   (bx, by, bar_w, bar_h))
            fill_c = (50, 220, 80) if self.player_weapon.ready else (220, 160, 30)
            pygame.draw.rect(self.screen, fill_c,          (bx, by, int(bar_w * frac), bar_h))
            pygame.draw.rect(self.screen, (150, 150, 150), (bx, by, bar_w, bar_h), 1)
            self.screen.blit(self._font.render(wname, True, (220, 220, 220)), (bx, by - 16))

        # ── Survival HUD (top-center) ──
        if self.survival:
            mins = int(self._survival_t) // 60
            secs = int(self._survival_t) % 60
            tc   = (255, 80, 80) if self._survival_t < 30 else (255, 220, 80)
            hud  = self._font.render(f"Survive: {mins}:{secs:02d}", True, tc)
            self.screen.blit(hud, (self.width // 2 - hud.get_width() // 2, 8))
            # Left-edge vignette only when there's an active current pushing player left
            if self.player and self._current_force > 0 and self.player.x < 600:
                alpha = int(180 * max(0.0, 1.0 - self.player.x / 600.0))
                edge  = pygame.Surface((60, self.height), pygame.SRCALPHA)
                edge.fill((200, 20, 20, alpha))
                self.screen.blit(edge, (0, 0))

        pygame.display.flip()
