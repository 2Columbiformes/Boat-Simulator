import math
from entity import Entity
from weapon import Pistol, MachineGun, Sniper, Shotgun, Bazooka, Projectile
import assets

class Enemy(Entity):
    def __init__(self, x, y, mass=1.0, color=(200, 50, 50), radius=15, hp=50, name="Enemy"):
        # Initialize the base entity properties
        super().__init__(x=x, y=y, mass=mass, color=color, radius=radius)
        self.hp = hp
        self.max_hp = hp
        self.name = name
        self.controllable = False
        
        # Weapon and AI logic parameters
        self.weapon = None
        self.speed = 100.0
        self.optimal_range = 200.0

    def tick_ai(self, player, dt):
        if not player or not player.alive:
            return []

        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)
        if dist == 0: dist = 0.0001
        
        dir_x = dx / dist
        dir_y = dy / dist
        
        # Movement logic
        if dist > self.optimal_range + 20:
            self.vx += dir_x * self.speed * dt
            self.vy += dir_y * self.speed * dt
        elif dist < self.optimal_range - 20:
            self.vx -= dir_x * self.speed * dt
            self.vy -= dir_y * self.speed * dt

        # Shooting logic
        if self.weapon:
            self.weapon.tick(dt) # Advance the cooldown timer
            # Check if off cooldown and in range
            if self.weapon.ready and dist < self.optimal_range * 1.5:
                angle = math.atan2(dy, dx)
                # IMPORTANT: This returns the bullets to the game loop
                return self.weapon.fire(self.x, self.y, angle) 
                
        return []


# ─── 1. The 5 Weapon-Wielding Enemies ─────────────────────────────────────────

class PistolEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, color=(180, 255, 180), hp=50, name="Pistol Grunt")
        self.weapon = Pistol()
        self.optimal_range = 250.0

class MachineGunEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, color=(255, 180, 50), hp=75, name="Gunner")
        self.weapon = MachineGun()
        self.optimal_range = 150.0

class SniperEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, color=(180, 80, 255), hp=40, name="Sniper")
        self.weapon = Sniper()
        self.optimal_range = 450.0
        self.speed = 60.0 # Slower moving

class ShotgunEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, color=(240, 190, 10), hp=100, name="Breacher")
        self.weapon = Shotgun()
        self.optimal_range = 100.0 # Wants to get very close
        self.speed = 120.0

class BazookaEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, color=(165, 150, 130), hp=120, name="Rocketeer")
        self.weapon = Bazooka()
        self.optimal_range = 350.0
        self.speed = 50.0 # Heavy and slow


# ─── 2. The Melee / Special Enemies ───────────────────────────────────────────

class ChaserEnemy(Enemy):
    def __init__(self, x, y, cx=0, cy=0):
        super().__init__(x=x, y=y, mass=1.0, color=(160, 40, 40), radius=12, hp=40, name="Chaser")
        self.optimal_range = 0.0 # Wants to touch player
        self.damage_on_touch = 5.0
        self.collision_damage_cooldown = 0.8
        self.last_collision_dmg = 0.0
        # Patrol center (optional)
        self.cx = cx
        self.cy = cy
        


class BomberEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, color=(255, 50, 50), hp=30, name="Bomber")
        self.optimal_range = 0.0
        self.speed = 190.0       # Fastest enemy
        
    def tick_ai(self, player, dt):
        """Overrides normal AI to rush and explode."""
        if not player or not player.alive:
            return []

        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)
        if dist == 0: dist = 0.0001
        
        # Always rush directly at the player
        self.vx += (dx / dist) * self.speed * dt
        self.vy += (dy / dist) * self.speed * dt
        
        # SUICIDE BOMBER TRIGGER: If touching the player, explode!
        # (Assuming radii sum is ~30, triggering slightly earlier ensures it hits)
        if dist < self.radius + player.radius + 15:
            self.hp = 0 # Kill the bomber
            
            # Spawn a projectile with 0.0 lifetime.
            # This makes game.py immediately detonate it on the next frame using
            # your existing Bazooka visual effects and AoE damage!
            return [Projectile(
                x=self.x, y=self.y, vx=0, vy=0,
                damage=0, lifetime=0.0,
                explodes=True,
                explosion_radius=120.0,
                explosion_damage=80.0,
                color=(255, 100, 30),
                weapon_type="rocket_launcher" 
            )]
        return []


# ─── Factory Functions (For easy importing into game.py) ──────────────────────

def make_chaser(x, y): return ChaserEnemy(x, y)
def make_bomber(x, y): return BomberEnemy(x, y)
def make_pistol_enemy(x, y): return PistolEnemy(x, y)
def make_gunner(x, y): return MachineGunEnemy(x, y)
def make_sniper(x, y): return SniperEnemy(x, y)
def make_breacher(x, y): return ShotgunEnemy(x, y)
def make_rocketeer(x, y): return BazookaEnemy(x, y)

def make_patrol(x, y, cx=0, cy=0): 
    # This acts as a placeholder so the game doesn't crash
    return PistolEnemy(x, y) 

def make_drift(x, y): return PistolEnemy(x, y)
def make_artillery(x, y): return BazookaEnemy(x, y)

