import random

from tank_battle.ai import aimed_at, decide, line_clear
from tank_battle.config import GRID_H, GRID_W, TILE
from tank_battle.entities import Direction, EnemyKind, EnemyTank
from tank_battle.game import Game
from tank_battle.tiles import TileMap, TileType


def empty_game() -> Game:
    game = Game(seed=7)
    game.tilemap = TileMap.empty(GRID_W, GRID_H)
    game.enemies = []
    game.bullets = []
    game.spawn_timer = 999
    game.player.x = 7 * TILE
    game.player.y = 10 * TILE
    game.player.shield_timer = 999
    return game


def test_aimed_at_same_column() -> None:
    enemy = EnemyTank.create(EnemyKind.BASIC, 7 * TILE, 1 * TILE)
    enemy.direction = Direction.DOWN
    assert aimed_at(enemy, (7 * TILE + 13, 10 * TILE)) is True
    enemy.direction = Direction.UP
    assert aimed_at(enemy, (7 * TILE + 13, 10 * TILE)) is False


def test_line_clear_blocked_by_brick() -> None:
    game = empty_game()
    assert line_clear(game, (100, 100), (100, 300)) is True
    game.tilemap.grid[4][3] = TileType.BRICK
    assert line_clear(game, (100, 100), (100, 300)) is False


def test_enemy_fires_when_aligned_with_player() -> None:
    game = empty_game()
    enemy = EnemyTank.create(EnemyKind.BASIC, 7 * TILE, 2 * TILE)
    enemy.direction = Direction.DOWN
    enemy.cooldown = 0
    enemy.decision_timer = 5
    direction, fire = decide(enemy, game, random.Random(1))
    assert fire is True
    assert direction is Direction.DOWN


def test_enemy_does_not_fire_through_wall() -> None:
    game = empty_game()
    game.tilemap.grid[5][7] = TileType.BRICK
    enemy = EnemyTank.create(EnemyKind.BASIC, 7 * TILE, 2 * TILE)
    enemy.direction = Direction.DOWN
    enemy.cooldown = 0
    enemy.decision_timer = 5
    _, fire = decide(enemy, game, random.Random(1))
    assert fire is False


class FixedRandom:
    def random(self) -> float:
        return 0.0

    def uniform(self, low: float, high: float) -> float:
        return high

    def choice(self, seq):
        return seq[0]


def test_enemy_changes_direction_when_blocked() -> None:
    game = empty_game()
    enemy = EnemyTank.create(EnemyKind.BASIC, 7 * TILE, 2)
    enemy.direction = Direction.UP
    enemy.decision_timer = 5
    direction, _ = decide(enemy, game, FixedRandom())
    assert direction is Direction.DOWN
    assert enemy.decision_timer > 0


def test_enemy_retargets_after_timer() -> None:
    game = empty_game()
    enemy = EnemyTank.create(EnemyKind.BASIC, 1 * TILE, 1 * TILE)
    enemy.direction = Direction.LEFT
    enemy.decision_timer = 0
    direction, _ = decide(enemy, game, random.Random(0))
    assert isinstance(direction, Direction)
