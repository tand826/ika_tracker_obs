from typing import NamedTuple


class Shape(NamedTuple):
    h: int
    w: int

    def __repr__(self):
        return f"Shape(h={self.h}, w={self.w})"


class Coord(NamedTuple):
    x: int
    y: int

    def __repr__(self):
        return f"Coord(x={self.x}, y={self.y})"


class Size:

    # h, w = 1080, 1920のときに計測した値
    tracker_h = 110
    tracker_w = 130
    icon_h = 91
    icon_w = 91
    name_h = 28
    name_w = 130
    triangle_h = 12
    triangle_w = 11

    def __init__(self, view_height, view_width):
        self.height = view_height
        self.width = view_width

    @property
    def tracker(self):
        return Shape(
            h=int(self.tracker_h*self.height/1080),
            w=int(self.tracker_w*self.width/1920)
        )

    @property
    def icon(self):
        return Shape(
            h=int(self.icon_h*self.height/1080),
            w=int(self.icon_w*self.width/1920)
        )

    @property
    def name(self):
        return Shape(
            h=int(self.name_h*self.height/1080),
            w=int(self.name_w*self.width/1920)
        )

    @property
    def triangle(self):
        return Shape(
            h=int(self.triangle_h*self.height/1080),
            w=int(self.triangle_w*self.width/1920)
        )

    def triangle_to_name(self, triangle: Coord):
        assert 0 <= triangle.x <= self.width
        assert 0 <= triangle.y <= self.height
        return Coord(
            triangle.x - (self.tracker.w - self.triangle.w) // 2,
            triangle.y - self.triangle.h - self.name.h
        )

    def name_to_triangle(self, name: Coord):
        assert 0 <= name.x <= self.width
        assert 0 <= name.y <= self.height
        return Coord(
            name.x + (self.tracker.w - self.triangle.w) // 2,
            name.y + self.name.h + self.triangle.h
        )

    def triangle_to_tracker(self, triangle: Coord):
        assert 0 <= triangle.x <= self.width
        assert 0 <= triangle.y <= self.height
        return Coord(
            triangle.x-self.tracker.w//2,
            triangle.y-self.tracker.h+15
        )
