from pathlib import Path

import cv2
import numpy as np

import ika_tracker
from ika_tracker.source import OBSSource
from ika_tracker.size import Size, Coord


class Ika(OBSSource):
    """イカのソース

    イカは、ゲーム画面で見えるキャラアイコン(tracker)を指す。
    キャラアイコンは、
        イカの形にブキのアイコンを含んだイカアイコン(icon)と、
        キャラ名(name)と
        下向き三角形(triangle)
    を囲うように設置する。
    """

    def __init__(self, name, client, view_width, view_height, triangle_x, triangle_y, tracker_img):
        super().__init__(name=name, client=client)
        self.view_width = view_width
        self.view_height = view_height
        self.size = Size(view_height=view_height, view_width=view_width)
        self.triangle = Coord(x=triangle_x, y=triangle_y)
        self.tracker_img = tracker_img
        self.tracker_thickness = 2  # 線の太さ
        self.name_img = self.get_name_img()
        self.name_x, self.name_y = self.name_coord()
        self.save_to = Path(ika_tracker.__file__).parent/".roi"
        if not self.save_to.exists():
            self.save_to.mkdir(exist_ok=True, parents=True)
        self.save_as = str(self.save_to/f"roi_{self.name}.png")
        self.missing = 0

    def get_roi(self, resize_as=False, expand=1):
        # 探索範囲は、前回の探索範囲を少しだけ広げた範囲。
        roi = np.zeros((self.view_height, self.view_width), dtype=np.uint8)
        h = self.size.tracker.h*expand
        w = self.size.tracker.w*expand
        cv2.rectangle(
            roi,
            [
                self.triangle.x-w//2,
                self.triangle.y-h//2,
                w,
                h
            ],
            color=1,
            thickness=-1)

        if resize_as is not False:
            roi = cv2.resize(roi, (resize_as.shape[1], resize_as.shape[0]))
        return roi

    def get_name_img(self):
        top = self.size.tracker.h - self.size.triangle.h - self.size.name.h - 7
        bottom = self.size.tracker.h - self.size.triangle.h - 7

        img = self.tracker_img[
            top:bottom,
            self.size.tracker.w//4:self.size.tracker.w//4*3]
        return img

    def name_coord(self):
        name = self.size.triangle_to_name(Coord(self.triangle.x, self.triangle.y))
        return name.x, name.y

    def get_color(self):
        if self.missing == 0:
            # green
            return (0, 255, 0, 255)
        elif self.missing == 1:
            # yellow
            return (0, 255, 255, 255)
        elif self.missing == 2:
            # red
            return (0, 0, 255, 255)
        else:
            # white
            return (0, 0, 0, 255)

    def create_image(self):
        # 全体マップにおいて、ikaの位置を四角で囲う画像。
        image = np.zeros((self.view_height, self.view_width, 4), dtype=np.uint8)
        image = cv2.rectangle(
            image,
            [
                self.triangle.x-self.size.tracker.w//2,
                self.triangle.y-self.size.tracker.h,
                self.size.tracker.w,
                self.size.tracker.h
            ],
            color=self.get_color(),
            thickness=self.tracker_thickness)
        cv2.imwrite(self.save_as, image)

    def remove_image(self):
        Path(self.save_as).unlink()

    def set_coord(self, x, y):
        self.triangle = Coord(x=x, y=y)

    def create(self):
        self.create_image()
        self.create_source()

    def update(self, x, y):
        self.set_coord(x, y)
        self.create_image()
        self.update_source()

    def get(self):
        raise NotImplementedError()

    def remove(self):
        self.remove_source()

    def __str__(self):
        return f"Ika: name={self.name}, triangle.x={self.triangle.x}, triangle.y={self.triangle.y}"

    def __repr__(self):
        return f"Ika: name={self.name}, triangle.x={self.triangle.x}, triangle.y={self.triangle.y}"
