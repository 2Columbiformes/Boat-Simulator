"""Entry point — wires menu → level select → game."""
import math
import pygame
from collections import defaultdict
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


def _spread_enemies(enem_list, radius=40):
    """Offset enemies that share the same spawn point so they don't overlap."""
    groups = defaultdict(list)
    for i, edef in enumerate(enem_list):
        groups[(edef["x"], edef["y"])].append(i)
    result = [dict(e) for e in enem_list]
    for indices in groups.values():
        if len(indices) > 1:
            for k, idx in enumerate(indices):
                angle = 2 * math.pi * k / len(indices)
                result[idx]["x"] += math.cos(angle) * radius
                result[idx]["y"] += math.sin(angle) * radius
    return result


def _build_game(lvl, weapon_override=None) -> WaterGame:
    game = WaterGame(
        flag_pos            = lvl.flag_pos,
        survival            = lvl.survival,
        survival_secs       = lvl.survival_secs,
        current_force       = lvl.current_force,
        scroll_speed        = lvl.scroll_speed,
        enemy_budget        = lvl.enemy_budget,
        spawn_pool          = lvl.spawn_pool or [],
        topology            = lvl.topology,
        entity_barriers     = lvl.entity_barriers,
        no_obstacle_damage  = lvl.no_obstacle_damage,
    )
    px, py = lvl.player_start
    game.add_entity(x=px, y=py, mass=2.0, radius=21,
                    color=(50, 220, 80), controllable=True, max_hp=1000, name="player",
                    wave_grad_k=10.0)
    # Fresh layout each replay when the level has a randomizing factory
    if lvl.obstacle_factory is not None:
        obs_list, enem_list = lvl.obstacle_factory()
    else:
        obs_list, enem_list = lvl.obstacles, lvl.enemies
    for obs in obs_list:
        hp = obs.get("hp", obs["radius"] * 350)
        game.add_entity(x=obs["x"], y=obs["y"],
                        mass=10.0, radius=obs["radius"],
                        color=obs.get("color", (110, 90, 60)), static=True, max_hp=hp)
    for edef in _spread_enemies(enem_list):
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


def _show_game_complete():
    screen = pygame.display.get_surface()
    w, h   = screen.get_size()
    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    screen.blit(overlay, (0, 0))
    big  = pygame.font.SysFont(None, 100)
    mid  = pygame.font.SysFont(None, 48)
    sub  = pygame.font.SysFont(None, 34)
    lines = [
        (big, "CONGRATULATIONS!", (80, 220, 120)),
        (mid, "You have conquered all 5 levels!", (200, 240, 200)),
        (sub, "Press any key to return to menu", (180, 180, 180)),
    ]
    y = h // 2 - 100
    for font, text, color in lines:
        surf = font.render(text, True, color)
        screen.blit(surf, (w // 2 - surf.get_width() // 2, y))
        y += surf.get_height() + 20
    pygame.display.flip()
    pygame.time.wait(500)
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.QUIT):
                waiting = False


def main():
    menu = MainMenu()
    chosen_weapon    = None      # None = use level default
    chosen_weapon_id = "pistol"  # tracks current id for the weapon menu highlight
    level_names      = [lvl.name for lvl in LEVELS]
    levels_unlocked  = 1

    while True:
        result = menu.run()
        if result == "quit":
            break
        if result == "weapons":
            chosen_weapon_id = WeaponMenu(current_weapon=chosen_weapon_id).run()
            chosen_weapon    = make_weapon(chosen_weapon_id)
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
            if result == "win" and sel == len(LEVELS) - 1:
                _show_game_complete()
            if result == "quit":
                quit_game = True
                break
            # "win" or "lose" → loop back to level select

        if quit_game:
            break

    pygame.quit()


if __name__ == "__main__":
    main()
