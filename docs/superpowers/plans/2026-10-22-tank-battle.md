# 坦克大战实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 交付一个可直接运行的 Python + Pygame 坦克大战，含 3 张手工关卡、地形破坏、敌人 AI、4 种道具、完整菜单与 HUD，并推送到 GitHub。

**Architecture:** 纯逻辑层（无 pygame 依赖）负责地图、实体、AI、状态机；渲染层只读状态绘图；`app.py` 处理输入与固定步长主循环。逻辑层用 pytest 全覆盖，CI 无头运行。

**Tech Stack:** Python 3.10+、pygame>=2.6、pytest、GitHub Actions

## Global Constraints

- 战场 15×15 格，每格 32px；窗口 640×480；60 FPS。
- 逻辑层文件严禁 `import pygame`。
- 无外部图片/字体/音频资源；音效不做。
- 玩家 3 条命；每关 20 辆敌人；同屏最多 4 辆。
- 命令行入口 `python main.py`。

---

### Task 1: 骨架、配置与地形

**Files:** Create `tank_battle/__init__.py`, `tank_battle/config.py`, `tank_battle/tiles.py`, `tests/test_tiles.py`, `requirements.txt`, `.gitignore`

**Interfaces:**
- `config.TILE=32`, `GRID_W=GRID_H=15`, `FIELD_W=480`, `WINDOW_W=640`, `WINDOW_H=480`, `TANK_SIZE=26`, `BULLET_SIZE=6`, `PLAYER_SPEED=120.0`, `BULLET_SPEED=340.0`, `PLAYER_LIVES=3`, `MAX_ENEMIES_ON_FIELD=4`, `ENEMIES_PER_LEVEL=20`
- `TileType(str, Enum)`：EMPTY/BRICK/STEEL/WATER/TREE/EAGLE
- `TileMap(cols, rows, tile, grid)` 方法：`at(col,row)->TileType`、`blocks_tank(rect)->bool`、`blocks_bullet(rect)->bool`、`bricks_in(rect)->list[tuple[int,int]]`、`destroy(col,row)->None`、`eagle_hit(rect)->bool`

**Steps:**
- [ ] 写 `tests/test_tiles.py`：砖墙挡坦克不挡子弹、钢墙挡子弹、水挡坦克不挡子弹、`destroy` 后变 EMPTY、越界算阻挡、EAGLE 判定。
- [ ] 运行 `pytest tests/test_tiles.py -v` 确认失败（模块不存在）。
- [ ] 实现 `config.py`、`tiles.py`（矩形按 32px 网格展开；越界 block）。
- [ ] 运行测试通过，`git commit -m "feat: 地形与配置"`。

### Task 2: 关卡解析与 3 张地图

**Files:** Create `tank_battle/levels.py`, `tests/test_levels.py`

**Interfaces:**
- `Level` dataclass：`tilemap: TileMap`、`player_spawn: tuple[int,int]`（像素中心）、`enemy_spawns: list[tuple[int,int]]`、`enemy_plan: list[EnemyKind]`
- `parse_level(text: str) -> Level`；`LEVELS: list[str]`；`load_level(index: int) -> Level`
- 字符：`.` 空、`B` 砖、`S` 钢、`W` 水、`T` 树、`E` 老鹰、`P` 玩家出生、`1`-`3` 敌人出生
- `enemy_plan`：20 个 `EnemyKind`，按关卡配比生成（L1 basic 70%/fast 20%/heavy 10%；L2 45/35/20；L3 25/40/35）

**Steps:**
- [ ] 写测试：3 张地图均为 15×15、含 1 个 P 与 3 个出生点、E 位于 (7,14)、错误行数/字符抛 `ValueError`、配比数量正确。
- [ ] 实现 `levels.py` 与三张 ASCII 地图。
- [ ] 运行 `pytest tests/test_levels.py -v` 通过，提交。

### Task 3: 实体与坦克移动

**Files:** Create `tank_battle/entities.py`, `tests/test_movement.py`

**Interfaces:**
- `Direction` 枚举带 `vector`；`Owner` 枚举 PLAYER/ENEMY；`EnemyKind` 枚举 BASIC/FAST/HEAVY 带 speed/hp/score/color_key
- `Tank(x,y,speed,hp,direction)`，属性 `rect`、`center`、`alive`、`cooldown`
- `PlayerTank`：`lives`、`shield_timer`、`weapon_level`、`max_bullets`
- `EnemyTank`：`kind`、`bonus`、`decision_timer`
- `Bullet(x,y,direction,speed,owner)`、`PowerUp(x,y,kind,ttl)`、`PowerUpKind` STAR/GRENADE/SHIELD/LIFE、`Explosion(x,y,timer=0.4)`
- `Game._move_tank(tank, direction, dt, tanks)`：分轴、子步 ≤4px、转向吸附格中心（容差 8px）

