# 坦克大战（Tank Battle）设计文档

- 日期：2026-10-22
- 仓库：https://github.com/sqgug123/tank-battle
- 技术栈：Python 3.10+ / pygame 2.6+，无外部素材、无外部服务

## 1. 目标

做一个可以直接 `python main.py` 启动的经典《坦克大战》复刻：守住基地、消灭一波波敌人、连续通过 3 张手工关卡。仓库公开，代码结构清晰、有自动化测试、clone 即玩。

非目标（YAGNI）：

- 不做联机、不做双人同屏（后续可扩展，但本期不实现）。
- 不做关卡编辑器、不做存档、不做排行榜。
- 不做音效。
- 不接入任何图片/字体/音频资源文件；所有画面用 pygame 图元绘制。

## 2. 核心玩法

| 项目 | 规则 |
| --- | --- |
| 目标 | 守住地图底部中央的老鹰基地，消灭每关 20 辆敌方坦克 |
| 玩家生命 | 3 条；被击中损失 1 条并重生，生命耗尽即失败 |
| 玩家复活 | 在出生点重生，3 秒无敌闪烁 |
| 关卡 | 3 张手工地图，敌人总量与刷新速度逐关提升 |
| 失败 | 基地被摧毁，或玩家生命耗尽 |
| 胜利 | 通过第 3 关 |
| 同屏敌人 | 最多 4 辆；场上敌人 ≤ 2 且尚有库存时，每 2 秒刷新 1 辆 |
| 刷新点 | 顶部左、中、右三个出生点轮换 |
| 操作 | 方向键 / WASD 移动，空格 / J 开火，P 暂停，R 重开，Esc 退出 |

### 地形

- 砖墙：子弹命中即破坏该格；坦克不可通过。
- 钢墙：不可破坏；子弹会被弹掉；坦克不可通过。
- 水域：坦克不可通过；子弹可通过。
- 树林：坦克与子弹均可通过；绘制在坦克上层，形成遮挡。
- 基地（老鹰）：占 1 格，四周由砖墙包围；被任意子弹命中即失败。

### 敌人

| 类型 | 速度 | 生命 | 分数 | 外观 |
| --- | --- | --- | --- | --- |
| 普通 basic | 60 px/s | 1 | 100 | 灰绿色 |
| 快速 fast | 110 px/s | 1 | 200 | 黄褐色 |
| 重装 heavy | 48 px/s | 3 | 300 | 深绿色，血量用颜色深浅区分 |

- 每关敌人按关卡比例混合：第 1 关 basic 为主，第 3 关 heavy/fast 为主。
- 每 4 辆敌人中有 1 辆为"闪烁奖励坦克"，被击毁后掉落道具。

### 道具（存在 12 秒后消失）

| 道具 | 效果 |
| --- | --- |
| 星形 STAR | 火力升级：最多同时 2 发子弹，子弹速度提升 |
| 手雷 GRENADE | 立即摧毁场上所有敌方坦克 |
| 护盾 SHIELD | 玩家 10 秒无敌 |
| 生命 LIFE | 玩家生命 +1 |

### 关卡流程

`菜单 → 第 1 关 → 过关结算 → 第 2 关 → ... → 第 3 关 → 胜利`
任意时刻玩家生命耗尽或基地被毁 → `游戏结束`，可按 R 从第 1 关重开。

## 3. 界面与美术

- 窗口 640×480：左侧 480×480 战场，右侧 160×480 HUD。
- 战场为 15×15 格，每格 32px。
- 坦克 26×26，按朝向绘制（履带 + 炮管），受击/无敌时闪烁。
- 子弹 6×6，带拖尾色块；命中产生扩散粒子爆炸。
- HUD 显示：剩余敌人图标、玩家生命、当前关卡、分数、操作提示。
- 全部颜色与形状集中定义，像素风、深色背景。
- 中文字体：优先使用系统字体（Microsoft YaHei / SimHei / Noto Sans CJK），找不到时回退到 pygame 默认字体；文字内容同时提供英文兜底，保证乱码不会导致崩溃。

## 4. 架构

