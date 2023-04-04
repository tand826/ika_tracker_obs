import base64
import io
import time
import warnings

from PIL import Image
import numpy as np
from obsws_python.error import OBSSDKError


class OBSSource:

    def __init__(self, client, name):
        self.client = client
        self.name = name

    def get_screen(self, view_width, view_height) -> np.array:
        data = self.client.get_source_screenshot(name=self.name, img_format="jpeg", width=None, height=None, quality=-1)
        string = data.image_data.split(",")[1]
        screen = Image.open(io.BytesIO(base64.b64decode(string))).resize((view_width, view_height))
        return np.array(screen)

    def get_height(self):
        if not hasattr(self, "height"):
            self.height, self.width = self.get_screen().shape[:2]
        return self.height

    def get_width(self):
        if not hasattr(self, "width"):
            self.height, self.width = self.get_screen().shape[:2]
        return self.width

    def update_source(self):
        self.client.set_input_settings(
            name=self.name,
            settings={
                "file": self.save_as},
            overlay=True)

    def create_source(self):
        self.client.create_input(
            sceneName="シーン",
            inputName=self.name,
            inputKind="image_source",
            inputSettings={
                "file": self.save_as},
            sceneItemEnabled=True)

    def remove_source(self):
        if not self.exists():
            warnings.warn(f"Source {self.name} does not exist.")
            return
        self.client.remove_input(name=self.name)
        while True:
            if self.assert_removed():
                return

    def exists(self) -> bool:
        try:
            self.client.get_input_settings(name=self.name)
            return True
        except OBSSDKError:
            return False

    def assert_removed(self) -> bool:
        start = time.time()
        while True:
            try:
                self.client.get_input_settings(name=self.name)
                now = time.time()
                if now - start > 5:
                    raise TimeoutError("Timeout")
            except OBSSDKError:
                return True
