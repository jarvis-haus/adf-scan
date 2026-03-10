import requests as requests_lib
import responses

from adf_scan.escl import ESCLClient, ESCLError, ScannerBusyError
from conftest import SCANNER_STATUS_ADF_EMPTY, SCANNER_STATUS_ADF_LOADED

import pytest

BASE = "https://192.168.1.100/eSCL"


@pytest.fixture
def client() -> ESCLClient:
    return ESCLClient(BASE)


@responses.activate
def test_get_scanner_status_adf_loaded(client: ESCLClient) -> None:
    responses.get(f"{BASE}/ScannerStatus", body=SCANNER_STATUS_ADF_LOADED)

    status = client.get_scanner_status()
    assert status.state == "Idle"
    assert status.adf_state == "ScannerAdfLoaded"


@responses.activate
def test_adf_has_paper_true(client: ESCLClient) -> None:
    responses.get(f"{BASE}/ScannerStatus", body=SCANNER_STATUS_ADF_LOADED)
    assert client.adf_has_paper() is True


@responses.activate
def test_adf_has_paper_false(client: ESCLClient) -> None:
    responses.get(f"{BASE}/ScannerStatus", body=SCANNER_STATUS_ADF_EMPTY)
    assert client.adf_has_paper() is False


@responses.activate
def test_create_scan_job(client: ESCLClient) -> None:
    responses.post(
        f"{BASE}/ScanJobs",
        status=201,
        headers={"Location": "/eSCL/ScanJobs/42"},
    )

    job_url = client.create_scan_job(300, "RGB24", "Adf")
    assert job_url == "/eSCL/ScanJobs/42"


@responses.activate
def test_create_scan_job_busy(client: ESCLClient) -> None:
    responses.post(f"{BASE}/ScanJobs", status=503)

    with pytest.raises(ScannerBusyError):
        client.create_scan_job(300, "RGB24", "Adf")


@responses.activate
def test_retrieve_pages(client: ESCLClient) -> None:
    job_url = "https://192.168.1.100/eSCL/ScanJobs/42"
    responses.get(f"{job_url}/NextDocument", body=b"\xff\xd8page1")
    responses.get(f"{job_url}/NextDocument", body=b"\xff\xd8page2")
    responses.get(f"{job_url}/NextDocument", status=404)

    pages = client.retrieve_pages(job_url)
    assert len(pages) == 2
    assert pages[0] == b"\xff\xd8page1"
    assert pages[1] == b"\xff\xd8page2"


@responses.activate
def test_retrieve_pages_relative_url(client: ESCLClient) -> None:
    responses.get(
        "https://192.168.1.100/eSCL/ScanJobs/7/NextDocument",
        body=b"\xff\xd8data",
    )
    responses.get(
        "https://192.168.1.100/eSCL/ScanJobs/7/NextDocument",
        status=404,
    )

    pages = client.retrieve_pages("/eSCL/ScanJobs/7")
    assert len(pages) == 1


@responses.activate
def test_status_network_error(client: ESCLClient) -> None:
    responses.get(
        f"{BASE}/ScannerStatus",
        body=requests_lib.ConnectionError("unreachable"),
    )

    with pytest.raises(ESCLError, match="Failed to get scanner status"):
        client.get_scanner_status()
