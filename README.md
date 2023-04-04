# IKA Tracker for OBS Studio
- OBS Studioで、Splatoon3のメモリープレーヤーの配信をしているときに、オーバーレイで表示した書き込みから、イカちゃんを追跡するアプリケーションです。
- 注意：未完成です。

# 使い方
- OBS
  - 28.0以降必須（obs websocketを手動でインストールする場合28.0未満でも可）
  - ゲーム画面を「game」という名前のソースとして追加
  - 書き込み画面を「board」という名前のソースとして追加
- obs websocket
  - オンにする
  - パスワードを設定しない
- 書き込みアプリ
  - 背景色と、書き込み色をカラーピッカーなどで確認
- ika_tracker
  - pythonをインストール
    - python >= 3.6
  - インストール
    - `pip install git+https://github.com/tand826/ika_tracker_obs.git`
  - 実行
    - `ika_tracker`

# 使用例
- youtubeの動画を貼りたい
