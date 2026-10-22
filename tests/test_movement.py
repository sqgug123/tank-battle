from tank_battle.config import FIELD_H, FIELD_W, GRID_H, GRID_W, TANK_SIZE, TILE
from tank_battle.entities import Direction, EnemyKind, EnemyTank
from tank_battle.game import Game
from tank_battle.tiles import TileMap, TileType


def empty_game(seed: int = 1) -> Game:
    game = Game(seed=seed)
    game.tilemap = TileMap.empty(GRID_W, GRID_H)
    game.enemies = []
    game.bullets = []
    game.spawn_timer = 999
    game.player.x = TILE
    game.player.y = TILE
    game.player.shield_timer = 999
    return game


def test_move_right_increases_x() -> None:
    game = empty_game()
    start = game.player.x
    game.move_tank(game.player, Direction.RIGHT, 0.2)
    assert game.player.x > start
    assert game.player.y >= TILE


def test_brick_wall_stops_tank() -> None:
    game = empty_game()
    game.tilemap.grid[1][4] = TileType.BRICK
    for _ in range(200):
        game.move_tank(game.player, Direction.RIGHT, 1 / 60)
    assert game.player.x + TANK_SIZE <= 4 * TILE
    assert game.player.x > 3 * TILE


def test_cannot_leave_field() -> None:
    game = empty_game()
    game.player.x = FIELD_W - TANK_SIZE
    game.player.y = FIELD_H - TANK_SIZE - 40
    for _ in range(20):
        game.move_tank(game.player, Direction.RIGHT, 1 / 60)
    assert game.player.x == FIELD_W - TANK_SIZE


def test_one_tile_corridor_is_passable() -> None:
    game = empty_game()
    for col in range(GRID_W):
        game.tilemap.grid[0][col] = TileType.BRICK
        game.tilemap.grid[2][col] = TileType.BRICK
    game.player.x = TILE + 2
    game.player.y = TILE + 3
    for _ in range(120):
        game.move_tank(game.player, Direction.RIGHT, 1 / 60)
    assert game.player.x > 6 * TILE


def test_tanks_do_not_overlap() -> None:
    game = empty_game()
    enemy = EnemyTank.create(EnemyKind.BASIC, 200.0, game.player.y)
    enemy.speed = 0.0
    game.enemies = [enemy]
    for _ in range(120):
        game.move_tank(game.player, Direction.RIGHT, 1 / 60)
    assert game.player.x + TANK_SIZE <= enemy.x + 0.01


def test_alignment_snaps_to_grid_center() -> None:
    game = empty_game()
    game.player.x = TILE + 2
    game.player.y = TILE + 1
    game.move_tank(game.player, Direction.DOWN, 0.0)
    assert abs(game.player.cx - (TILE + TILE / 2)) < 0.01
