"""无头生成 README 截图：python tools/make_screenshot.py"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

from tank_battle.app import App  # noqa: E402
from tank_battle.entities import (  # noqa: E402
    Bullet,
    Direction,
    EnemyKind,
    EnemyTank,
    Explosion,
    Owner,
    PowerUp,
    PowerUpKind,
)
from tank_battle.game import GameState  # noqa: E402


def build_scene() -> App:
    app = App()
    game = app.game
    game.start_level(1)
    game.state = GameState.PLAYING
    game.score = 1300
    game.enemies.clear()
    game.bullets.clear()
    game.powerups.clear()
    game.explosions.clear()

    game.player.x = 224
    game.player.y = 384
    game.player.direction = Direction.UP
    game.player.shield_timer = 2.5
    game.player.weapon_level = 1

    placements = [
        (EnemyKind.BASIC, 96, 72, False),
        (EnemyKind.FAST, 240, 96, True),
        (EnemyKind.HEAVY, 336, 160, False),
                (EnemyKind.BASIC, 160, 264, False),
    ]
    for kind, x, y, bonus in placements:
        enemy = EnemyTank.create(kind, float(x), float(y), bonus=bonus)
        enemy.speed = 0
        enemy.direction = Direction.DOWN
        game.enemies.append(enemy)

    game.powerups.append(
        PowerUp(x=224, y=288, kind=PowerUpKind.STAR, ttl=9.0)
    )
    game.explosions.append(Explosion(x=300, y=320, timer=0.18, size=34))
    game.explosions.append(Explosion(x=80, y=120, timer=0.05, size=26))
    game.bullets.append(
        Bullet(x=236, y=340, direction=Direction.UP, speed=340, owner=Owner.PLAYER)
    )
    game.bullets.append(
        Bullet(x=112, y=180, direction=Direction.DOWN, speed=290, owner=Owner.ENEMY)
    )
    return app


def main() -> None:
    app = build_scene()
    app.renderer.draw(app.game, 8.4)
    pygame.display.flip()
    output = ROOT / "docs" / "screenshot.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(app.screen, str(output))
    pygame.quit()
    print(f"截图已保存：{output}")


if __name__ == "__main__":
    main()
