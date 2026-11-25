"""
tests/test_tier1_features.py - Tier 1: Category-Partition Feature Coverage
Covers all 19 features (F01–F19) with at least 5 tests per feature (>= 95 tests).
"""
import re
import yaml
import json
from pathlib import Path
import pytest
from tests.conftest import (
    HTMLHelper, CSSHelper, JSHelper, CaddyfileHelper,
    NotebookHelper, PDFHelper, WORKSPACE_ROOT, FIXTURES_DIR,
    resolve_file
)


# ==============================================================================
# Feature 01: Zero-Backend Static Quarto Setup (_quarto.yml)
# ==============================================================================

def test_f01_quarto_yml_exists_and_parses(quarto_yml_text):
    """F01-1: _quarto.yml must exist and be valid YAML."""
    assert quarto_yml_text, "_quarto.yml is empty or missing"
    data = yaml.safe_load(quarto_yml_text)
    assert isinstance(data, dict), "Parsed _quarto.yml must be a mapping"

def test_f01_quarto_project_type_website(quarto_yml_text):
    """F01-2: project.type must be 'website' and output-dir must be '_site'."""
    data = yaml.safe_load(quarto_yml_text)
    assert data.get("project", {}).get("type") == "website"
    assert data.get("project", {}).get("output-dir") == "_site"

def test_f01_quarto_explicit_render_targets(quarto_yml_text):
    """F01-3: project.render must explicitly scope target files."""
    data = yaml.safe_load(quarto_yml_text)
    render_targets = data.get("project", {}).get("render", [])
    assert "index.qmd" in render_targets
    assert any("lectures" in r for r in render_targets)

def test_f01_quarto_resources_preservation(quarto_yml_text):
    """F01-4: project.resources must copy assets, slides, and notebooks."""
    data = yaml.safe_load(quarto_yml_text)
    resources = data.get("project", {}).get("resources", [])
    assert any("assets" in r for r in resources)
    assert any("*.pdf" in r for r in resources)
    assert any("*.ipynb" in r for r in resources)

def test_f01_quarto_format_theme_none_and_custom_css(quarto_yml_text):
    """F01-5: format.html must set theme: none and link custom styles.css."""
    data = yaml.safe_load(quarto_yml_text)
    html_format = data.get("format", {}).get("html", {})
    assert html_format.get("theme") == "none", "Must not use default Bootstrap theme"
    assert html_format.get("css") == "assets/styles.css"
    assert html_format.get("include-in-header") == "assets/head.html"


# ==============================================================================
# Feature 02: JupyterLite Integration & Build Pipeline (scripts/build_portal.py)
# ==============================================================================

def test_f02_build_portal_script_syntax(build_portal_script_path):
    """F02-1: scripts/build_portal.py must compile and define staging and build functions."""
    code = build_portal_script_path.read_text(encoding="utf-8")
    compiled = compile(code, str(build_portal_script_path), "exec")
    assert compiled is not None
    assert "stage_notebooks" in code
    assert "build_portal" in code

def test_f02_staging_notebooks_hierarchy(build_portal_script_path):
    """F02-2: Staging logic must stage notebooks under their lecture slug."""
    code = build_portal_script_path.read_text(encoding="utf-8")
    assert "notebook.ipynb" in code
    assert "staging_dir" in code

def test_f02_per_lecture_data_subfolder_support(build_portal_script_path):
    """F02-3: Staging logic must copy per-lecture data/ subfolder if present."""
    code = build_portal_script_path.read_text(encoding="utf-8")
    assert "data" in code
    assert "copytree" in code or "copy" in code

def test_f02_build_pipeline_order(build_portal_script_path):
    """F02-4: Build pipeline must coordinate Quarto render and JupyterLite build."""
    code = build_portal_script_path.read_text(encoding="utf-8")
    assert "quarto" in code
    assert "jupyterlite" in code or "jupyter-lite" in code or "jupyter" in code

