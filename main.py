"""Entry point — wires menu → level select → game."""
from menu import MainMenu
from level_select import LevelSelect
from weapons_menu import WeaponMenu
from levels import LEVELS
from game import WaterGame
from enemy import make_drift, make_chaser, make_sniper, make_artillery, make_patrol

# Import the actual weapon classes
from weapon import Pistol, MachineGun, Sniper, Shotgun, Bazooka

_FACTORIES = {
    "drift":     make_drift,
    "chase":     make_chaser,
    "snipe":     make_sniper,
    "artillery": make_artillery,
}

# Map the strings returned by the WeaponMenu to the actual classes
WEAPON_MAP = {
    "pistol": Pistol,
    "machine_gun": MachineGun,
    "sniper": Sniper,
    "shotgun": Shotgun,
    "bazooka": Bazooka
}

def _build_game(lvl, chosen_weapon_str=None) -> WaterGame:
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
        
    # Translate the menu string into a live Weapon object.
    # If no weapon is selected in the menu, fall back to the level's default.
    if chosen_weapon_str and chosen_weapon_str in WEAPON_MAP:
        game.player_weapon = WEAPON_MAP[chosen_weapon_str]()
    else:
        game.player_weapon = lvl.player_weapon
        
    return game


def main():
    menu = MainMenu()
    levels_unlocked = 1
    level_names = [lvl.name for lvl in LEVELS]
    
    chosen_weapon = None 

    while True:
        menu_choice = menu.run()
        
        if menu_choice == "quit":
            return
            
        elif menu_choice == "weapons":
            # Default display in the menu if they haven't picked one yet
            display_weapon = chosen_weapon if chosen_weapon else "pistol"
            chosen_weapon = WeaponMenu(display_weapon).run()
            continue
            
        elif menu_choice == "play":
            while True:
                sel = LevelSelect(level_names, levels_unlocked).run()
                
                if sel == -1: 
                    break     
                    
                result = _build_game(LEVELS[sel], chosen_weapon).run()  
                
                if result == "win" and sel + 1 == levels_unlocked and levels_unlocked < len(LEVELS):
                    levels_unlocked += 1
                if result == "quit":
                    return

if __name__ == "__main__":
    main()