```
tank-battle/
├── main.py
├── tank_battle/
│   ├── __init__.py
│   ├── config.py        # 尺寸、速度、颜色、常量
│   ├── tiles.py         # 地形枚举、TileMap、可通行/可破坏查询
│   ├── entities.py      # Tank、Bullet、PowerUp、Explosion、Player、EnemyTank
│   ├── ai.py            # 敌人决策（纯函数 + 可注入随机源）
│   ├── levels.py        # 3 张 ASCII 关卡与解析
│   ├── game.py          # 纯逻辑状态机：update(dt)、事件队列、胜负判定
│   ├── renderer.py      # 战场、坦克、HUD、菜单与遮罩绘制
│   └── app.py           # pygame 初始化、输入、固定步长主循环
├── tests/
│   ├── test_tiles.py
│   ├── test_levels.py
│   ├── test_movement.py
│   ├── test_combat.py
│   ├── test_ai.py
│   ├── test_spawning.py
│   ├── test_powerups.py
│   ├── test_flow.py
│   └── test_smoke.py
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
└── .github/workflows/ci.yml
```

### 分层约束

- `config.py`、`tiles.py`、`entities.py`、`ai.py`、`levels.py`、`game.py` **不得 import pygame**。
- 逻辑层只依赖 `dataclasses`、`math`、`random`、`typing`，可在无显示器环境测试。
- `renderer.py` 只读取逻辑层状态并绘制，不修改状态。
- `app.py` 负责输入映射与主循环，把输入转换为逻辑层命令（移动/开火/暂停/重开）。

### 关键数据

- `TileMap`：`grid: list[list[TileType]]`，提供 `is_blocked_for_tank(x, y, w, h)`、`is_blocked_for_bullet(...)`、`destroy_brick(col, row)`。
- `Game`：持有 `tilemap`、`player`、`enemies`、`bullets`、`powerups`、`explosions`、`state`、`score`、`level_index`、`enemies_remaining`。
- `Game.update(dt)` 处理：输入意图、移动与分轴碰撞、射击冷却、子弹推进与命中、AI 决策、道具拾取与过期、刷怪、胜负判定、状态切换。

### 碰撞

- AABB 矩形相交。
- 坦克移动分轴处理：先 X 后 Y，每轴独立检测地形与其它坦克，避免贴墙抖动。
- 转向时做"对齐辅助"：若垂直轴坐标距离最近的格中心 ≤ 8px，则吸附到格中心，保证 1 格宽通道可顺畅通过。
- 子弹按 4px 子步推进，防止高速穿墙；命中优先级：地形 → 坦克 → 基地。

## 5. 错误处理

- 未安装 pygame：`main.py` 捕获 `ImportError`，打印中文安装提示并 `sys.exit(1)`，不抛堆栈。
- 窗口初始化失败：捕获 `pygame.error`，提示显卡/显示环境问题后退出。
- 关卡数据格式错误：`levels.parse_level` 校验行数与字符集，抛出带行列信息的 `ValueError`；CI 中解析全部关卡防止手滑。
- 游戏中不因单个实体异常崩溃：AI 决策与道具生成均用 try 边界外的纯函数实现，越界坐标一律视为不可通行。

## 6. 测试策略

- `pytest`，逻辑层零 pygame 依赖。
- 覆盖：
  - 地形可通行/可破坏查询；子弹打碎砖墙、被钢墙挡住、穿过水域。
  - AABB 碰撞与分轴移动（贴墙不抖动、不能穿墙）。
  - AI 在直线对齐时开火；撞墙后改变方向（注入固定随机种子）。
  - 刷怪上限 4、库存 20、奖励坦克每 4 辆出现 1 辆。
  - 道具四种效果与 12 秒过期。
  - 基地被毁 → GAME_OVER；生命耗尽 → GAME_OVER；清空 20 辆 → LEVEL_CLEAR；第 3 关通关 → VICTORY。
  - 无头冒烟测试：`SDL_VIDEODRIVER=dummy` 下创建 App，模拟 300 帧不崩溃。
- CI：GitHub Actions，Ubuntu + Python 3.12，`pip install -r requirements.txt pytest` 后 `pytest -q`。

## 7. 交付与发布

- 本地仓库 `tank-battle/`，默认分支 `main`，提交信息使用 Conventional Commits。
- 远程 `origin` 已配置为 `https://github.com/sqgug123/tank-battle.git`。
- README 包含：项目简介、截图、安装、运行、操作说明、项目结构、测试命令、License。
- 截图通过无头渲染生成 `docs/screenshot.png`，提交进仓库。
- MIT License。