**Steps:**
- [ ] 写测试：向右移动增加 x；撞砖墙停住；不能走出边界；1 格宽通道可穿过；两坦克不重叠。
- [ ] 实现实体与移动，测试通过，提交。

### Task 4: 子弹、命中与基地

**Files:** Create `tank_battle/game.py`, `tests/test_combat.py`

**Interfaces:**
- `GameState` 枚举 MENU/PLAYING/PAUSED/LEVEL_CLEAR/GAME_OVER/VICTORY
- `Game(level_index=0, seed=None)`，属性：`state`、`player`、`enemies`、`bullets`、`powerups`、`explosions`、`score`、`lives`、`enemies_remaining`、`level_index`
- `Game.update(dt, move: Direction|None = None, fire: bool = False)`
- 子弹 4px 子步；优先级：地形→坦克→基地；玩家子弹不伤玩家，敌方子弹不伤敌人；命中砖墙移除重叠格

**Steps:**
- [ ] 写测试：子弹打碎砖墙、被钢墙挡下、穿水、击毁敌人加分、玩家中弹掉命并复活无敌、基地被毁 → GAME_OVER。
- [ ] 实现射击、子弹推进、命中与死亡流程，测试通过，提交。

### Task 5: 敌人 AI 与刷怪

**Files:** Create `tank_battle/ai.py`, `tests/test_ai.py`, `tests/test_spawning.py`

**Interfaces:**
- `decide(enemy, game, rng) -> tuple[Direction, bool]`（方向、是否开火）；对齐玩家/基地时开火；撞墙或计时到期重新决策；30% 随机方向
- `Game._update_enemies(dt)`、`Game._spawn_enemy()`
- 刷新：`SPAWN_INTERVAL` 秒、同屏 ≤4、库存 20、第 4/8/12…辆为 `bonus=True`、三出生点轮换

**Steps:**
- [ ] 写测试（固定种子）：直线对准玩家时开火；超时改变方向；刷怪不超 4；20 辆后停止；每 4 辆 1 辆奖励。
- [ ] 实现 `ai.py` 与刷怪逻辑，测试通过，提交。

### Task 6: 道具、计分与关卡流程

**Files:** Modify `tank_battle/game.py`; Create `tests/test_powerups.py`, `tests/test_flow.py`

**Interfaces:**
- 击杀奖励坦克生成随机道具，12 秒过期；拾取生效 STAR/GRENADE/SHIELD/LIFE
- 清空库存且场上无敌人 → `LEVEL_CLEAR`，2 秒后下一关或 `VICTORY`
- 生命为 0 或基地被毁 → `GAME_OVER`；`Game.restart()`、`Game.toggle_pause()`

**Steps:**
- [ ] 写测试：四种道具效果、道具过期、击杀奖励坦克掉落、关卡切换、第 3 关通关 VICTORY、失败与重启。
- [ ] 实现逻辑，测试通过，提交。

### Task 7: 渲染、主循环与截图

**Files:** Create `tank_battle/renderer.py`, `tank_battle/app.py`, `main.py`, `tests/test_smoke.py`, `tools/make_screenshot.py`

**Interfaces:**
- `Renderer(screen, fonts=None)`，`draw(game, elapsed)`：战场、地形、坦克、子弹、爆炸、道具、HUD、菜单/暂停/结算遮罩
- `App().run()`；固定步长 1/60；按键：方向/WASD、空格/J、P、R、Enter、Esc
- `main.py` 捕获 pygame 缺失并给出中文安装提示

**Steps:**
- [ ] 写无头冒烟测试（`SDL_VIDEODRIVER=dummy`，模拟 300 帧）。
- [ ] 实现渲染与主循环；`python tools/make_screenshot.py` 生成 `docs/screenshot.png`。
- [ ] 冒烟测试通过，提交。

### Task 8: 文档、CI 与发布

**Files:** Create `README.md`, `LICENSE`, `.github/workflows/ci.yml`; Modify `.gitignore`

**Steps:**
- [ ] README：简介、截图、安装、运行、操作、结构、测试、License。
- [ ] CI：Ubuntu + Python 3.12，`SDL_VIDEODRIVER=dummy` 跑 pytest。
- [ ] 全量 `pytest -q` 通过，提交。
- [ ] `git push -u origin main`（HTTPS + Credential Manager 浏览器登录）。

## Self-Review

- 覆盖：玩法/地形/敌人/道具/关卡/界面/测试/发布均有对应任务。
- 类型一致性：`Game.update(dt, move, fire)`、`TileMap` 方法、`decide()` 签名在各任务间一致。
- 无占位符；数值均来自 spec。
