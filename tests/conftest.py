from pathlib import Path

import pytest

from adf_scan.config import Config


@pytest.fixture
def config(tmp_path: Path) -> Config:
    return Config(
        scanner_url="https://192.168.1.100/eSCL",
        scan_dir=tmp_path / "scans",
        poll_interval=1.0,
    )


SCANNER_STATUS_ADF_LOADED = """\
<?xml version="1.0" encoding="UTF-8"?>
<scan:ScannerStatus xmlns:scan="http://schemas.hp.com/imaging/escl/2011/05/03"
                    xmlns:pwg="http://www.pwg.org/schemas/2010/12/sm">
  <pwg:Version>2.0</pwg:Version>
  <pwg:State>Idle</pwg:State>
  <scan:AdfState>ScannerAdfLoaded</scan:AdfState>
</scan:ScannerStatus>"""

SCANNER_STATUS_ADF_EMPTY = """\
<?xml version="1.0" encoding="UTF-8"?>
<scan:ScannerStatus xmlns:scan="http://schemas.hp.com/imaging/escl/2011/05/03"
                    xmlns:pwg="http://www.pwg.org/schemas/2010/12/sm">
  <pwg:Version>2.0</pwg:Version>
  <pwg:State>Idle</pwg:State>
  <scan:AdfState>ScannerAdfEmpty</scan:AdfState>
</scan:ScannerStatus>"""
