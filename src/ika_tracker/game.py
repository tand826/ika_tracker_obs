from ika_tracker.source import OBSSource


class Game(OBSSource):
    """ゲーム画面のソース"""

    def __init__(self, client, name, view_width, view_height, debug=False):
        super().__init__(client=client, name=name)
        self.view_width = view_width
        self.view_height = view_height
        self.debug = debug

    def is_birdseye(self):
        # 全体図画面であるか？
        # 画像処理でなんとかする
        return True
