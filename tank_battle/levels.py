"""手工关卡：ASCII 地图、解析与敌人配比。"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .config import ENEMIES_PER_LEVEL, ENEMY_MIX, GRID_H, GRID_W, TILE
from .entities import EnemyKind
from .tiles import TileMap, TileType

SPAWN_CHARS = {"P", "1", "2", "3"}
LEGEND = set(".") | {t.value for t in TileType} | SPAWN_CHARS

LEVELS: list[list[str]] = [
    [
        "1......2......3",
        "...............",
        "..BB.......BB..",
        "..BB.......BB..",
        "...............",
        ".BB..SS.SS..BB.",
        ".BB..SS.SS..BB.",
        "...TT.....TT...",
        "..BB..BBB..BB..",
        "..BB..BBB..BB..",
        "...............",
        ".BB.BB...BB.BB.",
        ".BB.BB...BB.BB.",
        "......BBB......",
        "....P.BEB......",
    ],
    [
        "1......2......3",
        "...............",
        ".SS..BB.BB..SS.",
        ".SS..BB.BB..SS.",
        ".....BB.BB.....",
        ".BB.........BB.",
        ".BB.WWW.WWW.BB.",
        "....WWW.WWW....",
        ".BB.........BB.",
        ".BB..BB.BB..BB.",
        ".....BB.BB.....",
        ".TT.BB...BB.TT.",
        ".TT.BB...BB.TT.",
        "......BBB......",
        "....P.BEB......",
    ],
    [
        "1......2......3",
        "...BB.BBB.BB...",
        "...BB.BBB.BB...",
        ".SS....B....SS.",
        ".SS.WWW.WWW.SS.",
        "....WWW.WWW....",
        ".BB.BB...BB.BB.",
        ".BB.BB...BB.BB.",
        "...............",
        ".SS..BB.BB..SS.",
        ".SS..BB.BB..SS.",
        "....BB...BB....",
        ".TT.BB...BB.TT.",
        "......BBB......",
        "....P.BEB......",
    ],
]


@dataclass
class Level:
    tilemap: TileMap
    player_spawn: tuple[float, float]
    enemy_spawns: list[tuple[float, float]] = field(default_factory=list)
    base_pos: tuple[float, float] = (0.0, 0.0)
    enemy_plan: list[EnemyKind] = field(default_factory=list)


def _cell_center(col: int, row: int) -> tuple[float, float]:
    return col * TILE + TILE / 2, row * TILE + TILE / 2


def build_enemy_plan(index: int) -> list[EnemyKind]:
    """按关卡配比生成 20 辆敌人，顺序用固定种子打乱，保证同关可复现。"""
    mix = ENEMY_MIX[min(index, len(ENEMY_MIX) - 1)]
    counts = {kind: int(round(ENEMIES_PER_LEVEL * ratio)) for kind, ratio in mix.items()}
    counts["heavy"] = ENEMIES_PER_LEVEL - counts["basic"] - counts["fast"]
    plan: list[EnemyKind] = []
    for name, count in counts.items():
        plan.extend([EnemyKind(name)] * max(0, count))
    rng = random.Random(1000 + index)
    rng.shuffle(plan)
    return plan[:ENEMIES_PER_LEVEL]


def parse_level(text: str) -> Level:
    rows = [line.rstrip() for line in text.strip("\n").splitlines()]
    if len(rows) != GRID_H:
        raise ValueError(f"地图行数 {len(rows)}，应为 {GRID_H}")

    grid_rows: list[str] = []
    player_spawn: tuple[float, float] | None = None
    enemy_spawns: list[tuple[float, float]] = []
    base: tuple[float, float] | None = None

    for row, line in enumerate(rows):
        if len(line) != GRID_W:
            raise ValueError(f"第 {row} 行长度 {len(line)}，应为 {GRID_W}")
        cells: list[str] = []
        for col, ch in enumerate(line):
            if ch not in LEGEND:
                raise ValueError(f"第 {row} 行第 {col} 列出现非法字符 {ch!r}")
            if ch == "P":
                player_spawn = _cell_center(col, row)
                cells.append(".")
            elif ch in {"1", "2", "3"}:
                enemy_spawns.append(_cell_center(col, row))
                cells.append(".")
            else:
                if ch == "E":
                    base = _cell_center(col, row)
                cells.append(ch)
        grid_rows.append("".join(cells))

    if player_spawn is None:
        raise ValueError("地图缺少玩家出生点 P")
    if len(enemy_spawns) != 3:
        raise ValueError(f"敌人出生点数量 {len(enemy_spawns)}，应为 3")
    if base is None:
        raise ValueError("地图缺少基地 E")

    return Level(
        tilemap=TileMap.from_rows(grid_rows),
        player_spawn=player_spawn,
        enemy_spawns=enemy_spawns,
        base_pos=base,
    )


def load_level(index: int) -> Level:
    level = parse_level("\n".join(LEVELS[index]))
    level.enemy_plan = build_enemy_plan(index)
    return level
