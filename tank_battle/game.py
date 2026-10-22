"""游戏核心：状态机、移动、战斗、AI 调度与关卡流程（纯逻辑）。"""

from __future__ import annotations

import math
import random
from enum import Enum

from . import config as C
from .ai import decide
from .entities import (
    Bullet,
    Direction,
    EnemyKind,
    EnemyTank,
    Explosion,
    Owner,
    PlayerTank,
    PowerUp,
    PowerUpKind,
    Tank,
)
from .geometry import clamp, overlaps
from .levels import LEVELS, Level, load_level
from .tiles import TileType


class GameState(str, Enum):
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    LEVEL_CLEAR = "level_clear"
    GAME_OVER = "game_over"
    VICTORY = "victory"


class Game:
    def __init__(self, level_index: int = 0, seed: int | None = None) -> None:
        self.rng = random.Random(seed)
        self.score = 0
        self.level_index = 0
        self.player: PlayerTank | None = None
        self.state = GameState.PLAYING
        self.start_level(level_index)

    # ------------------------------------------------------------------ 关卡

    def start_level(self, index: int) -> None:
        self.level_index = index
        self.level: Level = load_level(index)
        self.tilemap = self.level.tilemap
        self._plan: list[EnemyKind] = list(self.level.enemy_plan)
        self.rng.shuffle(self._plan)

        self.enemies: list[EnemyTank] = []
        self.bullets: list[Bullet] = []
        self.powerups: list[PowerUp] = []
        self.explosions: list[Explosion] = []

        self.spawn_timer = 0.8
        self.spawn_index = 0
        self.total_spawned = 0
        self.state_timer = 0.0

        lives = self.player.lives if self.player else C.PLAYER_LIVES
        weapon = self.player.weapon_level if self.player else 0
        sx, sy = self.level.player_spawn
        self.player = PlayerTank(
            x=sx - C.TANK_SIZE / 2,
            y=sy - C.TANK_SIZE / 2,
            lives=lives,
            weapon_level=weapon,
        )
        self.player.shield_timer = C.SPAWN_SHIELD_TIME
        self.state = GameState.PLAYING

    def restart(self) -> None:
        self.score = 0
        self.player = None
        self.start_level(0)

    def toggle_pause(self) -> None:
        if self.state is GameState.PLAYING:
            self.state = GameState.PAUSED
        elif self.state is GameState.PAUSED:
            self.state = GameState.PLAYING

    # ------------------------------------------------------------ 只读属性

    @property
    def lives(self) -> int:
        return self.player.lives if self.player else 0

    @property
    def base_pos(self) -> tuple[float, float]:
        return self.level.base_pos

    @property
    def pending_enemies(self) -> int:
        return len(self._plan)

    @property
    def enemies_remaining(self) -> int:
        return len(self._plan) + sum(1 for enemy in self.enemies if enemy.alive)

    # ---------------------------------------------------------------- 主循环

    def update(
        self,
        dt: float,
        move: Direction | None = None,
        fire: bool = False,
    ) -> None:
        if self.state is GameState.PAUSED:
            return

        self._update_effects(dt)

        if self.state is GameState.LEVEL_CLEAR:
            self.state_timer += dt
            if self.state_timer >= C.LEVEL_CLEAR_DELAY:
                if self.level_index + 1 < len(LEVELS):
                    self.start_level(self.level_index + 1)
                else:
                    self.state = GameState.VICTORY
                    self.state_timer = 0.0
            return

        if self.state is not GameState.PLAYING or self.player is None:
            return

        player = self.player
        player.cooldown = max(0.0, player.cooldown - dt)
        player.shield_timer = max(0.0, player.shield_timer - dt)

        if player.alive:
            if move is not None:
                self.move_tank(player, move, dt)
            if fire:
                self.fire(player, Owner.PLAYER)

        self._update_bullets(dt)
        if self.state is not GameState.PLAYING:
            return
        self._update_enemies(dt)
        if self.state is not GameState.PLAYING:
            return
        self._update_powerups(dt)
        self._update_spawning(dt)
        self._check_level_clear()

    # ---------------------------------------------------------------- 移动

    def _tanks(self) -> list[Tank]:
        tanks: list[Tank] = list(self.enemies)
        if self.player is not None:
            tanks.append(self.player)
        return tanks

    def _can_place(self, tank: Tank | None, rect: tuple[float, float, float, float]) -> bool:
        if self.tilemap.blocks_tank(rect):
            return False
        for other in self._tanks():
            if other is tank or not other.alive:
                continue
            if overlaps(rect, other.rect):
                return False
        return True

    def _align(self, tank: Tank, direction: Direction) -> None:
        """转向时把垂直轴吸附到最近格中心，便于通过 1 格通道。"""
        if direction in (Direction.UP, Direction.DOWN):
            nearest = round((tank.cx - C.TILE / 2) / C.TILE) * C.TILE + C.TILE / 2
            delta = nearest - tank.cx
            if abs(delta) <= C.ALIGN_TOLERANCE:
                rect = (tank.x + delta, tank.y, tank.size, tank.size)
                if self._can_place(tank, rect):
                    tank.x += delta
        else:
            nearest = round((tank.cy - C.TILE / 2) / C.TILE) * C.TILE + C.TILE / 2
            delta = nearest - tank.cy
            if abs(delta) <= C.ALIGN_TOLERANCE:
                rect = (tank.x, tank.y + delta, tank.size, tank.size)
                if self._can_place(tank, rect):
                    tank.y += delta

    def move_tank(self, tank: Tank, direction: Direction, dt: float) -> None:
        tank.direction = direction
        self._align(tank, direction)

        dx, dy = direction.vector
        distance = tank.speed * dt
        step_x = dx * distance
        step_y = dy * distance
        total = max(abs(step_x), abs(step_y))
        steps = max(1, math.ceil(total / C.BULLET_SUBSTEP))
        sub_x = step_x / steps
        sub_y = step_y / steps

        for _ in range(steps):
            rect = (tank.x + sub_x, tank.y + sub_y, tank.size, tank.size)
            if not self._can_place(tank, rect):
                break
            tank.x += sub_x
            tank.y += sub_y

    def ahead_blocked(self, tank: Tank, distance: float = 4.0) -> bool:
        dx, dy = tank.direction.vector
        rect = (tank.x + dx * distance, tank.y + dy * distance, tank.size, tank.size)
        return not self._can_place(tank, rect)

    # ---------------------------------------------------------------- 射击

    def fire(self, tank: Tank, owner: Owner) -> bool:
        if not tank.alive or tank.cooldown > 0:
            return False
        limit = tank.max_bullets if isinstance(tank, PlayerTank) else 1
        if sum(1 for bullet in self.bullets if bullet.owner is owner) >= limit:
            return False

        speed = tank.bullet_speed if isinstance(tank, PlayerTank) else C.BULLET_SPEED * 0.85
        dx, dy = tank.direction.vector
        cx, cy = tank.center
        muzzle = tank.size / 2 + 3
        bullet = Bullet(
            x=cx + dx * muzzle - C.BULLET_SIZE / 2,
            y=cy + dy * muzzle - C.BULLET_SIZE / 2,
            direction=tank.direction,
            speed=speed,
            owner=owner,
        )
        self.bullets.append(bullet)
        tank.cooldown = (
            C.PLAYER_FIRE_COOLDOWN
            if owner is Owner.PLAYER
            else tank.kind.fire_cooldown  # type: ignore[union-attr]
        )
        return True

    # ------------------------------------------------------------ 子弹推进

    def _update_bullets(self, dt: float) -> None:
        for bullet in list(self.bullets):
            if not bullet.alive:
                continue
            remaining = bullet.speed * dt
            while remaining > 1e-9 and bullet.alive:
                step = min(C.BULLET_SUBSTEP, remaining)
                remaining -= step
                dx, dy = bullet.direction.vector
                bullet.x += dx * step
                bullet.y += dy * step
                self._resolve_bullet(bullet)
        self.bullets = [bullet for bullet in self.bullets if bullet.alive]

    def _resolve_bullet(self, bullet: Bullet) -> None:
        if self.tilemap.out_of_bounds(bullet.rect):
            bullet.alive = False
            return

        if self.tilemap.eagle_hit(bullet.rect):
            bullet.alive = False
            self._destroy_base()
            return

        if self.tilemap.blocks_bullet(bullet.rect):
            bricks = self.tilemap.bricks_in(bullet.rect)
            for col, row in bricks:
                self.tilemap.destroy(col, row)
            self.explosions.append(
                Explosion(x=bullet.x - 10, y=bullet.y - 10, size=26)
            )
            bullet.alive = False
            return

        targets: list[Tank]
        if bullet.owner is Owner.PLAYER:
            targets = [enemy for enemy in self.enemies if enemy.alive]
        else:
            targets = [self.player] if self.player and self.player.alive else []

        for tank in targets:
            if overlaps(bullet.rect, tank.rect):
                bullet.alive = False
                self._damage_tank(tank, bullet.owner)
                return

    def _damage_tank(self, tank: Tank, owner: Owner) -> None:
        if isinstance(tank, EnemyTank):
            tank.hp -= 1
            if tank.hp <= 0:
                tank.alive = False
                self.score += tank.kind.score
                cx, cy = tank.center
                self.explosions.append(
                    Explosion(x=cx - tank.size / 2, y=cy - tank.size / 2, size=tank.size + 8)
                )
                if tank.bonus:
                    self._drop_powerup(cx, cy)
            return

        player = self.player
        if player is None:
            return
        if player.shield_timer > 0:
            return
        self._kill_player()

    def _kill_player(self) -> None:
        player = self.player
        if player is None:
            return
        cx, cy = player.center
        self.explosions.append(
            Explosion(x=cx - player.size / 2, y=cy - player.size / 2, size=player.size + 8)
        )
        player.alive = False
        player.lives -= 1
        if player.lives <= 0:
            player.lives = 0
            self.state = GameState.GAME_OVER
            self.state_timer = 0.0
            return
        self._respawn_player()

    def _respawn_player(self) -> None:
        player = self.player
        if player is None:
            return
        sx, sy = self.level.player_spawn
        player.x = sx - player.size / 2
        player.y = sy - player.size / 2
        player.direction = Direction.UP
        player.cooldown = 0.0
        player.shield_timer = C.SPAWN_SHIELD_TIME
        player.alive = True

    def _destroy_base(self) -> None:
        for row in range(self.tilemap.rows):
            for col in range(self.tilemap.cols):
                if self.tilemap.at(col, row) is TileType.EAGLE:
                    self.tilemap.grid[row][col] = TileType.EMPTY
        bx, by = self.base_pos
        self.explosions.append(Explosion(x=bx - 20, y=by - 20, size=44))
        self.state = GameState.GAME_OVER
        self.state_timer = 0.0

    # ------------------------------------------------------------------ 敌人

    def _update_enemies(self, dt: float) -> None:
        for enemy in list(self.enemies):
            if not enemy.alive:
                continue
            enemy.cooldown = max(0.0, enemy.cooldown - dt)
            enemy.decision_timer -= dt
            direction, wants_fire = decide(enemy, self, self.rng)
            self.move_tank(enemy, direction, dt)
            if wants_fire:
                self.fire(enemy, Owner.ENEMY)
        self.enemies = [enemy for enemy in self.enemies if enemy.alive]

    # ---------------------------------------------------------------- 刷怪

    def _update_spawning(self, dt: float) -> None:
        if not self._plan:
            return
        alive = sum(1 for enemy in self.enemies if enemy.alive)
        if alive >= C.MAX_ENEMIES_ON_FIELD:
            return
        self.spawn_timer -= dt
        if self.spawn_timer > 0:
            return
        self.spawn_enemy()

    def spawn_enemy(self) -> bool:
        if not self._plan:
            return False
        if sum(1 for enemy in self.enemies if enemy.alive) >= C.MAX_ENEMIES_ON_FIELD:
            return False

        kind = self._plan[0]
        cx, cy = self.level.enemy_spawns[self.spawn_index % len(self.level.enemy_spawns)]
        x = cx - C.TANK_SIZE / 2
        y = cy - C.TANK_SIZE / 2
        if not self._can_place(None, (x, y, C.TANK_SIZE, C.TANK_SIZE)):
            self.spawn_timer = 0.3
            return False

        self._plan.pop(0)
        bonus = (self.total_spawned + 1) % C.BONUS_EVERY == 0
        enemy = EnemyTank.create(kind, x, y, bonus=bonus)
        enemy.direction = Direction.DOWN
        enemy.decision_timer = self.rng.uniform(0.2, 0.8)
        self.enemies.append(enemy)
        self.spawn_index += 1
        self.total_spawned += 1
        self.spawn_timer = C.SPAWN_INTERVALS[min(self.level_index, len(C.SPAWN_INTERVALS) - 1)]
        return True

    # ---------------------------------------------------------------- 道具

    def _drop_powerup(self, cx: float, cy: float) -> None:
        kind = self.rng.choice(list(PowerUpKind))
        size = C.POWERUP_SIZE
        x = clamp(cx - size / 2, 0, C.FIELD_W - size)
        y = clamp(cy - size / 2, 0, C.FIELD_H - size)
        self.powerups.append(PowerUp(x=x, y=y, kind=kind, ttl=C.POWERUP_LIFETIME))

    def _update_powerups(self, dt: float) -> None:
        player = self.player
        for powerup in list(self.powerups):
            powerup.ttl -= dt
            if powerup.ttl <= 0:
                powerup.alive = False
                continue
            if player and player.alive and overlaps(powerup.rect, player.rect):
                self._apply_powerup(powerup)

        self.powerups = [powerup for powerup in self.powerups if powerup.alive]

    def _apply_powerup(self, powerup: PowerUp) -> None:
        player = self.player
        if player is None:
            return
        powerup.alive = False
        if powerup.kind is PowerUpKind.STAR:
            player.weapon_level = min(2, player.weapon_level + 1)
            self.score += 200
        elif powerup.kind is PowerUpKind.GRENADE:
            for enemy in self.enemies:
                if enemy.alive:
                    enemy.alive = False
                    self.score += enemy.kind.score
                    cx, cy = enemy.center
                    self.explosions.append(
                        Explosion(x=cx - enemy.size / 2, y=cy - enemy.size / 2, size=enemy.size + 8)
                    )
            self.enemies = [enemy for enemy in self.enemies if enemy.alive]
        elif powerup.kind is PowerUpKind.SHIELD:
            player.shield_timer = C.POWERUP_SHIELD_TIME
        elif powerup.kind is PowerUpKind.LIFE:
            player.lives += 1
        self.score += 100

    # ---------------------------------------------------------------- 状态

    def _update_effects(self, dt: float) -> None:
        for explosion in self.explosions:
            explosion.timer += dt
        self.explosions = [
            explosion for explosion in self.explosions if explosion.timer < explosion.duration
        ]

    def _check_level_clear(self) -> None:
        if self.state is not GameState.PLAYING:
            return
        if self._plan:
            return
        if any(enemy.alive for enemy in self.enemies):
            return
        self.state = GameState.LEVEL_CLEAR
        self.state_timer = 0.0
        self.score += 500
