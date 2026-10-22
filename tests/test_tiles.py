from tank_battle.config import TILE
from tank_battle.tiles import TileMap, TileType


def make_map() -> TileMap:
    return TileMap.from_rows(
        [
            "..............",
            ".B............",
            "..............",
            "..............",
            "..............",
            "..............",
            "..............",
            "..............",
            "..............",
            "..............",
            "..............",
            "..............",
            "..............",
            "..............",
            "..............",
            ".E............",
        ]
    )


def test_brick_blocks_tank_but_not_bullet() -> None:
    tilemap = make_map()
    rect = (1 * TILE, 1 * TILE, TILE, TILE)
    assert tilemap.blocks_tank(rect) is True
    assert tilemap.blocks_bullet(rect) is True


def test_steel_blocks_both() -> None:
    tilemap = make_map()
    tilemap.grid[2][2] = TileType.STEEL
    rect = (2 * TILE, 2 * TILE, TILE, TILE)
    assert tilemap.blocks_tank(rect) is True
    assert tilemap.blocks_bullet(rect) is True


def test_water_blocks_tank_but_not_bullet() -> None:
    tilemap = make_map()
    tilemap.grid[3][3] = TileType.WATER
    rect = (3 * TILE, 3 * TILE, TILE, TILE)
    assert tilemap.blocks_tank(rect) is True
    assert tilemap.blocks_bullet(rect) is False


def test_trees_block_nothing() -> None:
    tilemap = make_map()
    tilemap.grid[4][4] = TileType.TREE
    rect = (4 * TILE, 4 * TILE, TILE, TILE)
    assert tilemap.blocks_tank(rect) is False
    assert tilemap.blocks_bullet(rect) is False


def test_destroy_brick_only() -> None:
    tilemap = make_map()
    assert tilemap.destroy(1, 1) is True
    assert tilemap.at(1, 1) is TileType.EMPTY
    assert tilemap.destroy(1, 1) is False


def test_out_of_bounds_blocks_tank() -> None:
    tilemap = make_map()
    assert tilemap.blocks_tank((-4, 0, 26, 26)) is True
    assert tilemap.blocks_tank((0, 0, 26, 26)) is False


def test_eagle_and_bricks_in_rect() -> None:
    tilemap = make_map()
    eagle_rect = (1 * TILE, 15 * TILE, 26, 26)
    assert tilemap.eagle_hit(eagle_rect) is True
    brick_rect = (1 * TILE, 1 * TILE, TILE, TILE)
    assert tilemap.bricks_in(brick_rect) == [(1, 1)]
