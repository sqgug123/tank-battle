from tank_battle.config import GRID_H, GRID_W, MAX_ENEMIES_ON_FIELD
from tank_battle.entities import EnemyKind, EnemyTank
from tank_battle.game import Game
from tank_battle.tiles import TileMap


def empty_game(seed: int = 5) -> Game:
    game = Game(seed=seed)
    game.tilemap = TileMap.empty(GRID_W, GRID_H)
    game.enemies = []
    game.bullets = []
    game.spawn_timer = 999
    game.player.shield_timer = 9999
    game.player.x = 7 * 32
    game.player.y = 10 * 32
    return game


def test_spawns_stop_at_field_cap() -> None:
    game = empty_game()
    for index in range(MAX_ENEMIES_ON_FIELD):
        enemy = EnemyTank.create(EnemyKind.BASIC, 40 + index * 60, 200)
        enemy.speed = 0
        game.enemies.append(enemy)
    assert game.spawn_enemy() is False
    assert game.total_spawned == 0


def test_twenty_enemies_per_level_and_bonus_every_fourth() -> None:
    game = empty_game()
    bonuses: list[bool] = []
    for _ in range(40):
        game.enemies.clear()
        game.spawn_timer = 0
        game.update(0.01)
        bonuses.extend(enemy.bonus for enemy in game.enemies)
        if not game.pending_enemies:
            break
    assert game.total_spawned == 20
    assert game.pending_enemies == 0
    assert len(bonuses) == 20
    assert sum(bonuses) == 5
    assert bonuses[3] is True
    assert bonuses[0] is False


def test_spawn_points_cycle() -> None:
    game = empty_game()
    xs: list[float] = []
    for _ in range(3):
        game.enemies.clear()
        game.spawn_timer = 0
        game.update(0.01)
        xs.append(game.enemies[-1].x)
    assert len(set(xs)) == 3


def test_spawn_timer_prevents_instant_spawn() -> None:
    game = empty_game()
    game.spawn_timer = 1.0
    for _ in range(30):
        game.update(1 / 60)
    assert game.total_spawned == 0
    game.update(0.6)
    assert game.total_spawned == 1