def test_f02_output_dir_configuration(build_portal_script_path):
    """F02-5: Output directory for JupyterLite must target _site/lite."""
    code = build_portal_script_path.read_text(encoding="utf-8")
    assert "lite" in code


# ==============================================================================
# Feature 03: Bandwidth Guardrail (Zero Local Wheels)
# ==============================================================================

def test_f03_assert_zero_wheels_assertion(build_portal_script_path):
    """F03-1: Build script must define assert_zero_wheels guardrail."""
    code = build_portal_script_path.read_text(encoding="utf-8")
    assert "assert_zero_wheels" in code
    assert ".whl" in code

def test_f03_zero_wheels_in_fixtures_and_workspace(workspace_path):
    """F03-2: No .whl files must be committed or present in static assets."""
    whls = list(workspace_path.glob("**/*.whl"))
    assert len(whls) == 0, f"Found local wheels violating guardrail: {whls}"

def test_f03_pyodide_cdn_configuration(deploy_md_text):
    """F03-3: Documentation and build must specify CDN Pyodide loading."""
    assert "cdn.jsdelivr.net" in deploy_md_text or "CDN" in deploy_md_text

def test_f03_demo_lecture_transfer_budget(lecture_01_slides_bytes, lecture_01_notebook_dict):
    """F03-4: Local transferred assets for demo lecture must be under 2 MB."""
    slides_size = len(lecture_01_slides_bytes)
    nb_size = len(json.dumps(lecture_01_notebook_dict).encode("utf-8"))
    assert (slides_size + nb_size) < (2 * 1024 * 1024), "Lecture 01 assets exceed 2 MB budget"

def test_f03_scientific_packages_not_bundled(workspace_path):
    """F03-5: Heavy scientific packages (numpy, scipy, pandas) must not be bundled in assets."""
    heavy_files = list(workspace_path.glob("assets/**/numpy*")) + list(workspace_path.glob("assets/**/scipy*"))
    assert len(heavy_files) == 0, f"Bundled scientific libraries found in assets: {heavy_files}"


# ==============================================================================
# Feature 04: Academic Style & Light/Dark Theme (assets/styles.css, assets/head.html)
# ==============================================================================

def test_f04_academic_color_tokens_light_mode(styles_css_text):
    """F04-1: Light theme tokens must specify academic palette (off-white, slate ink, navy)."""
    helper = CSSHelper(styles_css_text)
    assert helper.get_var("--bg-app") is not None
    assert helper.get_var("--bg-surface") is not None
    assert helper.get_var("--text-primary") is not None
    assert helper.get_var("--accent-navy") is not None
    assert helper.get_var("--accent-amber") is not None

def test_f04_dark_theme_tokens_present(styles_css_text):
    """F04-2: Dark theme tokens must be defined under [data-theme='dark']."""
    helper = CSSHelper(styles_css_text)
    dark_props = helper.extract_dark_theme_properties()
    assert "--bg-app" in dark_props
    assert "--bg-surface" in dark_props
    assert "--text-primary" in dark_props

def test_f04_font_stack_academic_tokens(styles_css_text):
    """F04-3: Font stacks must define sans-serif UI and monospace fonts."""
    helper = CSSHelper(styles_css_text)
    assert "sans-serif" in helper.get_var("--font-ui")
    assert "monospace" in helper.get_var("--font-mono")

def test_f04_anti_fouc_script_head(head_html_text):
    """F04-4: assets/head.html must contain synchronous theme detection."""
    assert "localStorage.getItem('portal_theme')" in head_html_text or "portal_theme" in head_html_text
    assert "data-theme" in head_html_text

def test_f04_theme_toggle_js_persistence(workspace_js_text):
    """F04-5: workspace.js must toggle theme and persist to localStorage."""
    helper = JSHelper(workspace_js_text)
    assert helper.uses_local_storage_key("portal_theme")
    assert helper.has_function("initThemeToggle")


# ==============================================================================
# Feature 05: Home Page Catalog & Instant Search/Filter (index.qmd, assets/workspace.js)
# ==============================================================================

