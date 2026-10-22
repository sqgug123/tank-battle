from tank_battle.config import GRID_H, GRID_W, TILE
from tank_battle.entities import Bullet, Direction, EnemyKind, EnemyTank, Owner
from tank_battle.game import Game, GameState
from tank_battle.tiles import TileMap, TileType


def empty_game(seed: int = 2) -> Game:
    game = Game(seed=seed)
    game.tilemap = TileMap.empty(GRID_W, GRID_H)
    game.enemies = []
    game.bullets = []
    game.powerups = []
    game.spawn_timer = 999
    game.player.x = 7 * TILE
    game.player.y = 13 * TILE
    game.player.shield_timer = 0
    return game


def add_bullet(
    game: Game,
    x: float,
    y: float,
    direction: Direction = Direction.RIGHT,
    owner: Owner = Owner.PLAYER,
) -> Bullet:
    bullet = Bullet(x=x, y=y, direction=direction, speed=340.0, owner=owner)
    game.bullets.append(bullet)
    return bullet


def test_bullet_destroys_brick() -> None:
    game = empty_game()
    game.tilemap.grid[1][3] = TileType.BRICK
    add_bullet(game, 3 * TILE + 8, TILE + 8)
    game.update(0.05)
    assert game.tilemap.at(3, 1) is TileType.EMPTY
    assert game.bullets == []


def test_bullet_stopped_by_steel() -> None:
    game = empty_game()
    game.tilemap.grid[1][3] = TileType.STEEL
    add_bullet(game, 3 * TILE + 8, TILE + 8)
    game.update(0.05)
    assert game.tilemap.at(3, 1) is TileType.STEEL
    assert game.bullets == []


def test_bullet_passes_water() -> None:
    game = empty_game()
    game.tilemap.grid[1][3] = TileType.WATER
    bullet = add_bullet(game, 2 * TILE + 8, TILE + 8)
    game.update(0.2)
    assert bullet.alive is True
    assert bullet.x > 4 * TILE


def test_bullet_destroys_enemy_and_scores() -> None:
    game = empty_game()
    enemy = EnemyTank.create(EnemyKind.BASIC, 3 * TILE, TILE + 4)
    enemy.speed = 0
    game.enemies = [enemy]
    add_bullet(game, 100, TILE + 8)
    game.update(0.1)
    assert enemy.alive is False
    assert game.score == 100


def test_heavy_tank_needs_three_hits() -> None:
    game = empty_game()
    enemy = EnemyTank.create(EnemyKind.HEAVY, 3 * TILE, TILE + 4)
    enemy.speed = 0
    game.enemies = [enemy]
    for _ in range(2):
        add_bullet(game, 100, TILE + 8)
        game.update(0.1)
    assert enemy.alive is True
    add_bullet(game, 100, TILE + 8)
    game.update(0.1)
    assert enemy.alive is False


def test_player_hit_loses_life_and_respawns() -> None:
    game = empty_game()
    cx, cy = game.player.center
    add_bullet(game, cx, cy, Direction.RIGHT, Owner.ENEMY)
    game.update(0.016)
    assert game.lives == 2
    assert game.player.alive is True
    assert game.player.shield_timer > 0


def test_shield_blocks_damage() -> None:
    game = empty_game()
    game.player.shield_timer = 5
    cx, cy = game.player.center
    add_bullet(game, cx, cy, Direction.RIGHT, Owner.ENEMY)
    game.update(0.016)
    assert game.lives == 3


def test_eagle_destroyed_ends_game() -> None:
    game = Game(seed=3)
    game.spawn_timer = 999
    game.tilemap.destroy(7, 13)
    add_bullet(game, 7 * TILE + 13, 13 * TILE + 6, Direction.DOWN)
    game.update(0.12)
    assert game.state is GameState.GAME_OVER


def test_enemy_bullet_does_not_hurt_enemies() -> None:
    game = empty_game()
    enemy = EnemyTank.create(EnemyKind.BASIC, 3 * TILE, TILE + 4)
    enemy.speed = 0
    game.enemies = [enemy]
    add_bullet(game, 100, TILE + 8, Direction.RIGHT, Owner.ENEMY)
    game.update(0.1)
    assert enemy.alive is True
