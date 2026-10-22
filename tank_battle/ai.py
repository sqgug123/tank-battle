"""敌人 AI：可注入随机源，便于测试。"""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

from .config import TILE
from .entities import Direction, EnemyTank, Tank
from .tiles import TileType

if TYPE_CHECKING:  # pragma: no cover - 仅用于类型提示
    from .game import Game


def line_clear(game: "Game", start: tuple[float, float], end: tuple[float, float]) -> bool:
    """沿直线采样，判断子弹能否通过（砖/钢/基地阻挡）。"""
    sx, sy = start
    ex, ey = end
    distance = math.hypot(ex - sx, ey - sy)
    steps = max(1, int(distance // 8))
    for index in range(1, steps + 1):
        t = index / steps
        x = sx + (ex - sx) * t
        y = sy + (ey - sy) * t
        rect = (x - 2, y - 2, 4, 4)
        if game.tilemap.blocks_bullet(rect):
            return False
        col = int(x // TILE)
        row = int(y // TILE)
        if game.tilemap.at(col, row) is TileType.EAGLE:
            return False
    return True


def aimed_at(enemy: Tank, target: tuple[float, float], tolerance: float = TILE * 0.45) -> bool:
    """敌人是否正对着目标（同一条通道且朝向正确）。"""
    ex, ey = enemy.center
    tx, ty = target
    if abs(ex - tx) <= tolerance:
        if ty > ey and enemy.direction is Direction.DOWN:
            return True
        if ty < ey and enemy.direction is Direction.UP:
            return True
    if abs(ey - ty) <= tolerance:
        if tx > ex and enemy.direction is Direction.RIGHT:
            return True
        if tx < ex and enemy.direction is Direction.LEFT:
            return True
    return False


def decide(enemy: EnemyTank, game: "Game", rng: random.Random) -> tuple[Direction, bool]:
    """返回（本帧移动方向，是否开火）。"""
    fire = False
    if enemy.cooldown <= 0:
        targets: list[tuple[float, float]] = [game.base_pos]
        if game.player.alive:
            targets.insert(0, game.player.center)
        for target in targets:
            if aimed_at(enemy, target) and line_clear(game, enemy.center, target):
                fire = True
                break

    blocked = game.ahead_blocked(enemy)
    if enemy.decision_timer > 0 and not blocked:
        return enemy.direction, fire

    if rng.random() < 0.7:
        target = game.player.center if game.player.alive else game.base_pos
        ex, ey = enemy.center
        dx = target[0] - ex
        dy = target[1] - ey
        if abs(dx) > abs(dy):
            direction = Direction.RIGHT if dx > 0 else Direction.LEFT
        else:
            direction = Direction.DOWN if dy > 0 else Direction.UP
        if blocked and direction is enemy.direction:
            options = [d for d in Direction if d is not enemy.direction.opposite]
            direction = rng.choice(options)
    else:
        direction = rng.choice(list(Direction))

    enemy.decision_timer = rng.uniform(0.4, 1.4)
    return direction, fire