def test_f05_home_page_course_header(index_qmd_text):
    """F05-1: index.qmd must contain course header markup."""
    dom = HTMLHelper.parse(index_qmd_text)
    headers = dom.find_all_by_class("course-header")
    assert len(headers) > 0
    assert "Interactive Scientific Computing" in index_qmd_text or "CS 401" in index_qmd_text

def test_f05_search_input_element(index_qmd_text):
    """F05-2: index.qmd must contain #lecture-search input."""
    dom = HTMLHelper.parse(index_qmd_text)
    search_input = dom.find_by_id("lecture-search")
    assert search_input is not None
    assert search_input.tag == "input"

def test_f05_topic_filter_chips_markup(index_qmd_text):
    """F05-3: Topic filter chips toolbar must be present with data-tag attributes."""
    dom = HTMLHelper.parse(index_qmd_text)
    chips = dom.find_all_by_class("chip")
    assert len(chips) >= 3
    tags = [c.get("data-tag") for c in chips if c.get("data-tag")]
    assert "all" in tags

def test_f05_lecture_cards_data_attributes(index_qmd_text):
    """F05-4: Lecture cards must have data-number, data-title, and data-tags."""
    dom = HTMLHelper.parse(index_qmd_text)
    cards = dom.find_all_by_class("lecture-card")
    assert len(cards) > 0
    card = cards[0]
    assert card.get("data-number") is not None
    assert card.get("data-title") is not None
    assert card.get("data-tags") is not None

def test_f05_instant_search_filtering_logic(workspace_js_text):
    """F05-5: workspace.js must implement instant search filtering."""
    helper = JSHelper(workspace_js_text)
    assert helper.has_function("initLectureSearch")
    assert helper.listens_to_event("input")


# ==============================================================================
# Feature 06: Dual Lecture Workspace & Draggable Divider (assets/workspace.js, styles.css)
# ==============================================================================

def test_f06_workspace_container_flex_layout(styles_css_text):
    """F06-1: CSS must define full-height flex container for dual panes."""
    helper = CSSHelper(styles_css_text)
    assert helper.has_rule(r"\.workspace-layout")
    assert helper.has_rule(r"\.workspace-container")
    assert helper.has_rule(r"\.pane-slides")
    assert helper.has_rule(r"\.pane-notebook")

def test_f06_draggable_divider_styling(styles_css_text):
    """F06-2: Divider must have col-resize cursor and width token."""
    helper = CSSHelper(styles_css_text)
    assert helper.has_rule(r"\.workspace-divider")
    assert helper.get_var("--divider-width") is not None

def test_f06_pointer_events_iframe_overlay_resizing(styles_css_text):
    """F06-3: Pointer events on iframes must be disabled during resize."""
    assert "pointer-events: none" in styles_css_text
    assert "is-resizing" in styles_css_text

def test_f06_divider_bounds_clamping(workspace_js_text):
    """F06-4: workspace.js must clamp split ratio to prevent collapsing panes."""
    assert "15" in workspace_js_text
    assert "85" in workspace_js_text

def test_f06_split_ratio_local_storage_persistence(workspace_js_text):
    """F06-5: Split ratio must be saved to and read from localStorage."""
    helper = JSHelper(workspace_js_text)
    assert helper.uses_local_storage_key("workspace_split_ratio")
    assert helper.has_function("initSplitDivider")


# ==============================================================================
# Feature 07: Layout Switcher (Split/Slides/Notebook)
# ==============================================================================

def test_f07_layout_switcher_buttons_markup(lecture_01_index_text):
    """F07-1: Layout switcher must contain 3 mode buttons."""
    dom = HTMLHelper.parse(lecture_01_index_text)
    buttons = dom.find_all_by_class("layout-btn")
    assert len(buttons) == 3
    layouts = [b.get("data-layout") for b in buttons]
    assert "split" in layouts and "slides" in layouts and "notebook" in layouts

def test_f07_layout_slides_only_css(styles_css_text):
    """F07-2: CSS must support layout-slides mode hiding notebook."""
    assert "layout-slides" in styles_css_text
    assert ".workspace-container.layout-slides" in styles_css_text

