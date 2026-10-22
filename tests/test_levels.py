import pytest

from tank_battle.config import ENEMIES_PER_LEVEL, GRID_H, GRID_W
from tank_battle.entities import EnemyKind
from tank_battle.levels import LEVELS, build_enemy_plan, load_level, parse_level


def test_all_levels_parse() -> None:
    for index in range(len(LEVELS)):
        level = load_level(index)
        assert level.tilemap.cols == GRID_W
        assert level.tilemap.rows == GRID_H
        assert len(level.enemy_spawns) == 3
        assert len(level.enemy_plan) == ENEMIES_PER_LEVEL


def test_base_at_bottom_center() -> None:
    level = load_level(0)
    assert level.tilemap.at(7, 14).value == "E"
    assert level.base_pos == (7 * 32 + 16, 14 * 32 + 16)


def test_player_spawn_is_empty_terrain() -> None:
    level = load_level(0)
    col = int(level.player_spawn[0] // 32)
    row = int(level.player_spawn[1] // 32)
    assert level.tilemap.at(col, row).value == "."


def test_enemy_plan_composition() -> None:
    plan = build_enemy_plan(0)
    assert len(plan) == ENEMIES_PER_LEVEL
    assert plan.count(EnemyKind.BASIC) == 14
    assert plan.count(EnemyKind.FAST) == 4
    assert plan.count(EnemyKind.HEAVY) == 2

    plan3 = build_enemy_plan(2)
    assert plan3.count(EnemyKind.HEAVY) == 7
    assert plan3.count(EnemyKind.FAST) == 8


def test_bad_row_count() -> None:
    with pytest.raises(ValueError):
        parse_level("1......2......3")


def test_bad_char() -> None:
    rows = list(LEVELS[0])
    rows[1] = "X" + rows[1][1:]
    with pytest.raises(ValueError):
        parse_level("\n".join(rows))


def test_missing_player() -> None:
    rows = [line.replace("P", ".") for line in LEVELS[0]]
    with pytest.raises(ValueError):
        parse_level("\n".join(rows))
