from __future__ import annotations

from pathlib import Path

import img2pdf


def pages_to_pdf(pages: list[bytes], output_path: Path) -> None:
    pdf_bytes = img2pdf.convert(pages)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(pdf_bytes)
