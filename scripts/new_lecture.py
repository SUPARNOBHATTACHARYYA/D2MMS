#!/usr/bin/env python3
"""
scripts/new_lecture.py - Scaffolds a new lecture directory with starter meta.yml, slides.pdf, and notebook.ipynb
"""
import os
import sys
import argparse
from pathlib import Path

def scaffold_lecture(number: int, title: str, tags: list = None, date: str = None, root_dir: Path = None):
    if root_dir is None:
        root_dir = Path(__file__).resolve().parent.parent

    slug = f"{number:02d}-{title.lower().replace(' ', '-').replace('&', 'and')}"
    # Clean slug
    slug = "".join(c for c in slug if c.isalnum() or c == '-')
    lecture_dir = root_dir / "lectures" / slug
    lecture_dir.mkdir(parents=True, exist_ok=True)

    tags = tags or ["Scientific Computing", "Python"]
    date_str = date or "2026-09-10"

    meta_file = lecture_dir / "meta.yml"
    if not meta_file.exists():
        meta_content = f"""number: {number}
title: "{title}"
slug: "{slug}"
date: "{date_str}"
tags:
"""
        for t in tags:
            meta_content += f'  - "{t}"\n'
        meta_content += """takeaways:
  - "Understand key theoretical foundations"
  - "Run interactive computational experiments in Pyodide"
"""
        meta_file.write_text(meta_content, encoding="utf-8")

    return lecture_dir

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scaffold a new lecture")
    parser.add_argument("--number", type=int, default=2, help="Lecture number")
    parser.add_argument("--title", type=str, default="Numerical Modeling", help="Lecture title")
    args = parser.parse_args()
    res = scaffold_lecture(args.number, args.title)
    print(f"Scaffolded lecture in {res}")
