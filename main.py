"""Entry point — wires the menu into the game."""
from menu import MainMenu
from game import WaterGame
from enemy import make_drift, make_chaser, make_sniper, make_artillery, make_patrol
from water import GRID_W, GRID_H


def main():
    menu = MainMenu()
    if menu.run() != "play":
        return

    game = WaterGame()

    # Player boat — WASD / arrow keys
    game.add_entity(x=200, y=300, mass=2.0, radius=14,
                    color=(50, 220, 80), controllable=True, max_hp=120, name="player")

    # One of each enemy archetype
    game.add_enemy(make_drift    (x=500, y=180))
    game.add_enemy(make_chaser   (x=620, y=430))
    game.add_enemy(make_sniper   (x=650, y=150))
    game.add_enemy(make_artillery(x=100, y=450))
    game.add_enemy(make_patrol   (x=300, y=100, cx=300, cy=100))

    # Static rock obstacle
    game.add_entity(x=400, y=300, mass=10.0, radius=22,
                    color=(110, 90, 60), static=True)

    # Seed initial wave disturbance
    game.water.splash(GRID_W // 2, GRID_H // 2, 2.5, 10)
    game.water.splash(GRID_W // 4, GRID_H // 3, 1.5,  6)

    game.run()


if __name__ == "__main__":
    main()
