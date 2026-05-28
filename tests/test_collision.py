import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from sf6_env.engine.collision import Box, boxes_overlap


def test_boxes_overlap_basic():
    a = (0, 0, 10, 10)
    b = (5, 5, 15, 15)
    assert boxes_overlap(a, b)


def test_boxes_no_overlap():
    a = (0, 0, 10, 10)
    b = (20, 20, 30, 30)
    assert not boxes_overlap(a, b)


def test_box_to_world_facing_right():
    box = Box(x_offset=50, y_offset=80, w=60, h=40)
    l, b, r, t = box.to_world(char_x=300, char_y=0, facing=1)
    assert l == 300 + 50 - 30
    assert r == l + 60
    assert b == 80
    assert t == 80 + 40


def test_box_to_world_facing_left():
    box = Box(x_offset=50, y_offset=80, w=60, h=40)
    l, b, r, t = box.to_world(char_x=300, char_y=0, facing=-1)
    assert l == 300 - 50 - 30
    assert r == l + 60
