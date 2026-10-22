from tank_battle.config import GRID_H, GRID_W, POWERUP_SHIELD_TIME
from tank_battle.entities import EnemyKind, EnemyTank, PowerUp, PowerUpKind
from tank_battle.game import Game
from tank_battle.tiles import TileMap


def empty_game(seed: int = 6) -> Game:
    game = Game(seed=seed)
    game.tilemap = TileMap.empty(GRID_W, GRID_H)
    game.enemies = []
    game.bullets = []
    game.powerups = []
    game.spawn_timer = 999
    game.player.x = 200
    game.player.y = 200
    game.player.shield_timer = 999
    return game


def pick_up(game: Game, kind: PowerUpKind) -> PowerUp:
    powerup = PowerUp(x=game.player.x, y=game.player.y, kind=kind)
    game.powerups.append(powerup)
    game.update(0.01)
    return powerup


def test_star_upgrades_weapon() -> None:
    game = empty_game()
    pick_up(game, PowerUpKind.STAR)
    assert game.player.weapon_level == 1
    assert game.player.max_bullets == 2
    pick_up(game, PowerUpKind.STAR)
    pick_up(game, PowerUpKind.STAR)
    assert game.player.weapon_level == 2


def test_grenade_destroys_all_enemies() -> None:
    game = empty_game()
    for index in range(3):
        enemy = EnemyTank.create(EnemyKind.BASIC, 100 + index * 40, 100)
        enemy.speed = 0
        game.enemies.append(enemy)
    pick_up(game, PowerUpKind.GRENADE)
    assert game.enemies == []
    assert game.score >= 300


def test_shield_sets_timer() -> None:
    game = empty_game()
    pick_up(game, PowerUpKind.SHIELD)
    assert game.player.shield_timer == POWERUP_SHIELD_TIME


def test_life_increases_lives() -> None:
    game = empty_game()
    before = game.lives
    pick_up(game, PowerUpKind.LIFE)
    assert game.lives == before + 1


def test_powerup_expires() -> None:
    game = empty_game()
    powerup = PowerUp(x=10, y=10, kind=PowerUpKind.STAR, ttl=0.05)
    game.powerups.append(powerup)
    game.update(0.06)
    assert powerup.alive is False
    assert game.powerups == []


def test_bonus_enemy_drops_powerup() -> None:
    game = empty_game()
    game._drop_powerup(240, 240)
    assert len(game.powerups) == 1
    assert 0 <= game.powerups[0].x <= 480 - 24
