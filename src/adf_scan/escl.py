from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import requests
import urllib3
from defusedxml import ElementTree

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class ESCLError(Exception):
    pass


class ScannerBusyError(ESCLError):
    pass


@dataclass
class ScannerStatus:
    state: str
    adf_state: str


def _find_local(root: ElementTree, local_name: str) -> str | None:
    """Find element by local name, ignoring XML namespaces."""
    for elem in root.iter():
        tag = elem.tag
        if "}" in tag:
            tag = tag.split("}", 1)[1]
        if tag == local_name and elem.text:
            return elem.text.strip()
    return None


class ESCLClient:
    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self.base_url = base_url
        self.session = requests.Session()
        self.session.verify = False
        self.timeout = timeout

    def get_scanner_status(self) -> ScannerStatus:
        try:
            resp = self.session.get(
                f"{self.base_url}/ScannerStatus", timeout=self.timeout
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise ESCLError(f"Failed to get scanner status: {exc}") from exc

        root = ElementTree.fromstring(resp.content)
        state = _find_local(root, "State") or "Unknown"
        adf_state = _find_local(root, "AdfState") or "Unknown"
        return ScannerStatus(state=state, adf_state=adf_state)

    def adf_has_paper(self) -> bool:
        status = self.get_scanner_status()
        return status.adf_state == "ScannerAdfLoaded"

    def create_scan_job(
        self, resolution: int, color_mode: str, source: str
    ) -> str:
        scan_settings = f"""\
<?xml version="1.0" encoding="UTF-8"?>
<scan:ScanSettings xmlns:scan="http://schemas.hp.com/imaging/escl/2011/05/03"
                   xmlns:pwg="http://www.pwg.org/schemas/2010/12/sm">
  <pwg:Version>2.0</pwg:Version>
  <pwg:ScanRegions>
    <pwg:ScanRegion>
      <pwg:XOffset>0</pwg:XOffset>
      <pwg:YOffset>0</pwg:YOffset>
      <pwg:Width>2550</pwg:Width>
      <pwg:Height>3300</pwg:Height>
      <pwg:ContentRegionUnits>escl:ThreeHundredthsOfInches</pwg:ContentRegionUnits>
    </pwg:ScanRegion>
  </pwg:ScanRegions>
  <scan:InputSource>{source}</scan:InputSource>
  <scan:ColorMode>{color_mode}</scan:ColorMode>
  <pwg:Resolution>
    <pwg:XResolution>{resolution}</pwg:XResolution>
    <pwg:YResolution>{resolution}</pwg:YResolution>
  </pwg:Resolution>
  <pwg:DocumentFormat>image/jpeg</pwg:DocumentFormat>
</scan:ScanSettings>"""

        try:
            resp = self.session.post(
                f"{self.base_url}/ScanJobs",
                data=scan_settings,
                headers={"Content-Type": "text/xml"},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise ESCLError(f"Failed to create scan job: {exc}") from exc

        if resp.status_code == 503:
            raise ScannerBusyError("Scanner is busy")
        if resp.status_code != 201:
            raise ESCLError(
                f"Unexpected status {resp.status_code} creating scan job"
            )

        location = resp.headers.get("Location", "")
        if not location:
            raise ESCLError("No Location header in scan job response")

        return location

    def retrieve_pages(self, job_url: str) -> list[bytes]:
        pages: list[bytes] = []
        while True:
            url = f"{job_url}/NextDocument"
            if not url.startswith("http"):
                url = f"{self.base_url.rsplit('/eSCL', 1)[0]}{url}"

            try:
                resp = self.session.get(url, timeout=60)
            except requests.RequestException as exc:
                if pages:
                    logger.warning("Error retrieving page %d: %s", len(pages) + 1, exc)
                    break
                raise ESCLError(f"Failed to retrieve first page: {exc}") from exc

            if resp.status_code != 200:
                break

            pages.append(resp.content)
            logger.debug("Retrieved page %d (%d bytes)", len(pages), len(resp.content))
            time.sleep(0.5)

        return pages

    def delete_scan_job(self, job_url: str) -> None:
        url = job_url
        if not url.startswith("http"):
            url = f"{self.base_url.rsplit('/eSCL', 1)[0]}{url}"
        try:
            self.session.delete(url, timeout=self.timeout)
        except requests.RequestException:
            logger.debug("Failed to delete scan job %s (best-effort)", job_url)