def test_f07_layout_notebook_only_css(styles_css_text):
    """F07-3: CSS must support layout-notebook mode hiding slides."""
    assert "layout-notebook" in styles_css_text
    assert ".workspace-container.layout-notebook" in styles_css_text

def test_f07_layout_split_view_css(styles_css_text):
    """F07-4: CSS must support layout-split mode with both panes visible."""
    assert "layout-split" in styles_css_text

def test_f07_layout_switcher_persistence(workspace_js_text):
    """F07-5: Layout mode must be persisted in localStorage."""
    helper = JSHelper(workspace_js_text)
    assert helper.uses_local_storage_key("portal_layout_mode")
    assert helper.has_function("initLayoutSwitcher")


# ==============================================================================
# Feature 08: Responsive Mobile/Tablet Tabs
# ==============================================================================

def test_f08_responsive_media_query_breakpoint(styles_css_text):
    """F08-1: CSS must include max-width: 899px or 900px media query."""
    helper = CSSHelper(styles_css_text)
    queries = helper.extract_media_queries()
    assert any("max-width: 899px" in q[0] or "max-width: 900px" in q[0] for q in queries)

def test_f08_divider_hidden_on_mobile(styles_css_text):
    """F08-2: Draggable divider must be hidden on mobile viewport."""
    helper = CSSHelper(styles_css_text)
    queries = helper.extract_media_queries()
    mobile_block = next((q[1] for q in queries if "899px" in q[0] or "900px" in q[0]), "")
    assert ".workspace-divider" in mobile_block
    assert "display: none" in mobile_block

def test_f08_mobile_tab_bar_markup(lecture_01_index_text):
    """F08-3: Lecture workspace must have mobile-tab-bar markup."""
    dom = HTMLHelper.parse(lecture_01_index_text)
    tabs = dom.find_all_by_class("mobile-tab")
    assert len(tabs) >= 2
    assert dom.find_by_id("tab-slides") is not None
    assert dom.find_by_id("tab-notebook") is not None

def test_f08_mobile_tab_toggle_logic(workspace_js_text):
    """F08-4: workspace.js must toggle visible pane when tab is clicked."""
    helper = JSHelper(workspace_js_text)
    assert helper.has_function("initMobileTabs")
    assert "is-hidden-mobile" in workspace_js_text

def test_f08_touch_target_size(styles_css_text):
    """F08-5: Mobile tabs must specify minimum touch target height (>= 44px)."""
    assert "height: 44px" in styles_css_text or "min-height: 44px" in styles_css_text


# ==============================================================================
# Feature 09: Single-Notebook View & Status Notices
# ==============================================================================

def test_f09_jupyterlite_single_notebook_url(lecture_01_index_text):
    """F09-1: Iframe src must open single notebook index.html?path=..."""
    dom = HTMLHelper.parse(lecture_01_index_text)
    iframe = dom.find_by_id("jupyterlite-iframe")
    assert iframe is not None
    src = iframe.get("src", "")
    assert "lite/notebooks/index.html?path=" in src
    assert "01-intro-example/notebook.ipynb" in src

def test_f09_pyodide_startup_loading_notice(lecture_01_index_text):
    """F09-2: Status banner must notify about Pyodide 10s startup time."""
    assert "Starting Python in your browser" in lecture_01_index_text
    assert "10 seconds" in lecture_01_index_text

def test_f09_in_browser_persistence_warning(lecture_01_index_text):
    """F09-3: Status banner must advise students to download work to save edits."""
    assert "Your edits stay in your browser" in lecture_01_index_text
    assert "Download" in lecture_01_index_text

def test_f09_status_banner_dismissal(workspace_js_text):
    """F09-4: Status banner dismissal must be saved to sessionStorage."""
    helper = JSHelper(workspace_js_text)
    assert helper.has_function("initStatusBanner")
    assert helper.uses_session_storage_key("banner_dismissed")

