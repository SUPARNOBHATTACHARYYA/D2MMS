#!/usr/bin/env python3
"""
scripts/optimize_pdfs.py - Audits and compresses Beamer slides exceeding 2 MB
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

MAX_PDF_SIZE_BYTES = 2 * 1024 * 1024  # 2 MB

def check_and_optimize_pdf(pdf_path: Path) -> dict:
    size = pdf_path.stat().st_size
    is_oversized = size > MAX_PDF_SIZE_BYTES
    result = {
        "path": str(pdf_path),
        "size_bytes": size,
        "is_oversized": is_oversized,
        "optimized": False,
        "warning": None
    }

    if is_oversized:
        size_mb = size / (1024 * 1024)
        msg = f"[WARNING] {pdf_path} is {size_mb:.2f} MB, exceeding the 2 MB threshold."
        print(msg, file=sys.stderr)
        result["warning"] = msg

        # Attempt Ghostscript compression if available
        gs_cmd = shutil.which("gs") or shutil.which("gswin64c")
        if gs_cmd:
            tmp_out = pdf_path.with_suffix(".opt.pdf")
            cmd = [
                gs_cmd,
                "-sDEVICE=pdfwrite",
                "-dCompatibilityLevel=1.4",
                "-dPDFSETTINGS=/ebook",
                "-dNOPAUSE",
                "-dQUIET",
                "-dBATCH",
                f"-sOutputFile={tmp_out}",
                str(pdf_path)
            ]
            try:
                subprocess.run(cmd, check=True)
                if tmp_out.exists() and tmp_out.stat().st_size < size:
                    tmp_out.replace(pdf_path)
                    result["optimized"] = True
                    result["size_bytes"] = pdf_path.stat().st_size
            except Exception as e:
                print(f"[ERROR] Ghostscript optimization failed: {e}", file=sys.stderr)
    return result

def scan_all_lectures(lectures_dir: Path) -> list:
    results = []
    for pdf_file in lectures_dir.glob("*/slides.pdf"):
        results.append(check_and_optimize_pdf(pdf_file))
    return results

if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    lectures = root / "lectures"
    if lectures.exists():
        scan_all_lectures(lectures)
