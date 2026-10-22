"""Pygame 应用外壳：窗口、输入映射与固定步长主循环。"""

from __future__ import annotations

import pygame

from . import config as C
from .entities import Direction
from .game import Game, GameState
from .renderer import Renderer


class App:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("坦克大战 Tank Battle")
        self.screen = pygame.display.set_mode((C.WINDOW_W, C.WINDOW_H))
        self.clock = pygame.time.Clock()
        self.game = Game()
        self.game.state = GameState.MENU
        self.renderer = Renderer(self.screen)
        self.running = True
        self.elapsed = 0.0

    # ------------------------------------------------------------------ 输入

    def _move_intent(self) -> Direction | None:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            return Direction.UP
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            return Direction.DOWN
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            return Direction.LEFT
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            return Direction.RIGHT
        return None

    def _fire_intent(self) -> bool:
        keys = pygame.key.get_pressed()
        return keys[pygame.K_SPACE] or keys[pygame.K_j]

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if self.game.state in (
                        GameState.MENU,
                        GameState.GAME_OVER,
                        GameState.VICTORY,
                    ):
                        self.start_new_game()
                elif event.key == pygame.K_r:
                    self.start_new_game()
                elif event.key == pygame.K_p:
                    self.game.toggle_pause()

    def start_new_game(self) -> None:
        self.game.restart()

    # ------------------------------------------------------------------ 循环

    def step(self, dt: float) -> None:
        self.elapsed += dt
        if self.game.state is GameState.PLAYING:
            self.game.update(dt, self._move_intent(), self._fire_intent())
        else:
            self.game.update(dt)

    def draw(self) -> None:
        self.renderer.draw(self.game, self.elapsed)
        pygame.display.flip()

    def run(self) -> None:
        accumulator = 0.0
        while self.running:
            frame = min(self.clock.tick(C.FPS) / 1000.0, 0.1)
            accumulator += frame
            self.handle_events()
            steps = 0
            while accumulator >= C.DT and steps < 8:
                self.step(C.DT)
                accumulator -= C.DT
                steps += 1
            self.draw()
