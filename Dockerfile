FROM python:3.12-slim-bookworm

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir .

RUN mkdir -p /scans

USER nobody

ENTRYPOINT ["python", "-m", "adf_scan"]
