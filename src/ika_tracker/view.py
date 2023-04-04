import logging
import random
import string
from pathlib import Path

import numpy as np
import cv2

import ika_tracker
from ika_tracker.game import Game
from ika_tracker.board import Board
from ika_tracker.size import Size, Coord
from ika_tracker.ika import Ika


class OBSView:

    def __init__(self, client):
        self.client = client
        self.ika = {}

        self.load_settings()
        self.game = Game(client=self.client, name="game", view_width=self.width, view_height=self.height)
        self.board = Board(client=self.client, name="board", view_width=self.width, view_height=self.height)
        self.size = Size(view_width=self.width, view_height=self.height)
        self.triangles = self.get_triangle()

        self.last_used_roi = None

    def get_triangle(self):
        base = Path(ika_tracker.__file__).parent/".tri"
        tris = [
            cv2.imread(f"{base}/tri1.png"),
            cv2.imread(f"{base}/tri2.png"),
            cv2.imread(f"{base}/tri3.png"),
        ]
        return tris

    def get_random_name(self, n=8):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=n))

    def load_settings(self, name=False):
        outputs = self.client.get_output_list().outputs
        for output in outputs:
            if name and output["outputName"] == name:
                self.width = output["outputWidth"]
                self.height = output["outputHeight"]
                break
            elif not name:
                if output["outputWidth"] > 0:
                    self.width = output["outputWidth"]
                    self.height = output["outputHeight"]
                    break
        else:
            raise ValueError("Not found: outputs have no width and height.")

    def get_marked_ika(self):
        game = self.game.get_screen(view_width=self.width, view_height=self.height)
        rois = self.board.get_roi(resize_as=game)
        self.last_used_roi = rois

        ikas = []
        for roi in rois:
            marked = game * roi[:, :, np.newaxis]

            triangle = self.search_ika(marked, key=self.triangles, thresh=0.5)
            if not triangle:
                continue

            tracker = self.size.triangle_to_tracker(triangle)
            ikas.append(
                Ika(
                    name=self.get_random_name(),
                    client=self.client,
                    view_height=self.height,
                    view_width=self.width,
                    triangle_x=triangle.x,
                    triangle_y=triangle.y,
                    tracker_img=game[
                        tracker.y: tracker.y+self.size.tracker.h,
                        tracker.x: tracker.x+self.size.tracker.w])
            )
        return ikas

    def update_ika(self, ika: Ika):
        game = self.game.get_screen(view_width=self.width, view_height=self.height)
        roi = ika.get_roi(resize_as=game, expand=True)
        marked = game * roi[:, :, np.newaxis]

        if not self.search_ika(marked, key=ika.name_img, thresh=0.9):
            return

        triangle = self.search_ika(marked, key=self.triangles, thresh=0.9)
        if not triangle:
            ika.missing += 1
            logging.info(f"missing: {ika.name} {ika.missing} times.")
            return

        tracker = self.size.triangle_to_tracker(triangle)

        logging.info(f"updated: {ika.name}")
        self.ika[ika.name] = Ika(
            name=ika.name,
            client=self.client,
            view_height=self.height,
            view_width=self.width,
            triangle_x=triangle.x,
            triangle_y=triangle.y,
            tracker_img=game[
                tracker.y: tracker.y+self.size.tracker.h,
                tracker.x: tracker.x+self.size.tracker.w])

    def search_ika(self, roi, key, thresh):
        if type(key) == list:
            found = np.stack([cv2.matchTemplate(roi, k, cv2.TM_CCOEFF_NORMED) for k in key]).max(axis=0)
            key = key[0]
        else:
            found = cv2.matchTemplate(roi, key, cv2.TM_CCOEFF_NORMED)

        _, similarity, _, location = cv2.minMaxLoc(found)

        if similarity < thresh:
            # たぶんマークの中にキャラアイコンがない
            logging.info(f"not found: val={similarity}.")
            return False

        logging.info(f"found: val={similarity}.")
        return Coord(location[0], location[1])

    def board_is_updated(self):
        return self.last_used_roi != self.board.get_roi()

    def is_tracking(self, ika: Ika):
        # 旧trackerのなかに新name_imgがあるかにする
        for old_ika in self.ika.values():
            found = cv2.matchTemplate(old_ika.tracker_img, ika.name_img, cv2.TM_CCOEFF_NORMED)
            _, similarity, _, _ = cv2.minMaxLoc(found)
            if similarity > 0.9:
                logging.info(f"already tracking: val={similarity}.")
                return True
        return False

    def get_tracking_ika(self):
        return self.ika.values()

    def stop_tracking(self, ika: Ika):
        self.ika[ika.name].remove_image()
        self.ika[ika.name].remove_source()
        del self.ika[ika.name]

    def start_tracking(self, ika: Ika):
        self.ika[ika.name] = ika
        self.ika[ika.name].create()

    def update_tracking(self, ika: Ika):
        self.update_ika(ika)
        self.ika[ika.name].update(
            self.ika[ika.name].triangle.x,
            self.ika[ika.name].triangle.y
        )

    def clean_tracking(self):
        for ika in self.ika.values():
            ika.remove_image()
            ika.remove_source()
