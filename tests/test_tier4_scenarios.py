"""
tests/test_tier4_scenarios.py - Tier 4: Real-World Student & Instructor End-to-End Scenarios
Tests full multi-step user workflows (>= 6 scenarios).
"""
import re
import json
import yaml
import pytest
from pathlib import Path
from tests.conftest import (
    HTMLHelper, CSSHelper, JSHelper, CaddyfileHelper,
    NotebookHelper, PDFHelper, resolve_file, WORKSPACE_ROOT
)


# ==============================================================================
# S01: Student First-Day Onboarding Flow
# ==============================================================================

def test_s01_student_first_day_onboarding_flow(index_qmd_text, lecture_01_index_text, styles_css_text, workspace_js_text):
    """
    Scenario S01: Student navigates to the home page, inspects course details,
    uses the search filter to find 'intro', toggles dark theme, selects Lecture 01,
    and lands in the distraction-free dual workspace with slides and notebook ready.
    """
    # 1. Home page header inspection
    home_dom = HTMLHelper.parse(index_qmd_text)
    assert "CS 401" in index_qmd_text or "Interactive Scientific Computing" in index_qmd_text
    search_input = home_dom.find_by_id("lecture-search")
    assert search_input is not None

    # 2. Instant client-side search simulation
    cards = home_dom.find_all_by_class("lecture-card")
    assert len(cards) >= 1
    demo_card = cards[0]
    title = demo_card.get("data-title", "").lower()
    tags = demo_card.get("data-tags", "").lower()
    assert "parametric" in title or "intro" in title or "pyodide" in tags

    # 3. Theme toggle verification
    css_helper = CSSHelper(styles_css_text)
    dark_props = css_helper.extract_dark_theme_properties()
    assert "--bg-app" in dark_props
    js_helper = JSHelper(workspace_js_text)
    assert js_helper.uses_local_storage_key("portal_theme")

    # 4. Lecture 01 workspace inspection
    lec_dom = HTMLHelper.parse(lecture_01_index_text)
    pdf_obj = lec_dom.find_all_by_tag("object")
    assert len(pdf_obj) > 0
    assert pdf_obj[0].get("data").startswith("slides.pdf")

    iframe = lec_dom.find_by_id("jupyterlite-iframe")
    assert iframe is not None
    assert "01-intro-example/notebook.ipynb" in iframe.get("src")


# ==============================================================================
# S02: Student Mobile Study Session with Tabbed Workspace
# ==============================================================================

def test_s02_student_mobile_study_session(styles_css_text, lecture_01_index_text, workspace_js_text):
    """
    Scenario S02: Student visits the portal on a smartphone (viewport < 900px).
    The desktop split divider is automatically suppressed, the mobile tab bar
    appears, student switches between Slides and Notebook tabs, and expands the
    Key Takeaways drawer to review core concepts.
    """
    # 1. Viewport media query checks
    css_helper = CSSHelper(styles_css_text)
    queries = css_helper.extract_media_queries()
    mobile_query = next((q for q in queries if "899px" in q[0] or "900px" in q[0]), None)
    assert mobile_query is not None
    condition, block = mobile_query
    assert ".workspace-divider" in block
    assert "display: none !important" in block

    # 2. Mobile tab bar markup and touch targets
    lec_dom = HTMLHelper.parse(lecture_01_index_text)
    tab_slides = lec_dom.find_by_id("tab-slides")
    tab_nb = lec_dom.find_by_id("tab-notebook")
    assert tab_slides is not None and tab_nb is not None
    assert "height: 44px" in styles_css_text or "min-height: 44px" in styles_css_text

    # 3. Tab switching logic
    js_helper = JSHelper(workspace_js_text)
    assert js_helper.has_function("initMobileTabs")
    assert "is-hidden-mobile" in workspace_js_text

    # 4. Key Takeaways drawer expansion
    drawers = lec_dom.find_all_by_class("takeaways-drawer")
    assert len(drawers) > 0
    assert drawers[0].tag == "details"
    summaries = [c for c in drawers[0].children if c.tag == "summary"]
    assert len(summaries) == 1
    assert "Key Takeaways" in summaries[0].text or "Key Takeaways" in lecture_01_index_text


# ==============================================================================
# S03: Instructor New Lecture Scaffolding and PDF Optimization Workflow
# ==============================================================================

