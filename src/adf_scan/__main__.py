from __future__ import annotations

import logging
import signal
import sys

from .config import Config
from .scanner import ScannerDaemon


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        stream=sys.stdout,
    )

    config = Config.from_env()
    daemon = ScannerDaemon(config)

    def handle_signal(signum: int, frame: object) -> None:
        logging.getLogger(__name__).info("Received signal %d, shutting down", signum)
        daemon.stop()

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    daemon.run()


if __name__ == "__main__":
    main()
