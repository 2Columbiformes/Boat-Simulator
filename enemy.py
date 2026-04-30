import math
import random
from dataclasses import dataclass, field

from entity import Entity
from weapon import Weapon, Projectile, Pistol, MachineGun, Sniper, Bazooka, Shotgun
from water import WORLD_W, WORLD_H


def _torus_delta(ax, ay, bx, by):
    """Shortest signed (dx, dy) from a to b on the torus."""
    dx = bx - ax;  dx -= WORLD_W * round(dx / WORLD_W)
    dy = by - ay;  dy -= WORLD_H * round(dy / WORLD_H)
    return dx, dy


def _torus_dist(ax, ay, bx, by) -> float:
    dx, dy = _torus_delta(ax, ay, bx, by)
    return math.hypot(dx, dy)


def _torus_angle(ax, ay, bx, by) -> float:
    dx, dy = _torus_delta(ax, ay, bx, by)
    return math.atan2(dy, dx)


# ── Enemy wrapper ──────────────────────────────────────────────────────────────

@dataclass
class Enemy:
    """Wraps an Entity with a weapon and AI behaviour."""
    entity:   Entity
    weapon:   Weapon
    ai_type:  str            # "drift"|"chase"|"snipe"|"artillery"|"patrol"
    patrol_cx: float = 0.0   # patrol centre x  (only used by "patrol" AI)
    patrol_cy: float = 0.0
    _angle:    float = field(default=0.0, repr=False)
    _drift_timer: float = field(default=0.0, repr=False)

    def update(self, dt: float, target: Entity, water) -> list[Projectile]:
        """Advance AI, tick weapon cooldown, return any new projectiles."""
        self.weapon.tick(dt)
        if not self.entity.alive or (target is not None and not target.alive):
            return []

        tx = target.x if target else self.entity.x
        ty = target.y if target else self.entity.y
        dist = _torus_dist(self.entity.x, self.entity.y, tx, ty)
        angle_to = _torus_angle(self.entity.x, self.entity.y, tx, ty)

        if   self.ai_type == "drift":     return self._ai_drift(dt, tx, ty, dist, angle_to)
        elif self.ai_type == "chase":     return self._ai_chase(dt, tx, ty, dist, angle_to)
        elif self.ai_type == "snipe":     return self._ai_snipe(dt, tx, ty, dist, angle_to)
        elif self.ai_type == "artillery": return self._ai_artillery(dt, tx, ty, dist, angle_to)
        elif self.ai_type == "patrol":    return self._ai_patrol(dt, tx, ty, dist, angle_to)
        return []

    # ── AI implementations ────────────────────────────────────────────────────

    def _ai_drift(self, dt, tx, ty, dist, angle_to):
        """Wanders randomly; fires pistol when target is close."""
        e = self.entity
        self._drift_timer -= dt
        if self._drift_timer <= 0:
            self._angle = random.uniform(0, 2 * math.pi)
            self._drift_timer = random.uniform(1.5, 3.5)
        spd = 120.0
        e.vx += math.cos(self._angle) * spd * dt
        e.vy += math.sin(self._angle) * spd * dt
        if dist < 1200 and self.weapon.ready:
            return self.weapon.fire(e.x, e.y, angle_to)
        return []

    def _ai_chase(self, dt, tx, ty, dist, angle_to):
        """Steers toward target; fires machine gun continuously."""
        e = self.entity
        spd = 240.0
        e.vx += math.cos(angle_to) * spd * dt
        e.vy += math.sin(angle_to) * spd * dt
        if self.weapon.ready:
            return self.weapon.fire(e.x, e.y, angle_to)
        return []

    def _ai_snipe(self, dt, tx, ty, dist, angle_to):
        """Keeps 1400–2200 px from target; fires sniper when aimed within ±5°."""
        e = self.entity
        if dist < 1400:
            # back away
            e.vx += math.cos(angle_to + math.pi) * 220.0 * dt
            e.vy += math.sin(angle_to + math.pi) * 220.0 * dt
        elif dist > 2200:
            e.vx += math.cos(angle_to) * 180.0 * dt
            e.vy += math.sin(angle_to) * 180.0 * dt
        # face the target
        aim_err = abs(math.atan2(math.sin(angle_to - self._angle),
                                  math.cos(angle_to - self._angle)))
        self._angle = angle_to
        if aim_err < math.radians(5) and self.weapon.ready:
            return self.weapon.fire(e.x, e.y, angle_to)
        return []

    def _ai_artillery(self, dt, tx, ty, dist, angle_to):
        """Stays 1600+ px away; lobs bazookas leading the target."""
        e = self.entity
        if dist < 1600:
            e.vx += math.cos(angle_to + math.pi) * 200.0 * dt
            e.vy += math.sin(angle_to + math.pi) * 200.0 * dt
        if self.weapon.ready:
            return self.weapon.fire(e.x, e.y, angle_to)
        return []

    def _ai_patrol(self, dt, tx, ty, dist, angle_to):
        """Orbits its assigned centre point; fires shotgun at close range."""
        e   = self.entity
        # steer toward patrol centre with an orbital offset
        self._angle += 0.6 * dt           # orbit angular velocity
        orbit_r = 320.0
        goal_x  = self.patrol_cx + math.cos(self._angle) * orbit_r
        goal_y  = self.patrol_cy + math.sin(self._angle) * orbit_r
        dx, dy  = _torus_delta(e.x, e.y, goal_x, goal_y)
        spd     = 280.0
        e.vx += dx / max(math.hypot(dx, dy), 1) * spd * dt
        e.vy += dy / max(math.hypot(dx, dy), 1) * spd * dt
        if dist < 720 and self.weapon.ready:
            return self.weapon.fire(e.x, e.y, angle_to)
        return []


# ── Factory helpers ────────────────────────────────────────────────────────────

def make_drift(x: float, y: float) -> Enemy:
    e = Entity(x=x, y=y, mass=1.5, radius=22,
               color=(220, 60, 60), max_hp=2400, name="drifter")
    return Enemy(entity=e, weapon=Pistol(), ai_type="drift")

def make_chaser(x: float, y: float) -> Enemy:
    e = Entity(x=x, y=y, mass=1.8, radius=24,
               color=(220, 120, 40), max_hp=2700, name="chaser")
    return Enemy(entity=e, weapon=MachineGun(), ai_type="chase")

def make_sniper(x: float, y: float) -> Enemy:
    e = Entity(x=x, y=y, mass=1.2, radius=20,
               color=(120, 60, 200), max_hp=1800, name="sniper")
    return Enemy(entity=e, weapon=Sniper(), ai_type="snipe")

def make_artillery(x: float, y: float) -> Enemy:
    e = Entity(x=x, y=y, mass=3.0, radius=32,
               color=(180, 140, 40), max_hp=3600, name="artillery")
    return Enemy(entity=e, weapon=Bazooka(), ai_type="artillery")

def make_patrol(x: float, y: float, cx: float = None, cy: float = None) -> Enemy:
    cx = cx if cx is not None else x
    cy = cy if cy is not None else y
    e  = Entity(x=x, y=y, mass=1.6, radius=24,
                color=(200, 80, 160), max_hp=2550, name="patrol")
    return Enemy(entity=e, weapon=Shotgun(), ai_type="patrol",
                 patrol_cx=cx, patrol_cy=cy)