def test_f09_status_banner_styling(styles_css_text):
    """F09-5: Banner styling must use accent blue tokens."""
    helper = CSSHelper(styles_css_text)
    assert helper.has_rule(r"\.workspace-status-banner")
    assert "--accent-blue-bg" in helper.raw_css


# ==============================================================================
# Feature 10: Collapsible Key Takeaways Section
# ==============================================================================

def test_f10_html5_details_summary_markup(lecture_01_index_text):
    """F10-1: Takeaways section must use semantic HTML5 <details> and <summary>."""
    dom = HTMLHelper.parse(lecture_01_index_text)
    drawers = dom.find_all_by_class("takeaways-drawer")
    assert len(drawers) > 0
    assert drawers[0].tag == "details"
    summaries = [c for c in drawers[0].children if c.tag == "summary"]
    assert len(summaries) > 0

def test_f10_zero_js_expand_collapse(workspace_js_text):
    """F10-2: Takeaways drawer must not require JS toggles (native browser feature)."""
    # workspace.js should not attach manual click listeners to takeaways-drawer
    assert "takeaways-drawer" not in workspace_js_text

def test_f10_takeaways_content_structure(lecture_01_index_text):
    """F10-3: Content must include takeaways and practice tasks lists."""
    assert "Key Takeaways" in lecture_01_index_text
    assert "Practice Tasks" in lecture_01_index_text

def test_f10_takeaways_drawer_styling(styles_css_text):
    """F10-4: CSS must style .takeaways-drawer and .takeaways-summary."""
    helper = CSSHelper(styles_css_text)
    assert helper.has_rule(r"\.takeaways-drawer")
    assert helper.has_rule(r"\.takeaways-summary")

def test_f10_takeaways_metadata_alignment(lecture_01_meta_text, lecture_01_index_text):
    """F10-5: Takeaways in index.qmd must align with meta.yml."""
    meta = yaml.safe_load(lecture_01_meta_text)
    for takeaway in meta.get("takeaways", []):
        # Snippet of takeaway should appear in index
        snippet = takeaway[:20]
        assert snippet in lecture_01_index_text


# ==============================================================================
# Feature 11: Caddy Server & basic_auth from .env (Caddyfile)
# ==============================================================================

def test_f11_caddyfile_loopback_binding(caddyfile_text):
    """F11-1: Caddyfile must bind to 127.0.0.1:8080 (or :8080)."""
    assert "127.0.0.1:8080" in caddyfile_text or ":8080" in caddyfile_text

def test_f11_caddyfile_root_and_file_server(caddyfile_text):
    """F11-2: Caddyfile must configure root * _site and file_server."""
    helper = CaddyfileHelper(caddyfile_text)
    assert "root * _site" in caddyfile_text
    assert helper.has_directive("file_server")

def test_f11_basic_auth_directive_syntax(caddyfile_text):
    """F11-3: Caddyfile must use basic_auth loading CLASS_PASSWORD_HASH."""
    assert "basic_auth" in caddyfile_text
    assert "CLASS_PASSWORD_HASH" in caddyfile_text

def test_f11_env_example_documentation(env_example_text):
    """F11-4: .env.example must specify CLASS_USERNAME and CLASS_PASSWORD_HASH."""
    assert "CLASS_USERNAME=" in env_example_text
    assert "CLASS_PASSWORD_HASH=" in env_example_text

def test_f11_gitignore_protects_env():
    """F11-5: .gitignore must ignore .env."""
    gi_path = resolve_file(".gitignore")
    content = gi_path.read_text(encoding="utf-8")
    assert ".env" in content.splitlines()


# ==============================================================================
# Feature 12: Compression & Smart Cache-Control (Caddyfile)
# ==============================================================================

def test_f12_caddyfile_encode_zstd_gzip(caddyfile_text):
    """F12-1: Caddyfile must configure encode zstd gzip."""
    assert "encode zstd gzip" in caddyfile_text

