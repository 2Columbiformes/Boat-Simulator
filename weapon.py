import math
import random
from dataclasses import dataclass, field


@dataclass
class Projectile:
    """A single fired projectile living on the torus."""
    x:                float
    y:                float
    vx:               float
    vy:               float
    damage:           float
    lifetime:         float          # seconds remaining before despawn
    pierce:           bool  = False  # passes through entities without dying
    explodes:         bool  = False  # triggers AoE on death
    explosion_radius: float = 0.0
    explosion_damage: float = 0.0
    fuse:             float = 0.0   # bazooka: also explodes after this many extra seconds
    color:            tuple = (255, 220, 50)
    # origin stored for shotgun distance falloff
    origin_x:         float = 0.0
    origin_y:         float = 0.0
    shotgun:          bool  = False
    shotgun_range:    float = 280.0
    hits: set = field(default_factory=set, repr=False)  # id(entity) already struck

    @property
    def alive(self) -> bool:
        return self.lifetime > 0.0


# ── Weapon base ────────────────────────────────────────────────────────────────

class Weapon:
    """Base class. Subclasses override _make_projectiles()."""

    fire_rate: float = 1.0   # shots per second

    def __init__(self):
        self._cooldown: float = 0.0

    def tick(self, dt: float):
        self._cooldown = max(0.0, self._cooldown - dt)

    @property
    def ready(self) -> bool:
        return self._cooldown <= 0.0

    def fire(self, x: float, y: float, angle: float) -> list[Projectile]:
        """Return new projectiles and reset the cooldown."""
        if not self.ready:
            return []
        self._cooldown = 1.0 / self.fire_rate
        return self._make_projectiles(x, y, angle)

    def _make_projectiles(self, x: float, y: float, angle: float) -> list[Projectile]:
        raise NotImplementedError

    @staticmethod
    def _vel(speed: float, angle: float, spread: float = 0.0):
        a = angle + random.uniform(-spread, spread)
        return math.cos(a) * speed, math.sin(a) * speed


# ── Pistol ─────────────────────────────────────────────────────────────────────

class Pistol(Weapon):
    """Single accurate shot."""
    fire_rate = 1.0

    def _make_projectiles(self, x, y, angle):
        vx, vy = self._vel(250.0, angle)
        return [Projectile(x=x, y=y, vx=vx, vy=vy,
                           damage=20.0, lifetime=2.5,
                           color=(255, 255, 100))]


# ── Machine Gun ────────────────────────────────────────────────────────────────

class MachineGun(Weapon):
    """Fast fire rate, inaccurate."""
    fire_rate = 8.0

    def _make_projectiles(self, x, y, angle):
        vx, vy = self._vel(280.0, angle, spread=math.radians(18))
        return [Projectile(x=x, y=y, vx=vx, vy=vy,
                           damage=8.0, lifetime=1.8,
                           color=(255, 180, 50))]


# ── Sniper ─────────────────────────────────────────────────────────────────────

class Sniper(Weapon):
    """Slow rate, very fast bullet, pierces all targets."""
    fire_rate = 0.4

    def _make_projectiles(self, x, y, angle):
        vx, vy = self._vel(700.0, angle)
        return [Projectile(x=x, y=y, vx=vx, vy=vy,
                           damage=55.0, lifetime=3.0,
                           pierce=True,
                           color=(180, 80, 255))]


# ── Bazooka ────────────────────────────────────────────────────────────────────

class Bazooka(Weapon):
    """Slow projectile that explodes on impact or after a fuse timer."""
    fire_rate = 0.3

    def _make_projectiles(self, x, y, angle):
        vx, vy = self._vel(160.0, angle)
        return [Projectile(x=x, y=y, vx=vx, vy=vy,
                           damage=0.0, lifetime=5.0,
                           explodes=True,
                           explosion_radius=80.0,
                           explosion_damage=60.0,
                           fuse=3.0,
                           color=(255, 100, 30))]


# ── Shotgun ────────────────────────────────────────────────────────────────────

class Shotgun(Weapon):
    """7 pellets in a cone; damage falls off with distance."""
    fire_rate  = 0.8
    _pellets   = 7
    _cone      = math.radians(22)
    _base_dmg  = 30.0
    _range     = 280.0

    def _make_projectiles(self, x, y, angle):
        projs = []
        for i in range(self._pellets):
            t     = i / (self._pellets - 1) if self._pellets > 1 else 0.5
            a     = angle + self._cone * (t * 2 - 1)
            vx, vy = self._vel(240.0, a)
            projs.append(Projectile(
                x=x, y=y, vx=vx, vy=vy,
                damage=self._base_dmg, lifetime=1.2,
                shotgun=True, shotgun_range=self._range,
                origin_x=x, origin_y=y,
                color=(255, 140, 60),
            ))
        return projs
