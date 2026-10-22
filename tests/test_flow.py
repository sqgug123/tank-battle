from tank_battle.config import GRID_H, GRID_W, TILE
from tank_battle.entities import Bullet, Direction, Owner
from tank_battle.game import Game, GameState
from tank_battle.tiles import TileMap


def test_level_clear_then_next_level() -> None:
    game = Game(seed=8)
    game.spawn_timer = 999
    game._plan.clear()
    game.enemies.clear()
    game.update(0.01)
    assert game.state is GameState.LEVEL_CLEAR

    game.update(2.1)
    assert game.state is GameState.PLAYING
    assert game.level_index == 1
    assert game.enemies_remaining == 20


def test_final_level_clear_is_victory() -> None:
    game = Game(seed=8)
    game.start_level(2)
    game.spawn_timer = 999
    game._plan.clear()
    game.enemies.clear()
    game.update(0.01)
    assert game.state is GameState.LEVEL_CLEAR
    game.update(2.1)
    assert game.state is GameState.VICTORY


def test_zero_lives_is_game_over() -> None:
    game = Game(seed=8)
    game.tilemap = TileMap.empty(GRID_W, GRID_H)
    game.spawn_timer = 999
    game.enemies = []
    game.player.lives = 1
    game.player.shield_timer = 0
    cx, cy = game.player.center
    game.bullets.append(
        Bullet(x=cx, y=cy, direction=Direction.RIGHT, speed=340, owner=Owner.ENEMY)
    )
    game.update(0.016)
    assert game.state is GameState.GAME_OVER
    assert game.lives == 0


def test_restart_resets_everything() -> None:
    game = Game(seed=8)
    game.score = 1200
    game.start_level(2)
    game.player.lives = 1
    game.restart()
    assert game.score == 0
    assert game.level_index == 0
    assert game.lives == 3
    assert game.state is GameState.PLAYING


def test_pause_freezes_game() -> None:
    game = Game(seed=8)
    game.spawn_timer = 999
    start_x = game.player.x
    game.toggle_pause()
    assert game.state is GameState.PAUSED
    for _ in range(60):
        game.update(1 / 60, move=Direction.RIGHT)
    assert game.player.x == start_x
    game.toggle_pause()
    assert game.state is GameState.PLAYING


def test_player_moves_and_fires_through_update() -> None:
    game = Game(seed=8)
    game.tilemap = TileMap.empty(GRID_W, GRID_H)
    game.enemies = []
    game.spawn_timer = 999
    game.player.x = 7 * TILE
    game.player.y = 7 * TILE
    start_x = game.player.x
    game.update(0.2, move=Direction.RIGHT, fire=True)
    assert game.player.x > start_x
    assert len(game.bullets) == 1
