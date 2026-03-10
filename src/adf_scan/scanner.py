from __future__ import annotations

import logging
from datetime import datetime
from threading import Event

from .config import Config
from .escl import ESCLClient, ESCLError, ScannerBusyError
from .pdf import pages_to_pdf

logger = logging.getLogger(__name__)


class ScannerDaemon:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.client = ESCLClient(config.scanner_url)
        self._stop = Event()

    def run(self) -> None:
        logger.info(
            "Starting ADF scanner daemon, polling %s every %.1fs",
            self.config.scanner_url,
            self.config.poll_interval,
        )
        self.config.scan_dir.mkdir(parents=True, exist_ok=True)

        while not self._stop.is_set():
            try:
                if self.client.adf_has_paper():
                    self._do_scan()
                    continue  # re-poll immediately after a scan
            except ScannerBusyError:
                logger.info("Scanner is busy, will retry")
            except ESCLError as exc:
                logger.warning("Scanner communication error: %s", exc)
            except Exception:
                logger.exception("Unexpected error")

            self._stop.wait(timeout=self.config.poll_interval)

        logger.info("Scanner daemon stopped")

    def _do_scan(self) -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        logger.info("Paper detected in ADF, starting scan (source: %s)...", self.config.scan_source)

        job_url = self.client.create_scan_job(
            resolution=self.config.scan_resolution,
            color_mode=self.config.scan_color_mode,
            source=self.config.scan_source,
        )
        logger.info("Scan job created: %s", job_url)

        try:
            pages = self.client.retrieve_pages(job_url)
        finally:
            self.client.delete_scan_job(job_url)

        if not pages:
            logger.warning("Scan job returned zero pages")
            return

        output_path = self.config.scan_dir / f"scan_{timestamp}.pdf"
        pages_to_pdf(pages, output_path)
        logger.info("Saved %d-page PDF: %s", len(pages), output_path)

    def stop(self) -> None:
        self._stop.set()