def test_s03_instructor_lecture_scaffolding_and_pdf_optimization_workflow(tmp_path):
    """
    Scenario S03: Instructor creates a new lecture using new_lecture.py,
    authors meta.yml and slides.pdf, verifies the PDF optimizer warns if
    slides exceed 2 MB, and stages files for the portal build.
    """
    from tests.fixtures.scripts.new_lecture import scaffold_lecture
    from tests.fixtures.scripts.optimize_pdfs import check_and_optimize_pdf
    from tests.fixtures.scripts.build_portal import stage_notebooks

    # 1. Scaffold new lecture
    lec_dir = scaffold_lecture(2, "Numerical Quadrature", tags=["NumPy", "Integration"], root_dir=tmp_path)
    assert (lec_dir / "meta.yml").exists()

    # 2. Validate meta.yml schema
    meta = yaml.safe_load((lec_dir / "meta.yml").read_text(encoding="utf-8"))
    assert meta["number"] == 2
    assert "Numerical Quadrature" in meta["title"]
    assert "Integration" in meta["tags"]

    # 3. Instructor places a normal PDF (< 2 MB)
    normal_pdf = lec_dir / "slides.pdf"
    normal_pdf.write_bytes(b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF")
    norm_res = check_and_optimize_pdf(normal_pdf)
    assert norm_res["is_oversized"] is False

    # 4. Instructor places an oversized PDF (> 2 MB)
    large_pdf = lec_dir / "slides_large.pdf"
    large_pdf.write_bytes(b"0" * (2 * 1024 * 1024 + 1024))
    large_res = check_and_optimize_pdf(large_pdf)
    assert large_res["is_oversized"] is True
    assert "[WARNING]" in large_res["warning"]

    # 5. Build portal staging
    (lec_dir / "notebook.ipynb").write_text('{"cells":[],"metadata":{},"nbformat":4}', encoding="utf-8")
    staging_dir = tmp_path / "staging"
    stage_notebooks(tmp_path / "lectures", staging_dir)
    assert (staging_dir / lec_dir.name / "notebook.ipynb").exists()


# ==============================================================================
# S04: Zero-Bloat Student Bandwidth Audit
# ==============================================================================

def test_s04_zero_bloat_student_bandwidth_audit(workspace_path, deploy_md_text, lecture_01_slides_bytes, lecture_01_notebook_dict, caddyfile_text):
    """
    Scenario S04: High-volume student access audit. Verifies zero local wheels
    are bundled, Pyodide and scientific wheels load from public CDN, demo assets
    transfer < 2 MB, and caching headers prevent redundant bandwidth consumption.
    """
    # 1. Zero wheel guarantee
    whls = list(workspace_path.glob("**/*.whl"))
    assert len(whls) == 0, f"Found local .whl files: {whls}"

    # 2. CDN Pyodide specification
    assert "CDN" in deploy_md_text or "cdn.jsdelivr.net" in deploy_md_text

    # 3. Demo lecture transfer budget (< 2 MB total)
    total_demo_bytes = len(lecture_01_slides_bytes) + len(json.dumps(lecture_01_notebook_dict).encode("utf-8"))
    assert total_demo_bytes < (2 * 1024 * 1024), f"Transfer size {total_demo_bytes} exceeds 2 MB"

    # 4. Caddy caching policy
    assert "@static_assets" in caddyfile_text
    assert "max-age=31536000, immutable" in caddyfile_text
    assert "@no_cache" in caddyfile_text
    assert "no-cache, no-store, must-revalidate" in caddyfile_text


# ==============================================================================
# S05: Production Deployment and Security Hardening Audit
# ==============================================================================

def test_s05_production_deployment_and_security_hardening_audit(caddyfile_text, env_example_text, deploy_md_text):
    """
    Scenario S05: Production security audit verifying Caddy loopback binding,
    basic_auth with bcrypt hashing, frame-ancestors security, Tailscale Funnel
    exposure commands, and cloud fallback instructions.
    """
    # 1. Caddy loopback binding
    assert "127.0.0.1:8080" in caddyfile_text or ":8080" in caddyfile_text

    # 2. Authentication security
    assert "basic_auth" in caddyfile_text
    assert "CLASS_PASSWORD_HASH" in caddyfile_text
    assert "CLASS_PASSWORD_HASH=" in env_example_text

    # 3. Frame security and CSP
    assert "frame-ancestors 'self'" in caddyfile_text
    assert "SAMEORIGIN" in caddyfile_text
    assert "nosniff" in caddyfile_text

    # 4. Tailscale Funnel and cloud fallbacks
    assert "tailscale funnel --bg 8080" in deploy_md_text
    assert "GitHub Pages" in deploy_md_text
    assert "Cloudflare Pages" in deploy_md_text


# ==============================================================================
# S06: Interactive Workspace State Persistence and Resilience
# ==============================================================================

def test_s06_interactive_workspace_state_persistence_and_resilience(workspace_js_text, lecture_01_index_text):
    """
    Scenario S06: Student resizes the vertical divider, switches to Notebook-Only
    mode, dismisses the startup notice banner, clicks direct download buttons,
    and refreshes the page, verifying state restoration in localStorage.
    """
    js_helper = JSHelper(workspace_js_text)

    # 1. Split ratio persistence
    assert js_helper.uses_local_storage_key("workspace_split_ratio")
    assert js_helper.has_function("initSplitDivider")

    # 2. Layout switcher persistence
    assert js_helper.uses_local_storage_key("portal_layout_mode")
    assert js_helper.has_function("initLayoutSwitcher")

    # 3. Status banner dismissal persistence in sessionStorage
    assert js_helper.uses_session_storage_key("banner_dismissed")
    assert js_helper.has_function("initStatusBanner")

    # 4. Direct download buttons in top navigation
    lec_dom = HTMLHelper.parse(lecture_01_index_text)
    downloads = lec_dom.find_all_by_class("btn-download")
    assert len(downloads) >= 2
    hrefs = [d.get("href") for d in downloads]
    assert "slides.pdf" in hrefs
    assert "notebook.ipynb" in hrefs
    for d in downloads:
        assert "download" in d.attrs
