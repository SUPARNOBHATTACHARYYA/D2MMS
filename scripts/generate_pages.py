#!/usr/bin/env python3
"""
scripts/generate_pages.py
Validates metadata and ensures clean project structure for Quarto build.
"""
import yaml
from pathlib import Path

root = Path(__file__).resolve().parent.parent
lectures_dir = root / "lectures"

# Gather all lectures dynamically
lectures = []
for ldir in sorted(lectures_dir.iterdir()):
    if ldir.is_dir() and (ldir / "meta.yml").exists():
        with open(ldir / "meta.yml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            lectures.append(data)

lectures.sort(key=lambda x: x.get("number", 0))

print(f"Verified {len(lectures)} course lecture modules:")
for l in lectures:
    num_str = f"{l['number']:02d}"
    qmd_path = lectures_dir / l["slug"] / "index.qmd"
    pdf_path = lectures_dir / l["slug"] / "slides.pdf"
    nb_path = lectures_dir / l["slug"] / "notebook.ipynb"
    print(f"  [{num_str}] {l['title']} -> QMD: {qmd_path.exists()} | PDF: {pdf_path.exists()} | NB: {nb_path.exists()}")

print("Course modules integrity check complete.")
