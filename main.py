"""Entry point — wires menu → level select → game."""
import pygame
from menu import MainMenu
from level_select import LevelSelect
from levels import LEVELS
from game import WaterGame
from enemy import make_drift, make_chaser, make_sniper, make_artillery, make_patrol, make_boss
from weapons_menu import WeaponMenu, make_weapon


_FACTORIES = {
    "drift":     make_drift,
    "chase":     make_chaser,
    "snipe":     make_sniper,
    "artillery": make_artillery,
    "patrol":    make_patrol,
    "boss":      make_boss,
}


def _build_game(lvl, weapon_override=None) -> WaterGame:
    game = WaterGame(
        flag_pos      = lvl.flag_pos,
        survival      = lvl.survival,
        survival_secs = lvl.survival_secs,
        current_force = lvl.current_force,
        scroll_speed  = lvl.scroll_speed,
        enemy_budget  = lvl.enemy_budget,
        spawn_pool    = lvl.spawn_pool or [],
        topology      = lvl.topology,
    )
    px, py = lvl.player_start
    game.add_entity(x=px, y=py, mass=2.0, radius=14,
                    color=(50, 220, 80), controllable=True, max_hp=1000, name="player")
    for obs in lvl.obstacles:
        hp = obs.get("hp", obs["radius"] * 35)
        game.add_entity(x=obs["x"], y=obs["y"],
                        mass=10.0, radius=obs["radius"],
                        color=obs.get("color", (110, 90, 60)), static=True, max_hp=hp)
    for edef in lvl.enemies:
        t = edef["type"]
        if t == "patrol":
            enemy = make_patrol(edef["x"], edef["y"],
                                edef.get("cx", edef["x"]),
                                edef.get("cy", edef["y"]))
        elif t == "boss":
            enemy = make_boss(edef["x"], edef["y"])
        else:
            enemy = _FACTORIES[t](edef["x"], edef["y"])
        game.add_enemy(enemy)
    for gx, gy, amp, r in lvl.splashes:
        game.water.splash(gx, gy, amp, r)
    game.player_weapon = weapon_override or lvl.player_weapon
    return game


def main():
    menu = MainMenu()
    chosen_weapon  = None   # None = use level default
    level_names    = [lvl.name for lvl in LEVELS]
    levels_unlocked = 1     # persists across weapon-menu visits

    while True:
        result = menu.run()
        if result == "quit":
            break
        if result == "weapons":
            name = WeaponMenu().run()
            chosen_weapon = make_weapon(name)
            continue

        # result == "play"
        quit_game = False
        while True:
            sel = LevelSelect(level_names, levels_unlocked).run()
            if sel == -1:
                break   # back to main menu

            result = _build_game(LEVELS[sel], chosen_weapon).run()

            if result == "win" and sel + 1 == levels_unlocked and levels_unlocked < len(LEVELS):
                levels_unlocked += 1
            if result == "quit":
                quit_game = True
                break
            # "win" or "lose" → loop back to level select

        if quit_game:
            break

    pygame.quit()


if __name__ == "__main__":
    main()
