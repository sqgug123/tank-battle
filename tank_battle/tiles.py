"""地形网格与可通行性查询（纯逻辑，不依赖 pygame）。"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

from .config import TILE
from .geometry import Rect


class TileType(str, Enum):
    EMPTY = "."
    BRICK = "B"
    STEEL = "S"
    WATER = "W"
    TREE = "T"
    EAGLE = "E"


TANK_BLOCKING = frozenset(
    {TileType.BRICK, TileType.STEEL, TileType.WATER, TileType.EAGLE}
)
BULLET_BLOCKING = frozenset({TileType.BRICK, TileType.STEEL})


@dataclass
class TileMap:
    cols: int
    rows: int
    tile: int
    grid: list[list[TileType]]

    @classmethod
    def empty(cls, cols: int, rows: int, tile: int = TILE) -> "TileMap":
        return cls(
            cols=cols,
            rows=rows,
            tile=tile,
            grid=[[TileType.EMPTY for _ in range(cols)] for _ in range(rows)],
        )

    @classmethod
    def from_rows(cls, rows: list[str], tile: int = TILE) -> "TileMap":
        if not rows:
            raise ValueError("地图不能为空")
        width = len(rows[0])
        grid: list[list[TileType]] = []
        for index, line in enumerate(rows):
            if len(line) != width:
                raise ValueError(f"第 {index} 行长度 {len(line)}，应为 {width}")
            try:
                grid.append([TileType(ch) for ch in line])
            except ValueError as exc:
                raise ValueError(f"第 {index} 行包含非法字符：{line}") from exc
        return cls(cols=width, rows=len(rows), tile=tile, grid=grid)

    @property
    def pixel_width(self) -> int:
        return self.cols * self.tile

    @property
    def pixel_height(self) -> int:
        return self.rows * self.tile

    def at(self, col: int, row: int) -> TileType:
        if 0 <= col < self.cols and 0 <= row < self.rows:
            return self.grid[row][col]
        return TileType.EMPTY

    def _cells(self, rect: Rect) -> list[tuple[int, int]]:
        x, y, w, h = rect
        col0 = math.floor(x / self.tile)
        row0 = math.floor(y / self.tile)
        col1 = math.floor((x + w - 1e-6) / self.tile)
        row1 = math.floor((y + h - 1e-6) / self.tile)
        return [
            (col, row)
            for row in range(row0, row1 + 1)
            for col in range(col0, col1 + 1)
        ]

    def out_of_bounds(self, rect: Rect) -> bool:
        x, y, w, h = rect
        return x < 0 or y < 0 or x + w > self.pixel_width or y + h > self.pixel_height

    def blocks_tank(self, rect: Rect) -> bool:
        if self.out_of_bounds(rect):
            return True
        return any(self.at(c, r) in TANK_BLOCKING for c, r in self._cells(rect))

    def blocks_bullet(self, rect: Rect) -> bool:
        return any(self.at(c, r) in BULLET_BLOCKING for c, r in self._cells(rect))

    def bricks_in(self, rect: Rect) -> list[tuple[int, int]]:
        return [
            (c, r) for c, r in self._cells(rect) if self.at(c, r) is TileType.BRICK
        ]

    def eagle_hit(self, rect: Rect) -> bool:
        return any(self.at(c, r) is TileType.EAGLE for c, r in self._cells(rect))

    def destroy(self, col: int, row: int) -> bool:
        if self.at(col, row) is TileType.BRICK:
            self.grid[row][col] = TileType.EMPTY
            return True
        return False
