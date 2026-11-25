"""
tests/test_tier3_interactions.py - Tier 3: Pairwise Combinatorial Feature Interactions
Tests cross-feature interactions and state transitions (>= 19 tests).
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


def test_i01_search_filter_and_tag_chip_selection(workspace_js_text):
    """I01: Search text query and topic tag chip selection work conjunctively."""
    helper = JSHelper(workspace_js_text)
    assert helper.has_function("initLectureSearch")
    # Verify conjunction: matchesQuery && matchesTag
    assert "matchesQuery && matchesTag" in workspace_js_text

def test_i02_search_filter_and_dark_theme_toggle_persistence(workspace_js_text):
    """I02: Search filtering and theme toggle maintain independent localStorage keys."""
    helper = JSHelper(workspace_js_text)
    assert helper.uses_local_storage_key("portal_theme")
    # Search uses in-memory or DOM filtering, preserving theme preference
    assert helper.has_function("initThemeToggle")
    assert helper.has_function("initLectureSearch")

def test_i03_split_divider_and_layout_switcher_interaction(workspace_js_text, styles_css_text):
    """I03: Switching layout to slides hides divider; restoring split restores saved ratio."""
    assert "container.classList.add(`layout-${mode}`)" in workspace_js_text or "layout-" in workspace_js_text
    assert ".workspace-container.layout-slides .workspace-divider" in styles_css_text
    assert "display: none !important" in styles_css_text
    # Ratio is restored when in split mode
    assert "workspace_split_ratio" in workspace_js_text

def test_i04_split_divider_drag_and_iframe_pointer_events_overlay(workspace_js_text, styles_css_text):
    """I04: Dragging divider adds is-resizing class which sets pointer-events: none on iframes."""
    assert "document.body.classList.add('is-resizing')" in workspace_js_text
    assert "document.body.classList.remove('is-resizing')" in workspace_js_text
    assert "body.is-resizing iframe" in styles_css_text
    assert "pointer-events: none !important" in styles_css_text

def test_i05_layout_switcher_slides_only_and_fullscreen_capability(lecture_01_index_text, styles_css_text):
    """I05: Slides-Only mode expands left pane to 100% and embeds PDF viewer."""
    dom = HTMLHelper.parse(lecture_01_index_text)
    obj = dom.find_all_by_tag("object")
    assert len(obj) > 0
    assert obj[0].get("type") == "application/pdf"
    assert ".workspace-container.layout-slides .pane-slides" in styles_css_text

def test_i06_layout_switcher_notebook_only_and_status_banner(lecture_01_index_text, styles_css_text):
    """I06: Notebook-Only mode renders single-notebook iframe at 100% with status banner."""
    dom = HTMLHelper.parse(lecture_01_index_text)
    banner = dom.find_by_id("workspace-status-banner")
    assert banner is not None
    iframe = dom.find_by_id("jupyterlite-iframe")
    assert iframe is not None
    assert ".workspace-container.layout-notebook .pane-notebook" in styles_css_text

def test_i07_mobile_viewport_and_tab_switcher_slides_to_notebook(workspace_js_text, styles_css_text):
    """I07: Mobile breakpoint switches to tabs and updates is-hidden-mobile classes."""
    helper = CSSHelper(styles_css_text)
    assert any("899px" in q[0] or "900px" in q[0] for q in helper.extract_media_queries())
    assert "tabSlides.addEventListener" in workspace_js_text
    assert "tabNotebook.addEventListener" in workspace_js_text
    assert "is-hidden-mobile" in workspace_js_text

def test_i08_mobile_viewport_and_collapsible_takeaways_drawer(styles_css_text, lecture_01_index_text):
    """I08: In mobile viewport, takeaways drawer retains full accessibility without overflow."""
    dom = HTMLHelper.parse(lecture_01_index_text)
    details = dom.find_all_by_tag("details")
    assert len(details) > 0
    helper = CSSHelper(styles_css_text)
    assert helper.has_rule(r"\.takeaways-drawer")

def test_i09_caddy_basic_auth_and_env_password_hash_loading(caddyfile_text, env_example_text):
    """I09: Caddyfile basic_auth uses environment variable defined in .env.example."""
    assert "CLASS_PASSWORD_HASH" in caddyfile_text
    assert "CLASS_PASSWORD_HASH" in env_example_text
    assert "basic_auth" in caddyfile_text

def test_i10_caddy_compression_and_immutable_static_caching(caddyfile_text):
    """I10: Caddyfile pairs zstd/gzip compression with 1-year immutable caching on static assets."""
    assert "encode zstd gzip" in caddyfile_text
    assert "@static_assets" in caddyfile_text
    assert "max-age=31536000, immutable" in caddyfile_text

def test_i11_caddy_no_cache_headers_and_jupyter_notebook_delivery(caddyfile_text):
    """I11: *.ipynb and *.html match @no_cache to guarantee fresh notebook delivery."""
    assert "@no_cache" in caddyfile_text
    assert "*.ipynb" in caddyfile_text
    assert "no-cache, no-store, must-revalidate" in caddyfile_text

def test_i12_caddy_frame_security_and_inline_pdf_embedding(caddyfile_text):
    """I12: frame-ancestors 'self' and Content-Disposition inline permit embedded PDF rendering."""
    assert "frame-ancestors 'self'" in caddyfile_text
    assert "Content-Disposition" in caddyfile_text
    assert "inline" in caddyfile_text

def test_i13_build_pipeline_and_zero_local_wheels_guarantee(build_portal_script_path):
    """I13: build_portal.py verifies zero .whl files post-build."""
    code = build_portal_script_path.read_text(encoding="utf-8")
    assert "assert_zero_wheels" in code
    assert "site_dir" in code

def test_i14_build_pipeline_staging_and_data_subfolder_preservation(tmp_path):
    """I14: Staging preserves both notebook and data/ folder for Pyodide access."""
    from tests.fixtures.scripts.build_portal import stage_notebooks
    lec = tmp_path / "lectures" / "01-calc"
    lec.mkdir(parents=True)
    (lec / "notebook.ipynb").write_text("{}", encoding="utf-8")
    (lec / "data").mkdir()
    (lec / "data" / "points.json").write_text("[]", encoding="utf-8")

    stg = tmp_path / "staging"
    stage_notebooks(tmp_path / "lectures", stg)

    assert (stg / "01-calc" / "notebook.ipynb").exists()
    assert (stg / "01-calc" / "data" / "points.json").exists()

def test_i15_lecture_scaffolding_and_pdf_size_auditor(tmp_path):
    """I15: Scaffolding starter PDF conforms to optimize_pdfs 2 MB size audit."""
    from tests.fixtures.scripts.new_lecture import scaffold_lecture
    from tests.fixtures.scripts.optimize_pdfs import check_and_optimize_pdf
    lec_dir = scaffold_lecture(2, "DiffEq", root_dir=tmp_path)
    # Write a small starter PDF
    dummy_pdf = lec_dir / "slides.pdf"
    dummy_pdf.write_bytes(b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF")
    res = check_and_optimize_pdf(dummy_pdf)
    assert res["is_oversized"] is False

def test_i16_lecture_scaffolding_and_demo_meta_schema_alignment(tmp_path, lecture_01_meta_text):
    """I16: Newly scaffolded meta.yml contains same required schema keys as Demo 01."""
    from tests.fixtures.scripts.new_lecture import scaffold_lecture
    demo_meta = yaml.safe_load(lecture_01_meta_text)
    lec_dir = scaffold_lecture(3, "Algebra", root_dir=tmp_path)
    new_meta = yaml.safe_load((lec_dir / "meta.yml").read_text(encoding="utf-8"))
    for required_key in ["number", "title", "slug", "date", "tags", "takeaways"]:
        assert required_key in new_meta, f"Missing key {required_key} in scaffolded meta.yml"
        assert required_key in demo_meta

def test_i17_makefile_targets_and_powershell_make_ps1_parity(makefile_text, make_ps1_text):
    """I17: Makefile and make.ps1 have exact target name parity across all 8 targets."""
    targets = ["setup", "new-lecture", "optimize-pdfs", "build", "hash-password", "serve", "funnel-up", "funnel-down"]
    for t in targets:
        assert f"{t}:" in makefile_text
        assert f'"{t}"' in make_ps1_text

def test_i18_add_lecture_agent_skill_and_bandwidth_guardrail(add_lecture_skill_text):
    """I18: Agent skill SKILL.md embeds CDN Pyodide and zero bundled wheels guardrails."""
    assert "CDN" in add_lecture_skill_text or "Pyodide" in add_lecture_skill_text
    assert ".whl" in add_lecture_skill_text or "wheels" in add_lecture_skill_text.lower()

def test_i19_relative_path_resolution_across_nested_lecture_and_lite(lecture_01_index_text):
    """I19: Lecture workspace page resolves all parent navigation and Lite URLs relatively."""
    dom = HTMLHelper.parse(lecture_01_index_text)
    back_link = dom.find_all_by_class("nav-back-link")
    assert len(back_link) > 0
    assert back_link[0].get("href") == "../../index.html"

    iframe = dom.find_by_id("jupyterlite-iframe")
    assert iframe.get("src").startswith("../../lite/notebooks/index.html")