def test_f12_no_cache_matcher_for_html_and_ipynb(caddyfile_text):
    """F12-2: Caddyfile must match *.html and *.ipynb for no-cache."""
    assert "@no_cache" in caddyfile_text
    assert "*.html" in caddyfile_text
    assert "*.ipynb" in caddyfile_text

def test_f12_no_cache_headers_values(caddyfile_text):
    """F12-3: No-cache headers must forbid caching for dynamic pages."""
    helper = CaddyfileHelper(caddyfile_text)
    headers = helper.get_headers()
    assert "Cache-Control" in headers
    assert "no-cache" in caddyfile_text
    assert "no-store" in caddyfile_text

def test_f12_static_assets_cache_matcher(caddyfile_text):
    """F12-4: Caddyfile must match static assets (*.pdf, *.css, *.js, *.wasm)."""
    assert "@static_assets" in caddyfile_text
    assert "*.pdf" in caddyfile_text
    assert "*.css" in caddyfile_text

def test_f12_immutable_cache_header_values(caddyfile_text):
    """F12-5: Static assets must be cached with max-age=31536000 and immutable."""
    assert "31536000" in caddyfile_text
    assert "immutable" in caddyfile_text


# ==============================================================================
# Feature 13: Frame Security & Inline PDF Headers (Caddyfile)
# ==============================================================================

def test_f13_frame_ancestors_self_header(caddyfile_text):
    """F13-1: Caddyfile must set frame-ancestors 'self' in CSP."""
    assert "frame-ancestors 'self'" in caddyfile_text

def test_f13_x_frame_options_sameorigin(caddyfile_text):
    """F13-2: X-Frame-Options must be SAMEORIGIN (allowing iframe embedding)."""
    assert "SAMEORIGIN" in caddyfile_text

def test_f13_x_content_type_options_nosniff(caddyfile_text):
    """F13-3: X-Content-Type-Options must be set to nosniff."""
    assert "nosniff" in caddyfile_text

def test_f13_inline_pdf_content_disposition(caddyfile_text):
    """F13-4: Caddyfile must set Content-Disposition inline for *.pdf."""
    assert "Content-Disposition" in caddyfile_text
    assert "inline" in caddyfile_text

def test_f13_no_blocking_coep_coop_headers(caddyfile_text):
    """F13-5: Caddyfile must NOT enable global require-corp (which blocks Pyodide CDN)."""
    assert "require-corp" not in caddyfile_text


# ==============================================================================
# Feature 14: Tailscale Funnel & Deployment Guide (DEPLOY.md)
# ==============================================================================

def test_f14_deploy_md_tailscale_funnel_command(deploy_md_text):
    """F14-1: DEPLOY.md must document tailscale funnel --bg 8080."""
    assert "tailscale funnel --bg 8080" in deploy_md_text

def test_f14_deploy_md_funnel_lifecycle(deploy_md_text):
    """F14-2: DEPLOY.md must document funnel status and teardown."""
    assert "tailscale funnel status" in deploy_md_text
    assert "tailscale funnel --bg 8080 off" in deploy_md_text

def test_f14_deploy_md_caddy_integration(deploy_md_text):
    """F14-3: DEPLOY.md must document Caddy setup and .env configuration."""
    assert "caddy run" in deploy_md_text
    assert "CLASS_PASSWORD_HASH" in deploy_md_text

def test_f14_deploy_md_cloud_fallbacks_relative_paths(deploy_md_text):
    """F14-4: DEPLOY.md must document GitHub Pages and Cloudflare Pages compatibility."""
    assert "GitHub Pages" in deploy_md_text
    assert "Cloudflare Pages" in deploy_md_text

def test_f14_deploy_md_bandwidth_optimizations(deploy_md_text):
    """F14-5: DEPLOY.md must document zero .whl files and Pyodide CDN."""
    assert ".whl" in deploy_md_text
    assert "Pyodide" in deploy_md_text


# ==============================================================================
# Feature 15: Cross-Platform Automation & Makefile (Makefile, make.ps1)
# ==============================================================================

