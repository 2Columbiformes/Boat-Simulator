from dataclasses import dataclass, field


@dataclass
class Entity:
    """Anything that lives in the water: player, enemy boat, or static obstacle."""
    x:            float
    y:            float
    vx:           float = 0.0
    vy:           float = 0.0
    mass:         float = 1.0
    radius:       float = 12.0
    color:        tuple = (0, 200, 80)
    static:       bool  = False
    controllable: bool  = False
    name:         str   = ""
    max_hp:       float = 100.0
    hp:           float = field(default=0.0)
    ax: float = field(default=0.0, repr=False)
    ay: float = field(default=0.0, repr=False)

    def __post_init__(self):
        if self.hp == 0.0:
            self.hp = self.max_hp

    @property
    def alive(self) -> bool:
        return self.hp > 0.0
