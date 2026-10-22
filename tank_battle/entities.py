"""游戏实体（纯逻辑，不依赖 pygame）。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .config import (
    BULLET_SIZE,
    BULLET_SPEED,
    BULLET_SPEED_UPGRADED,
    EXPLOSION_TIME,
    PLAYER_FIRE_COOLDOWN,
    PLAYER_LIVES,
    PLAYER_SPEED,
    POWERUP_SIZE,
    TANK_SIZE,
)
from .geometry import Rect


class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    @property
    def vector(self) -> tuple[int, int]:
        return self.value

    @property
    def opposite(self) -> "Direction":
        return {
            Direction.UP: Direction.DOWN,
            Direction.DOWN: Direction.UP,
            Direction.LEFT: Direction.RIGHT,
            Direction.RIGHT: Direction.LEFT,
        }[self]

    @classmethod
    def from_name(cls, name: str) -> "Direction":
        return cls[name.upper()]


class Owner(Enum):
    PLAYER = "player"
    ENEMY = "enemy"


class EnemyKind(str, Enum):
    BASIC = "basic"
    FAST = "fast"
    HEAVY = "heavy"

    @property
    def speed(self) -> float:
        return {"basic": 62.0, "fast": 112.0, "heavy": 48.0}[self.value]

    @property
    def hp(self) -> int:
        return {"basic": 1, "fast": 1, "heavy": 3}[self.value]

    @property
    def score(self) -> int:
        return {"basic": 100, "fast": 200, "heavy": 300}[self.value]

    @property
    def fire_cooldown(self) -> float:
        return {"basic": 1.2, "fast": 1.0, "heavy": 1.6}[self.value]


class PowerUpKind(str, Enum):
    STAR = "star"
    GRENADE = "grenade"
    SHIELD = "shield"
    LIFE = "life"


@dataclass
class Tank:
    x: float
    y: float
    speed: float = PLAYER_SPEED
    hp: int = 1
    direction: Direction = Direction.UP
    cooldown: float = 0.0
    alive: bool = True
    size: int = TANK_SIZE

    @property
    def rect(self) -> Rect:
        return (self.x, self.y, self.size, self.size)

    @property
    def center(self) -> tuple[float, float]:
        return self.x + self.size / 2, self.y + self.size / 2

    @property
    def cx(self) -> float:
        return self.x + self.size / 2

    @property
    def cy(self) -> float:
        return self.y + self.size / 2


@dataclass
class PlayerTank(Tank):
    lives: int = PLAYER_LIVES
    shield_timer: float = 0.0
    weapon_level: int = 0
    speed: float = PLAYER_SPEED

    @property
    def max_bullets(self) -> int:
        return 2 if self.weapon_level >= 1 else 1

    @property
    def bullet_speed(self) -> float:
        return BULLET_SPEED if self.weapon_level < 2 else BULLET_SPEED_UPGRADED


@dataclass
class EnemyTank(Tank):
    kind: EnemyKind = EnemyKind.BASIC
    bonus: bool = False
    decision_timer: float = 0.0
    speed: float = 62.0
    hp: int = 1

    def __post_init__(self) -> None:
        self.speed = self.kind.speed
        self.hp = self.kind.hp
        self.cooldown = self.kind.fire_cooldown * 0.5

    @classmethod
    def create(
        cls,
        kind: EnemyKind,
        x: float,
        y: float,
        bonus: bool = False,
    ) -> "EnemyTank":
        return cls(x=x, y=y, kind=kind, bonus=bonus)


@dataclass
class Bullet:
    x: float
    y: float
    direction: Direction
    speed: float
    owner: Owner
    alive: bool = True
    size: int = BULLET_SIZE

    @property
    def rect(self) -> Rect:
        return (self.x, self.y, self.size, self.size)

    @property
    def center(self) -> tuple[float, float]:
        return self.x + self.size / 2, self.y + self.size / 2


@dataclass
class PowerUp:
    x: float
    y: float
    kind: PowerUpKind
    ttl: float = 12.0
    size: int = POWERUP_SIZE
    alive: bool = True

    @property
    def rect(self) -> Rect:
        return (self.x, self.y, self.size, self.size)


@dataclass
class Explosion:
    x: float
    y: float
    x2: float = 0.0
    y2: float = 0.0
    timer: float = 0.0
    duration: float = EXPLOSION_TIME
    size: int = TANK_SIZE

    @property
    def progress(self) -> float:
        if self.duration <= 0:
            return 1.0
        return min(1.0, self.timer / self.duration)
