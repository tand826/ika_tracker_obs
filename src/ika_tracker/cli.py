import time
import logging
import signal

from obsws_python import ReqClient

from ika_tracker.view import OBSView


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, help="OBS Websocket host", default="localhost")
    parser.add_argument("--port", type=int, help="OBS Websocket port", default=4455)
    parser.add_argument("--password", type=str, help="OBS Websocket password")
    parser.add_argument("--interval", type=int, help="Interval to check for new ika", default=0.1)
    parser.add_argument("--missed", type=int, help="Number of missing to stop tracking", default=3)
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s :%(message)s"
    )

    with ReqClient(host=args.host, port=args.port, password=args.password) as client:
        view = OBSView(client)
        logging.info("view initialized")

        try:
            while True:
                # 同じroiからは1回しか検出をしない
                if view.board_is_updated():

                    # viewから、特定の色でマークされた領域内のイカを取得
                    ikas = view.get_marked_ika()
                    logging.info(f"found {len(ikas)} ikas")

                    for ika in ikas:
                        # そのイカが追跡中でなかったら、追跡リストに加える
                        if not view.is_tracking(ika):
                            view.start_tracking(ika)
                            logging.info(f"start tracking {ika.name}")

                    # 追跡中のイカのリストを取得
                    ikas = view.get_tracking_ika()
                    logging.info(f"tracking {len(ikas)} ikas")

                    # 3回以上見失ったイカは追跡リストから削除
                    to_stop = []
                    for i in range(len(ikas)):
                        ika = list(ikas)[i]
                        if ika.missing >= args.missed:
                            to_stop.append(ika)
                    while len(to_stop) > 0:
                        ika = to_stop.pop()
                        logging.info(f"stop tracking {ika.name}")
                        view.stop_tracking(ika)

                for ika in ikas:
                    # イカの位置を更新
                    view.update_tracking(ika)
                    logging.info(f"updated {ika.name}")

                logging.info(f"waiting {args.interval} seconds for next check")
                time.sleep(args.interval)
        finally:
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            view.clean_tracking()
            signal.signal(signal.SIGTERM, signal.SIG_DFL)
            signal.signal(signal.SIGINT, signal.SIG_DFL)


if __name__ == "__main__":
    main()
