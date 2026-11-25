---
name: add-lecture
description: Scaffold and author a new university lecture module with 16:9 Beamer slides and interactive JupyterLite notebook.
---

# Add Lecture Skill

## Overview
This skill guides the creation of a new lecture module in the University Lecture Portal, pairing a compiled Beamer PDF with an in-browser runnable Jupyter notebook.

## When to Use
- Adding a new lecture module to the course catalog.
- Updating or expanding existing lecture notebooks and slides.

## Step-by-Step Workflow
1. **Scaffold Directory**:
   Run `python scripts/new_lecture.py --number <NN> --title "<Title>" --tags "<Tag1,Tag2>"`
2. **Author Lecture Metadata**:
   Edit `lectures/<slug>/meta.yml` with valid number, title, date, tags, and takeaways.
3. **Add 16:9 Beamer Slides**:
   Place compiled `slides.pdf` into `lectures/<slug>/slides.pdf`.
   Run `python scripts/optimize_pdfs.py` to ensure slides are < 2 MB.
4. **Author Interactive Notebook**:
   Edit `lectures/<slug>/notebook.ipynb`. Ensure scientific dependencies (NumPy, SciPy, Matplotlib) load via CDN Pyodide.
5. **Build Portal**:
   Run `python scripts/build_portal.py` (or `make build`).
6. **Verify Acceptance Criteria**:
   Verify dual workspace loads slides on left and notebook on right with zero `.whl` files bundled.
   Ensure relative path resolution works cleanly across nested lecture routes and JupyterLite.
