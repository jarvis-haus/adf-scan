# ADF Scan

Automatic document feeder (ADF) scanner daemon. Polls an HP Envy 6400 (or any eSCL-compatible scanner) for documents in the ADF tray and saves them as PDFs — fully unattended.

## How it works

The daemon continuously polls the scanner's eSCL status endpoint. When paper is detected in the ADF, it:

1. Creates a scan job via the eSCL protocol
2. Downloads all pages as JPEGs
3. Converts them to a lossless PDF using `img2pdf`
4. Saves the PDF with a timestamp filename (e.g. `scan_20260310_143022.pdf`)
5. Resumes polling for the next document

No SANE, no drivers — just direct HTTP/XML communication with the printer.

## Configuration

All settings are via environment variables:

| Variable | Required | Default | Description |
|---|---|---|---|
| `SCANNER_URL` | Yes | — | eSCL base URL, e.g. `https://192.168.1.100:443/eSCL` |
| `SCAN_DIR` | No | `/scans` | Output directory for PDFs |
| `POLL_INTERVAL` | No | `5` | Seconds between ADF status checks |
| `SCAN_RESOLUTION` | No | `300` | DPI resolution |
| `SCAN_COLOR_MODE` | No | `RGB24` | Color mode (`RGB24` or `Grayscale8`) |
| `SCAN_DUPLEX` | No | `false` | Enable duplex scanning (if supported) |

### Finding your scanner URL

Your HP Envy 6400 exposes eSCL over HTTPS. To find the URL:

```bash
# Check if the printer responds on the eSCL endpoint
curl -k https://<PRINTER-IP>:443/eSCL/ScannerStatus
```

The printer IP can be found in your router's DHCP client list or on the printer's network settings screen.

## Local development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run the daemon
SCANNER_URL=https://192.168.1.100:443/eSCL SCAN_DIR=./scans python -m adf_scan

# Run tests
pytest -v
```

## Docker

```bash
# Build
docker build -t adf-scan .

# Run
docker run \
  -e SCANNER_URL=https://192.168.1.100:443/eSCL \
  -v $(pwd)/scans:/scans \
  adf-scan
```

## CI/CD: GitHub Actions + DockerHub

The included workflow (`.github/workflows/build.yaml`) builds and pushes the Docker image to DockerHub on every push to `main` and on version tags.

## Kubernetes: Helm chart

### Install from the git repo

```bash
git clone <this-repo>
cd adf-scan

helm install adf-scan ./chart/adf-scan \
  --set image.repository=yourdockerhubuser/adf-scan \
  --set scanner.url=https://192.168.1.100:443/eSCL
```

### Customize

Override values inline or with a file:

```bash
helm install adf-scan ./chart/adf-scan -f my-values.yaml
```

Example `my-values.yaml`:

```yaml
image:
  repository: yourdockerhubuser/adf-scan

scanner:
  url: https://192.168.1.100:443/eSCL
  pollInterval: "10"
  resolution: "600"

persistence:
  storageClass: longhorn
  size: 20Gi
```

### Accessing scanned PDFs

The scans are stored on a PersistentVolumeClaim. You can access them by:

- Mounting the same PVC in another pod (e.g. a file browser like FileBrowser)
- Using `kubectl cp` to copy files out:
  ```bash
  kubectl cp adf-scan-<pod>:/scans/scan_20260310_143022.pdf ./scan.pdf
  ```
- Using an NFS-backed StorageClass so the volume is accessible from the network
- Mount it to the same folder as the Paperless consume folder to automatically import scanned documents
