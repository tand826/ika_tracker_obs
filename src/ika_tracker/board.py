import numpy as np
import cv2

from ika_tracker.source import OBSSource


class Board(OBSSource):
    """JamBoardとか、書き込む用の画面のソース。
        背景が白いものに書き込んでいることを想定し、240を超える領域を白紙領域として扱い透過させる。
    """

    def __init__(self, client, name, view_width, view_height):
        super().__init__(client=client, name=name)
        self.view_width = view_width
        self.view_height = view_height
        self.chroma = False

    def get_mark_coord(self, binary_screen):
        contours = cv2.findContours(binary_screen, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
        return contours

    def get_roi(self, resize_as=False):
        screen = self.get_screen(view_width=self.view_width, view_height=self.view_height)
        screen = self.crop_background(screen)
        screen = self.get_binary_screen(screen)
        coords = self.get_mark_coord(screen)

        rois = []
        for coord in coords:
            blank = np.zeros(screen.shape, dtype=np.uint8)
            pts = np.array([coord]).reshape(1, -1, 2)
            roi = cv2.fillPoly(blank, pts=pts, color=1)

            if resize_as is not False:
                roi = cv2.resize(roi, (resize_as.shape[1], resize_as.shape[0]))

            # 上10%、下10%、左10%、右10%はキャラがいないので除外
            roi[:roi.shape[0]//10, :] = 0
            roi[-roi.shape[0]//10:, :] = 0
            roi[:, :roi.shape[1]//10] = 0
            roi[:, -roi.shape[1]//10:] = 0
            rois.append(roi)
        return rois

    def expand_roi(self, roi):
        roi = cv2.dilate(roi, np.ones((3, 3), np.uint8), iterations=1)
        return roi

    def get_in_range(self, screen, color):
        lower = np.maximum(np.array(color) - 20, 0)
        upper = np.minimum(np.array(color) + 10, 255)
        return cv2.inRange(screen, lower, upper)

    def get_binary_screen(self, screen, color=[255, 255, 255]):
        # マークの色は白色を想定。後に引数で指定できるようにする。
        # クロマキー領域のみを切り抜いた、RGBのscreen
        return self.get_in_range(screen, color)

    def crop_background(self, screen, chroma=False, strict=False):
        if not chroma and self.chroma is False:
            # 最も多く見られる色をchromaとして扱う
            self.chroma = np.array([
                np.histogram(screen[:, :, 0], bins=255)[0].argmax()+1,
                np.histogram(screen[:, :, 1], bins=255)[0].argmax()+1,
                np.histogram(screen[:, :, 2], bins=255)[0].argmax()+1
            ])

        binary = self.get_in_range(screen, self.chroma)
        h, w = binary.shape
        # まずは、クロマキーの背景色がある領域を取り出す
        # 縦横半分以上が背景色である領域を取り出す
        for i in range(0, h//2):
            if (binary[i] == 255).sum() > w // 2:
                top = i
                break
        else:
            raise ValueError("no background found")
        for i in range(h-1, h//2, -1):
            if (binary[i] == 255).sum() > w // 2:
                bottom = i
                break
        else:
            raise ValueError("no background found")
        for i in range(0, w//2):
            if (binary[:, i] == 255).sum() > h // 2:
                left = i
                break
        else:
            raise ValueError("no background found")
        for i in range(w-1, w//2, -1):
            if (binary[:, i] == 255).sum() > h // 2:
                right = i
                break
        else:
            raise ValueError("no background found")

        if not strict:
            return screen[top:bottom, left:right]
        else:
            print("trying to crop background in strict mode")
            raise NotImplementedError("strict mode is not implemented")
