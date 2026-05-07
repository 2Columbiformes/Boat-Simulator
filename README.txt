Boat Simulator

An interactive top-down boat combat game built with Pygame and NumPy, featuring
a real-time shallow-water physics simulation.


DESCRIPTION
You pilot a boat through 5 progressively challenging levels, navigating around
obstacles and battling enemy ships. The water surface reacts dynamically to
movement and explosions using a finite-difference wave equation solved on a
200x150 height-field grid. Enemies have distinct AI behaviors and the player
chooses a weapon loadout before each campaign.


REQUIREMENTS
- Python 3.9+
- pygame
- numpy

Install dependencies:
    pip install pygame numpy


HOW TO RUN
    python main.py

Game flow: Main Menu -> Level Select -> (Weapons Menu on first run) -> Level -> repeat


CONTROLS
Move:       WASD or Arrow keys
Aim/Shoot:  Mouse (left-click to fire)
Zoom:       Mouse wheel (if supported)


LEVELS
1. Open Water    - Introduction; basic enemies, open field
2. The Gauntlet  - Narrow obstacle corridors with enemies
3. Crossfire     - Multi-directional sniper and artillery fire
4. Wave Assault  - Survival with increasing enemy waves
5. Boss Fight    - End-game guardian combining all enemy types

Levels must be completed in order to unlock the next.


WEAPONS
Pistol      - 1 shot/sec, 200 damage, reliable single target
Machine Gun - 8 shots/sec, low damage per bullet, wide spread
Sniper      - 0.4 shots/sec, pierces all targets, high velocity
Bazooka     - 0.3 shots/sec, 160 px explosion radius, 300 AoE damage
Shotgun     - 1.5 shots/sec, 7-pellet cone, damage falls off with distance


ENEMY TYPES
Drifter    - Wanders randomly; fires pistol at close range
Chaser     - Actively pursues the player with a machine gun
Sniper     - Keeps distance (350-550 px); fires precise long-range shots
Artillery  - Stands off >400 px; lobs bazooka rounds
Patrol     - Orbits a fixed point; fires shotgun defensively
Boss       - End-level guardian; combines sniper and bazooka attacks


FILE STRUCTURE
main.py          Entry point; wires menu, level select, and game loop
game.py          Core WaterGame class: physics, rendering, entity management
water.py         WaterGrid shallow-water simulator (height-field equations)
entity.py        Entity dataclass for all dynamic and static objects
enemy.py         Enemy AI with 5 behavior types and Boss class
weapon.py        Weapon classes (Pistol, MachineGun, Sniper, Bazooka, Shotgun)
bullet.py        Projectile visual rendering
player_visual.py Player boat drawing with weapon aiming
menu.py          Main menu UI
level_select.py  Level selection UI with lock/unlock system
levels.py        5 LevelDef definitions (obstacles, enemies, weapons per level)
weapons_menu.py  Weapon selection screen


TECHNICAL NOTES
- 60 FPS simulation with fixed-timestep physics
- Water grid uses NumPy vectorized operations for performance
- World topology options: torus (wrap edges) or bounded (solid walls)
- Elastic collision response with velocity-proportional damage
- Camera follows player with optional zoom


CREDITS
-
ECE160 course project
