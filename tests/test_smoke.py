import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from tank_battle.app import App  # noqa: E402
from tank_battle.game import GameState  # noqa: E402


def test_headless_run_300_frames() -> None:
    app = App()
    app.game.state = GameState.PLAYING
    for frame in range(300):
        app.step(1 / 60)
        app.renderer.draw(app.game, frame / 60)
    assert app.game.state in (
        GameState.PLAYING,
        GameState.LEVEL_CLEAR,
        GameState.GAME_OVER,
    )


def test_menu_and_overlay_render() -> None:
    app = App()
    app.game.state = GameState.MENU
    app.renderer.draw(app.game, 0.0)
    app.game.state = GameState.GAME_OVER
    app.renderer.draw(app.game, 1.0)
    app.game.state = GameState.VICTORY
    app.renderer.draw(app.game, 2.0)
