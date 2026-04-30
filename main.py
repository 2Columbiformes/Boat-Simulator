"""Entry point — wires menu → level select → game."""
from menu import MainMenu
from level_select import LevelSelect
from weapons_menu import WeaponMenu
from levels import LEVELS
from game import WaterGame
# Only import what actually exists in enemy.py
from enemy import (
    make_chaser, make_sniper, make_bomber, 
    make_pistol_enemy, make_gunner, make_breacher, 
    make_rocketeer, make_patrol, make_drift, make_artillery
)

# IMPORT YOUR WEAPON CLASSES HERE
from weapon import Pistol, MachineGun, Sniper, Bazooka, Shotgun

_FACTORIES = {
    "drift":     make_drift,
    "chase":     make_chaser,
    "snipe":     make_sniper,
    "artillery": make_artillery,
    "bomber":    make_bomber,
    "gunner":    make_gunner,
    "breacher":  make_breacher,
}

def _build_game(lvl, chosen_weapon_string=None) -> WaterGame:
    game = WaterGame(
        flag_pos      = lvl.flag_pos,
        survival      = lvl.survival,
        survival_secs = lvl.survival_secs,
        current_force = lvl.current_force,
        scroll_speed  = lvl.scroll_speed,
    )
    px, py = lvl.player_start
    game.add_entity(x=px, y=py, mass=2.0, radius=14,
                    color=(50, 220, 80), controllable=True, max_hp=1000, name="player")
    for obs in lvl.obstacles:
        game.add_entity(x=obs["x"], y=obs["y"],
                        mass=10.0, radius=obs["radius"],
                        color=obs.get("color", (110, 90, 60)), static=True)
    for edef in lvl.enemies:
        t = edef["type"]
        if t == "patrol":
            enemy = make_patrol(edef["x"], edef["y"],
                                edef.get("cx", edef["x"]),
                                edef.get("cy", edef["y"]))
        else:
            enemy = _FACTORIES[t](edef["x"], edef["y"])
        game.add_enemy(enemy)
    for gx, gy, amp, r in lvl.splashes:
        game.water.splash(gx, gy, amp, r)
        
    # --- THIS IS THE FIX ---
    # Convert the text string back into a real weapon object!
    weapon_instance = None
    if chosen_weapon_string == "pistol":
        weapon_instance = Pistol()
    elif chosen_weapon_string == "machine_gun":
        weapon_instance = MachineGun()
    elif chosen_weapon_string == "sniper":
        weapon_instance = Sniper()
    elif chosen_weapon_string == "bazooka":
        weapon_instance = Bazooka()
    elif chosen_weapon_string == "shotgun":
        weapon_instance = Shotgun()
        
    # Assign the real weapon instance, or safely fall back to the level's default
    game.player_weapon = weapon_instance if weapon_instance else lvl.player_weapon
    return game


def main():
    menu = MainMenu()
    levels_unlocked = 1
    level_names = [lvl.name for lvl in LEVELS]
    
    # Default to None so we don't break the game's expected weapon format
    chosen_weapon = None 

    while True:
        menu_choice = menu.run()
        
        if menu_choice == "quit":
            return # This is the ONLY place we want to return and close the game!
            
        elif menu_choice == "weapons":
            display_weapon = chosen_weapon if chosen_weapon else "pistol"
            chosen_weapon = WeaponMenu(display_weapon).run()
            continue
            
        elif menu_choice == "play":
            while True:
                sel = LevelSelect(level_names, levels_unlocked).run()
                
                if sel == -1: 
                    break # User clicked back in Level Select, go to Main Menu
                    
                result = _build_game(LEVELS[sel], chosen_weapon).run()  
                
                if result == "win" and sel + 1 == levels_unlocked and levels_unlocked < len(LEVELS):
                    levels_unlocked += 1
                
                if result == "quit":
                    # Changed from 'return' to 'continue'
                    # Now it loops back to the Level Select screen instead of closing!
                    continue

if __name__ == "__main__":
    main()