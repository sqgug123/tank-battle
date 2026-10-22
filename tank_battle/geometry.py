"""不依赖 pygame 的矩形工具。"""

from __future__ import annotations

Rect = tuple[float, float, float, float]


def overlaps(a: Rect, b: Rect) -> bool:
    """AABB 相交（边缘相接不算相交）。"""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


def center_of(rect: Rect) -> tuple[float, float]:
    x, y, w, h = rect
    return x + w / 2, y + h / 2


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
