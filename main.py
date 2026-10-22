"""游戏入口：python main.py"""

from __future__ import annotations

import sys


def main() -> int:
    try:
        import pygame  # noqa: F401
    except ImportError:
        print("缺少依赖 pygame。请先运行：")
        print("    python -m pip install -r requirements.txt")
        return 1

    from tank_battle.app import App

    try:
        App().run()
    except pygame.error as exc:  # type: ignore[attr-defined]
        print(f"无法初始化游戏窗口：{exc}")
        print("请确认当前环境支持图形界面（或设置了正确的 SDL 视频驱动）。")
        return 1
    finally:
        pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
