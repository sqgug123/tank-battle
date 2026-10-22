"""渲染层：读取游戏状态并绘制，不修改逻辑状态。"""

from __future__ import annotations

import math
import os

import pygame

from . import config as C
from .entities import (
    Direction,
    EnemyKind,
    EnemyTank,
    PowerUpKind,
    Tank,
)
from .game import Game, GameState
from .tiles import TileType


def _load_font(size: int) -> pygame.font.Font:
    """按已知路径加载中文字体，避免 pygame 在部分 Windows 环境下枚举注册表报错。"""
    candidates = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyhbd.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return pygame.font.Font(path, size)
            except pygame.error:
                continue
    return pygame.font.Font(None, size)


ENEMY_COLORS = {
    EnemyKind.BASIC: C.ENEMY_BASIC,
    EnemyKind.FAST: C.ENEMY_FAST,
    EnemyKind.HEAVY: C.ENEMY_HEAVY,
}


class Renderer:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.font_title = _load_font(44)
        self.font_big = _load_font(30)
        self.font_mid = _load_font(19)
        self.font_small = _load_font(13)
        self.font_tiny = _load_font(11)

    # ------------------------------------------------------------------ 入口

    def draw(self, game: Game, elapsed: float = 0.0) -> None:
        self.screen.fill(C.BG)
        self._draw_field(game, elapsed)
        self._draw_hud(game)
        self._draw_overlay(game, elapsed)

    # ------------------------------------------------------------------ 战场

    def _draw_field(self, game: Game, elapsed: float) -> None:
        pygame.draw.rect(self.screen, C.FIELD_BG, (0, 0, C.FIELD_W, C.FIELD_H))
        tilemap = game.tilemap
        trees: list[pygame.Rect] = []

        for row in range(tilemap.rows):
            for col in range(tilemap.cols):
                tile = tilemap.at(col, row)
                rect = pygame.Rect(col * C.TILE, row * C.TILE, C.TILE, C.TILE)
                if tile is TileType.BRICK:
                    self._draw_brick(rect)
                elif tile is TileType.STEEL:
                    self._draw_steel(rect)
                elif tile is TileType.WATER:
                    self._draw_water(rect, elapsed, col)
                elif tile is TileType.TREE:
                    trees.append(rect)
                elif tile is TileType.EAGLE:
                    self._draw_eagle(rect)

        for powerup in game.powerups:
            if powerup.alive:
                self._draw_powerup(powerup.x, powerup.y, powerup.kind, elapsed, powerup.ttl)

        for bullet in game.bullets:
            if bullet.alive:
                self._draw_bullet(bullet.x, bullet.y)

        if game.player is not None and game.player.alive:
            self._draw_tank(game.player, C.PLAYER_COLOR, C.PLAYER_TRACK, elapsed)
            if game.player.shield_timer > 0:
                self._draw_shield(game.player, elapsed)

        for enemy in game.enemies:
            if not enemy.alive:
                continue
            color = ENEMY_COLORS[enemy.kind]
            if enemy.bonus and int(elapsed * 6) % 2 == 0:
                color = C.ENEMY_BONUS
            self._draw_tank(enemy, color, C.ENEMY_TRACK, elapsed)

        for explosion in game.explosions:
            self._draw_explosion(explosion)

        for rect in trees:
            self._draw_tree(rect)

    def _draw_brick(self, rect: pygame.Rect) -> None:
        pygame.draw.rect(self.screen, C.BRICK_DARK, rect)
        for row in range(2):
            for col in range(2):
                brick = pygame.Rect(
                    rect.x + col * 16 + 2,
                    rect.y + row * 16 + 2,
                    12,
                    12,
                )
                pygame.draw.rect(self.screen, C.BRICK, brick)
                pygame.draw.line(
                    self.screen,
                    C.BRICK_DARK,
                    (brick.x, brick.y + 6),
                    (brick.right - 1, brick.y + 6),
                )

    def _draw_steel(self, rect: pygame.Rect) -> None:
        pygame.draw.rect(self.screen, C.STEEL_DARK, rect)
        inner = rect.inflate(-4, -4)
        pygame.draw.rect(self.screen, C.STEEL, inner)
        pygame.draw.rect(self.screen, C.STEEL_DARK, inner.inflate(-10, -10))

    def _draw_water(self, rect: pygame.Rect, elapsed: float, col: int) -> None:
        pygame.draw.rect(self.screen, C.WATER, rect)
        offset = math.sin(elapsed * 2.2 + col * 0.8) * 5
        for index in range(2):
            y = rect.y + 10 + index * 11 + offset
            pygame.draw.line(
                self.screen,
                C.WATER_LIGHT,
                (rect.x + 3, int(y)),
                (rect.right - 4, int(y)),
                2,
            )

    def _draw_tree(self, rect: pygame.Rect) -> None:
        pygame.draw.rect(self.screen, C.TREE_DARK, rect)
        pygame.draw.circle(self.screen, C.TREE, (rect.x + 9, rect.y + 12), 9)
        pygame.draw.circle(self.screen, C.TREE, (rect.x + 22, rect.y + 11), 8)
        pygame.draw.circle(self.screen, C.TREE, (rect.x + 15, rect.y + 22), 9)

    def _draw_eagle(self, rect: pygame.Rect) -> None:
        pygame.draw.rect(self.screen, (44, 44, 52), rect)
        cx, cy = rect.center
        body = [
            (cx, cy - 11),
            (cx - 12, cy + 1),
            (cx - 5, cy + 1),
            (cx - 5, cy + 11),
            (cx + 5, cy + 11),
            (cx + 5, cy + 1),
            (cx + 12, cy + 1),
        ]
        pygame.draw.polygon(self.screen, C.EAGLE_DARK, body)
        inner = [(cx, cy - 7), (cx - 8, cy), (cx - 3, cy), (cx - 3, cy + 8),
                 (cx + 3, cy + 8), (cx + 3, cy), (cx + 8, cy)]
        pygame.draw.polygon(self.screen, C.EAGLE, inner)

    # ------------------------------------------------------------------ 实体

    def _draw_tank(
        self,
        tank: Tank,
        color: tuple[int, int, int],
        track_color: tuple[int, int, int],
        elapsed: float,
    ) -> None:
        x, y = int(tank.x), int(tank.y)
        size = tank.size
        dx, dy = tank.direction.vector

        if dy != 0:
            pygame.draw.rect(self.screen, track_color, (x, y, 6, size))
            pygame.draw.rect(self.screen, track_color, (x + size - 6, y, 6, size))
            self._treads(x, y, size, vertical=True)
        else:
            pygame.draw.rect(self.screen, track_color, (x, y, size, 6))
            pygame.draw.rect(self.screen, track_color, (x, y + size - 6, size, 6))
            self._treads(x, y, size, vertical=False)

        body = pygame.Rect(x + 4, y + 4, size - 8, size - 8)
        pygame.draw.rect(self.screen, (18, 18, 22), body.inflate(2, 2))
        pygame.draw.rect(self.screen, color, body, border_radius=2)

        cx, cy = int(tank.cx), int(tank.cy)
        barrel = 8
        if dx == 0 and dy < 0:
            pygame.draw.rect(self.screen, color, (cx - 2, y - 3, 4, size // 2 + 6))
        elif dx == 0 and dy > 0:
            pygame.draw.rect(self.screen, color, (cx - 2, cy - 2, 4, size // 2 + 5))
        elif dx < 0:
            pygame.draw.rect(self.screen, color, (x - 3, cy - 2, size // 2 + 6, 4))
        else:
            pygame.draw.rect(self.screen, color, (cx - 2, cy - 2, size // 2 + 5, 4))

        pygame.draw.circle(self.screen, track_color, (cx, cy), 5)
        pygame.draw.circle(self.screen, color, (cx, cy), 3)

    def _treads(self, x: int, y: int, size: int, vertical: bool) -> None:
        shade = (58, 58, 66)
        for offset in range(4, size - 2, 6):
            if vertical:
                pygame.draw.line(self.screen, shade, (x + 1, y + offset), (x + 4, y + offset))
                pygame.draw.line(
                    self.screen, shade, (x + size - 5, y + offset), (x + size - 2, y + offset)
                )
            else:
                pygame.draw.line(self.screen, shade, (x + offset, y + 1), (x + offset, y + 4))
                pygame.draw.line(
                    self.screen, shade, (x + offset, y + size - 5), (x + offset, y + size - 2)
                )

    def _draw_bullet(self, x: float, y: float) -> None:
        rect = pygame.Rect(int(x), int(y), C.BULLET_SIZE, C.BULLET_SIZE)
        pygame.draw.rect(self.screen, (110, 104, 84), rect.inflate(4, 4), border_radius=2)
        pygame.draw.rect(self.screen, C.BULLET, rect, border_radius=1)

    def _draw_explosion(self, explosion) -> None:
        progress = explosion.progress
        cx = int(explosion.x + explosion.size / 2)
        cy = int(explosion.y + explosion.size / 2)
        radius = int(6 + (explosion.size / 2) * progress)
        if progress < 0.4:
            color = (255, 244, 180)
        elif progress < 0.7:
            color = (250, 160, 60)
        else:
            color = (120, 70, 40)
        if progress < 0.85:
            pygame.draw.circle(self.screen, (90, 50, 30), (cx, cy), radius + 3)
        pygame.draw.circle(self.screen, color, (cx, cy), max(2, radius))

    def _draw_shield(self, tank: Tank, elapsed: float) -> None:
        cx, cy = int(tank.cx), int(tank.cy)
        radius = 20 + int(math.sin(elapsed * 12) * 2)
        pygame.draw.circle(self.screen, (120, 210, 255), (cx, cy), radius, 2)

    def _draw_powerup(
        self,
        x: float,
        y: float,
        kind: PowerUpKind,
        elapsed: float,
        ttl: float,
    ) -> None:
        rect = pygame.Rect(int(x), int(y), C.POWERUP_SIZE, C.POWERUP_SIZE)
        if ttl < 3 and int(elapsed * 8) % 2 == 0:
            return
        pygame.draw.rect(self.screen, (18, 18, 24), rect, border_radius=4)
        border = {
            PowerUpKind.STAR: (250, 214, 84),
            PowerUpKind.GRENADE: (240, 120, 80),
            PowerUpKind.SHIELD: (120, 210, 255),
            PowerUpKind.LIFE: (120, 230, 140),
        }[kind]
        pygame.draw.rect(self.screen, border, rect, width=2, border_radius=4)
        cx, cy = rect.center

        if kind is PowerUpKind.STAR:
            points = []
            for index in range(10):
                angle = -math.pi / 2 + index * math.pi / 5
                radius = 9 if index % 2 == 0 else 4
                points.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
            pygame.draw.polygon(self.screen, border, points)
        elif kind is PowerUpKind.GRENADE:
            pygame.draw.circle(self.screen, border, (cx, cy + 2), 7)
            pygame.draw.rect(self.screen, border, (cx - 2, cy - 10, 4, 6))
            pygame.draw.line(self.screen, border, (cx + 3, cy - 9), (cx + 7, cy - 6), 2)
        elif kind is PowerUpKind.SHIELD:
            points = [(cx, cy - 9), (cx + 8, cy - 4), (cx + 7, cy + 4), (cx, cy + 9),
                      (cx - 7, cy + 4), (cx - 8, cy - 4)]
            pygame.draw.polygon(self.screen, border, points, width=2)
        else:
            pygame.draw.rect(self.screen, border, (cx - 3, cy - 8, 6, 16))
            pygame.draw.rect(self.screen, border, (cx - 8, cy - 3, 16, 6))

    # -------------------------------------------------------------------- HUD

    def _draw_hud(self, game: Game) -> None:
        panel = pygame.Rect(C.FIELD_W, 0, C.HUD_W, C.WINDOW_H)
        pygame.draw.rect(self.screen, C.HUD_BG, panel)
        pygame.draw.line(self.screen, C.HUD_LINE, (C.FIELD_W, 0), (C.FIELD_W, C.WINDOW_H), 2)

        self._text("坦克大战", self.font_mid, C.ACCENT, center=(C.FIELD_W + C.HUD_W // 2, 26))
        self._text(
            "TANK BATTLE",
            self.font_tiny,
            C.TEXT_DIM,
            center=(C.FIELD_W + C.HUD_W // 2, 46),
        )

        self._text(f"关卡  {game.level_index + 1} / 3", self.font_small, C.TEXT, (C.FIELD_W + 14, 68))
        self._text(f"分数  {game.score}", self.font_small, C.TEXT, (C.FIELD_W + 14, 90))

        self._text("剩余敌人", self.font_small, C.TEXT_DIM, (C.FIELD_W + 14, 118))
        remaining = game.enemies_remaining
        for index in range(min(remaining, 20)):
            col = index % 5
            row = index // 5
            icon = pygame.Rect(C.FIELD_W + 14 + col * 26, 140 + row * 18, 18, 12)
            pygame.draw.rect(self.screen, C.ENEMY_BASIC, icon, border_radius=2)
            pygame.draw.rect(self.screen, (30, 30, 38), icon.inflate(-8, -6))

        self._text("生命", self.font_small, C.TEXT_DIM, (C.FIELD_W + 14, 236))
        lives = game.lives
        for index in range(min(max(lives, 0), 5)):
            x = C.FIELD_W + 14 + index * 22
            pygame.draw.rect(self.screen, C.PLAYER_TRACK, (x, 258, 18, 14), border_radius=2)
            pygame.draw.rect(self.screen, C.PLAYER_COLOR, (x + 3, 261, 12, 8), border_radius=1)
        if lives > 5:
            self._text(f"+{lives - 5}", self.font_tiny, C.TEXT, (C.FIELD_W + 14 + 5 * 22, 258))
        self._text(f"× {lives}", self.font_small, C.TEXT, (C.FIELD_W + 14, 280))

        weapon = game.player.weapon_level if game.player else 0
        self._text(f"火力  Lv.{weapon}", self.font_small, C.TEXT_DIM, (C.FIELD_W + 14, 316))

        hints = [
            "方向键 / WASD  移动",
            "空格 / J       开火",
            "P  暂停    R  重开",
            "Esc  退出",
        ]
        for index, line in enumerate(hints):
            self._text(line, self.font_tiny, C.TEXT_DIM, (C.FIELD_W + 14, 356 + index * 20))

    # ---------------------------------------------------------------- 覆盖层

    def _draw_overlay(self, game: Game, elapsed: float) -> None:
        if game.state is GameState.MENU:
            self._dim(150)
            cx = C.FIELD_W // 2
            self._text("坦克大战", self.font_title, C.ACCENT, center=(cx, 150))
            self._text("TANK  BATTLE", self.font_mid, C.TEXT_DIM, center=(cx, 192))
            self._text("按 Enter 开始游戏", self.font_big, C.TEXT, center=(cx, 280))
            self._text("守住基地，消灭 3 关全部敌人", self.font_small, C.TEXT_DIM, center=(cx, 330))
            self._text("方向键/WASD 移动 · 空格/J 开火 · P 暂停", self.font_tiny, C.TEXT_DIM, center=(cx, 362))
        elif game.state is GameState.PAUSED:
            self._dim(140)
            self._text("暂停", self.font_title, C.TEXT, center=(C.FIELD_W // 2, 210))
            self._text("按 P 继续", self.font_mid, C.ACCENT, center=(C.FIELD_W // 2, 260))
        elif game.state is GameState.LEVEL_CLEAR:
            self._dim(150)
            self._text(f"第 {game.level_index + 1} 关完成", self.font_big, C.ACCENT, center=(C.FIELD_W // 2, 200))
            self._text("准备下一关…", self.font_mid, C.TEXT, center=(C.FIELD_W // 2, 248))
        elif game.state is GameState.GAME_OVER:
            self._dim(170)
            self._text("游戏结束", self.font_title, C.DANGER, center=(C.FIELD_W // 2, 180))
            self._text(f"得分  {game.score}", self.font_mid, C.TEXT, center=(C.FIELD_W // 2, 240))
            self._text("按 R 重新开始    Esc 退出", self.font_small, C.TEXT_DIM, center=(C.FIELD_W // 2, 300))
        elif game.state is GameState.VICTORY:
            self._dim(170)
            self._text("胜利！", self.font_title, C.ACCENT, center=(C.FIELD_W // 2, 170))
            self._text("你守住了基地，通过全部 3 关", self.font_mid, C.TEXT, center=(C.FIELD_W // 2, 230))
            self._text(f"最终得分  {game.score}", self.font_mid, C.TEXT, center=(C.FIELD_W // 2, 268))
            self._text("按 R 再来一局    Esc 退出", self.font_small, C.TEXT_DIM, center=(C.FIELD_W // 2, 320))

    def _dim(self, alpha: int) -> None:
        shade = pygame.Surface((C.FIELD_W, C.FIELD_H), pygame.SRCALPHA)
        shade.fill((0, 0, 0, alpha))
        self.screen.blit(shade, (0, 0))

    def _text(
        self,
        content: str,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        topleft: tuple[int, int] | None = None,
        center: tuple[int, int] | None = None,
    ) -> pygame.Rect:
        surface = font.render(content, True, color)
        if center is not None:
            rect = surface.get_rect(center=center)
        elif topleft is not None:
            rect = surface.get_rect(topleft=topleft)
        else:
            rect = surface.get_rect()
        self.screen.blit(surface, rect)
        return rect