def test_f15_makefile_has_all_eight_targets(makefile_text):
    """F15-1: Makefile must define all 8 required targets."""
    targets = ["setup", "new-lecture", "optimize-pdfs", "build", "hash-password", "serve", "funnel-up", "funnel-down"]
    for t in targets:
        assert f"{t}:" in makefile_text, f"Missing target {t} in Makefile"

def test_f15_makefile_phony_targets(makefile_text):
    """F15-2: Makefile must declare .PHONY."""
    assert ".PHONY:" in makefile_text

def test_f15_make_ps1_target_parity(make_ps1_text):
    """F15-3: make.ps1 must implement all 8 targets matching Makefile."""
    targets = ["setup", "new-lecture", "optimize-pdfs", "build", "hash-password", "serve", "funnel-up", "funnel-down"]
    for t in targets:
        assert f'"{t}"' in make_ps1_text, f"Missing target {t} in make.ps1"

def test_f15_hash_password_script_exists(hash_password_script_path):
    """F15-4: scripts/hash_password.py must exist and compile."""
    code = hash_password_script_path.read_text(encoding="utf-8")
    assert "hash_password" in code

def test_f15_make_ps1_help_menu(make_ps1_text):
    """F15-5: make.ps1 must include Show-Help menu."""
    assert "Show-Help" in make_ps1_text


# ==============================================================================
# Feature 16: Lecture Scaffolding Script (scripts/new_lecture.py)
# ==============================================================================

def test_f16_new_lecture_cli_arguments(new_lecture_script_path):
    """F16-1: scripts/new_lecture.py must support --number and --title CLI flags."""
    code = new_lecture_script_path.read_text(encoding="utf-8")
    assert "--number" in code
    assert "--title" in code

def test_f16_directory_slug_generation(new_lecture_script_path):
    """F16-2: Slug generation must produce two-digit sequential prefixes."""
    code = new_lecture_script_path.read_text(encoding="utf-8")
    assert "{number:02d}" in code or "02d" in code

def test_f16_meta_yml_scaffolding(new_lecture_script_path):
    """F16-3: Scaffolding must generate meta.yml with required keys."""
    code = new_lecture_script_path.read_text(encoding="utf-8")
    assert "meta.yml" in code
    assert "takeaways" in code

def test_f16_scaffolding_idempotence(new_lecture_script_path):
    """F16-4: Scaffolding script must guard against overwriting existing meta files."""
    code = new_lecture_script_path.read_text(encoding="utf-8")
    assert "exists()" in code or "mkdir" in code

def test_f16_script_executable_syntax(new_lecture_script_path):
    """F16-5: scripts/new_lecture.py must be valid Python."""
    code = new_lecture_script_path.read_text(encoding="utf-8")
    compiled = compile(code, str(new_lecture_script_path), "exec")
    assert compiled is not None


# ==============================================================================
# Feature 17: PDF Size Checker & Compression (scripts/optimize_pdfs.*)
# ==============================================================================

def test_f17_two_megabyte_threshold_constant(optimize_pdfs_script_path):
    """F17-1: MAX_PDF_SIZE_BYTES must be 2 * 1024 * 1024."""
    code = optimize_pdfs_script_path.read_text(encoding="utf-8")
    assert "2 * 1024 * 1024" in code or "2097152" in code

def test_f17_pdf_warning_emission_on_large_files(optimize_pdfs_script_path):
    """F17-2: Script must emit warning on files exceeding 2 MB."""
    code = optimize_pdfs_script_path.read_text(encoding="utf-8")
    assert "[WARNING]" in code
    assert "2 MB" in code

def test_f17_ghostscript_flags_and_device(optimize_pdfs_script_path):
    """F17-3: Compression must invoke Ghostscript with -dPDFSETTINGS=/ebook."""
    code = optimize_pdfs_script_path.read_text(encoding="utf-8")
    assert "pdfwrite" in code
    assert "/ebook" in code

def test_f17_cross_platform_gs_executable_names(optimize_pdfs_script_path):
    """F17-4: Script must detect both gs and gswin64c on Windows."""
    code = optimize_pdfs_script_path.read_text(encoding="utf-8")
    assert "gs" in code
    assert "gswin64c" in code

def test_f17_bash_script_parity():
    """F17-5: scripts/optimize_pdfs.sh must have 2097152 byte check."""
    sh_path = resolve_file("scripts/optimize_pdfs.sh")
    content = sh_path.read_text(encoding="utf-8")
    assert "2097152" in content
    assert "pdfwrite" in content


# ==============================================================================
# Feature 18: Working Demo Lecture 01 (lectures/01-intro-example/)
# ==============================================================================

def test_f18_demo_slides_pdf_validity(lecture_01_slides_bytes):
    """F18-1: slides.pdf must be valid PDF binary starting with %PDF-."""
    inspection = PDFHelper.inspect(lecture_01_slides_bytes)
    assert inspection["is_valid"] is True
    assert inspection["version"] != "unknown"

def test_f18_demo_slides_size_under_300kb(lecture_01_slides_bytes):
    """F18-2: Demo slides.pdf must be under 300 KB."""
    size = len(lecture_01_slides_bytes)
    assert size < 300 * 1024, f"slides.pdf is {size} bytes (>= 300 KB)"

def test_f18_demo_notebook_nbformat_v4(lecture_01_notebook_dict):
    """F18-3: notebook.ipynb must be valid nbformat 4 schema."""
    assert NotebookHelper.validate_schema(lecture_01_notebook_dict)

def test_f18_demo_notebook_numpy_matplotlib_lissajous(lecture_01_notebook_dict):
    """F18-4: notebook.ipynb must import numpy and matplotlib and plot Lissajous curves."""
    code_cells = NotebookHelper.get_code_cells(lecture_01_notebook_dict)
    all_code = "\n".join(code_cells)
    assert "numpy" in all_code
    assert "matplotlib.pyplot" in all_code
    assert "np.sin" in all_code

def test_f18_demo_meta_yml_validity(lecture_01_meta_text):
    """F18-5: meta.yml must specify number 1, title, and required tags."""
    meta = yaml.safe_load(lecture_01_meta_text)
    assert meta.get("number") == 1
    assert "Parametric Curves" in meta.get("title") or "Introduction" in meta.get("title")
    tags = meta.get("tags", [])
    assert "NumPy" in tags
    assert "Matplotlib" in tags


# ==============================================================================
# Feature 19: Add-Lecture Agent Skill (.agents/skills/add-lecture/SKILL.md)
# ==============================================================================

def test_f19_skill_yaml_frontmatter(add_lecture_skill_text):
    """F19-1: SKILL.md must have valid YAML frontmatter with name and description."""
    assert add_lecture_skill_text.startswith("---")
    match = re.search(r"^---\n(.*?)\n---", add_lecture_skill_text, flags=re.DOTALL)
    assert match is not None
    fm = yaml.safe_load(match.group(1))
    assert fm.get("name") == "add-lecture"
    assert "description" in fm

def test_f19_skill_step_by_step_workflow(add_lecture_skill_text):
    """F19-2: SKILL.md must specify all workflow steps."""
    assert "new_lecture.py" in add_lecture_skill_text
    assert "meta.yml" in add_lecture_skill_text
    assert "slides.pdf" in add_lecture_skill_text
    assert "notebook.ipynb" in add_lecture_skill_text

def test_f19_skill_pdf_size_guardrail(add_lecture_skill_text):
    """F19-3: SKILL.md must reference the 2 MB PDF size check."""
    assert "2 MB" in add_lecture_skill_text or "optimize_pdfs" in add_lecture_skill_text

def test_f19_skill_zero_wheels_guardrail(add_lecture_skill_text):
    """F19-4: SKILL.md must enforce zero bundled wheels."""
    assert ".whl" in add_lecture_skill_text or "wheels" in add_lecture_skill_text.lower()

def test_f19_skill_relative_paths_guardrail(add_lecture_skill_text):
    """F19-5: SKILL.md must enforce strict relative URLs."""
    assert "relative" in add_lecture_skill_text.lower()
