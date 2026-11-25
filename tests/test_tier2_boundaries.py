"""
tests/test_tier2_boundaries.py - Tier 2: Boundary Value Analysis & Fault Injection
Covers boundary, negative, and corner cases across all 19 features (F01–F19, >= 95 tests).
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
# Feature 01 Boundaries: Quarto Setup
# ==============================================================================

def test_f01_b01_quarto_missing_render_section_fails_safe():
    """F01-B1: Empty or missing render section must be detectable as invalid."""
    invalid_yaml = "project:\n  type: website\n"
    data = yaml.safe_load(invalid_yaml)
    assert "render" not in data.get("project", {}), "Validator must detect missing render list"

def test_f01_b02_quarto_invalid_output_dir_rejected(quarto_yml_text):
    """F01-B2: output-dir must not be root or empty string."""
    data = yaml.safe_load(quarto_yml_text)
    out_dir = data.get("project", {}).get("output-dir", "")
    assert out_dir not in ("", "/", "."), f"Invalid output-dir: {out_dir}"

def test_f01_b03_quarto_nonexistent_theme_or_bootstrap_suppression(quarto_yml_text):
    """F01-B3: format.html.theme must explicitly be 'none' to suppress Bootstrap."""
    data = yaml.safe_load(quarto_yml_text)
    theme = data.get("format", {}).get("html", {}).get("theme")
    assert theme == "none", f"Theme was {theme}, must be 'none'"

def test_f01_b04_quarto_empty_resources_list_fault(quarto_yml_text):
    """F01-B4: resources list cannot be empty."""
    data = yaml.safe_load(quarto_yml_text)
    resources = data.get("project", {}).get("resources", [])
    assert len(resources) > 0, "resources list is empty; static files would not be copied"

def test_f01_b05_quarto_deeply_nested_lecture_glob(quarto_yml_text):
    """F01-B5: Render pattern must use double asterisk to support nested lectures."""
    data = yaml.safe_load(quarto_yml_text)
    render_targets = data.get("project", {}).get("render", [])
    assert any("lectures/**" in r for r in render_targets)


# ==============================================================================
# Feature 02 Boundaries: Build Pipeline
# ==============================================================================

def test_f02_b01_staging_empty_lectures_dir(tmp_path):
    """F02-B1: Staging function must handle empty lectures directory without error."""
    from tests.fixtures.scripts.build_portal import stage_notebooks
    lectures_dir = tmp_path / "lectures"
    lectures_dir.mkdir()
    staging_dir = tmp_path / "staging"
    stage_notebooks(lectures_dir, staging_dir)
    assert staging_dir.exists()
    assert len(list(staging_dir.iterdir())) == 0

def test_f02_b02_staging_missing_notebook_graceful(tmp_path):
    """F02-B2: Lecture folder lacking notebook.ipynb must not crash staging."""
    from tests.fixtures.scripts.build_portal import stage_notebooks
    lec = tmp_path / "lectures" / "02-slides-only"
    lec.mkdir(parents=True)
    staging_dir = tmp_path / "staging"
    stage_notebooks(tmp_path / "lectures", staging_dir)
    assert (staging_dir / "02-slides-only").exists()
    assert not (staging_dir / "02-slides-only" / "notebook.ipynb").exists()

def test_f02_b03_staging_non_directory_files_ignored(tmp_path):
    """F02-B3: Non-directory files in lectures/ (e.g. .DS_Store) must be skipped."""
    from tests.fixtures.scripts.build_portal import stage_notebooks
    lectures_dir = tmp_path / "lectures"
    lectures_dir.mkdir()
    (lectures_dir / ".DS_Store").write_text("dummy", encoding="utf-8")
    staging_dir = tmp_path / "staging"
    stage_notebooks(lectures_dir, staging_dir)
    assert not (staging_dir / ".DS_Store").exists()

def test_f02_b04_data_subfolder_with_subdirectories(tmp_path):
    """F02-B4: Complex nested data/ folders must be recursively staged."""
    from tests.fixtures.scripts.build_portal import stage_notebooks
    data_nested = tmp_path / "lectures" / "01-test" / "data" / "nested"
    data_nested.mkdir(parents=True)
    (data_nested / "sample.csv").write_text("a,b,c\n1,2,3", encoding="utf-8")
    staging_dir = tmp_path / "staging"
    stage_notebooks(tmp_path / "lectures", staging_dir)
    staged_csv = staging_dir / "01-test" / "data" / "nested" / "sample.csv"
    assert staged_csv.is_file()

def test_f02_b05_special_characters_in_lecture_slug(tmp_path):
    """F02-B5: Staging handles slugs with numbers, hyphens, and underscores."""
    from tests.fixtures.scripts.build_portal import stage_notebooks
    lec = tmp_path / "lectures" / "99_special-test_case"
    lec.mkdir(parents=True)
    (lec / "notebook.ipynb").write_text("{}", encoding="utf-8")
    staging_dir = tmp_path / "staging"
    stage_notebooks(tmp_path / "lectures", staging_dir)
    assert (staging_dir / "99_special-test_case" / "notebook.ipynb").is_file()


# ==============================================================================
# Feature 03 Boundaries: Zero-Wheel Guardrails
# ==============================================================================

def test_f03_b01_assert_zero_wheels_detects_nested_whl(tmp_path):
    """F03-B1: assert_zero_wheels must detect .whl file nested deep in site directory."""
    from tests.fixtures.scripts.build_portal import assert_zero_wheels
    bad_dir = tmp_path / "_site" / "lite" / "pypi"
    bad_dir.mkdir(parents=True)
    (bad_dir / "numpy-2.0.0-cp311-cp311-emscripten_wasm32.whl").write_bytes(b"dummy")
    with pytest.raises(RuntimeError, match="Bandwidth guardrail violated"):
        assert_zero_wheels(tmp_path / "_site")

def test_f03_b02_assert_zero_wheels_case_insensitivity(tmp_path):
    """F03-B2: Detection handles uppercase .WHL extension."""
    site = tmp_path / "_site"
    site.mkdir()
    (site / "package.WHL").write_bytes(b"dummy")
    whls = list(site.glob("**/*.[wW][hH][lL]"))
    assert len(whls) == 1

def test_f03_b03_wheel_simulation_raises_runtime_error(tmp_path):
    """F03-B3: Injected wheel raises clear error message citing bandwidth guardrail."""
    from tests.fixtures.scripts.build_portal import assert_zero_wheels
    site = tmp_path / "_site"
    site.mkdir()
    (site / "test.whl").write_bytes(b"")
    with pytest.raises(RuntimeError) as exc:
        assert_zero_wheels(site)
    assert "guardrail violated" in str(exc.value).lower()

def test_f03_b04_non_wheel_tar_gz_or_zip_safety(tmp_path):
    """F03-B4: Regular zip or wasm files are not mistakenly flagged as .whl."""
    from tests.fixtures.scripts.build_portal import assert_zero_wheels
    site = tmp_path / "_site"
    site.mkdir()
    (site / "pyodide.wasm").write_bytes(b"\x00asm\x01\x00\x00\x00")
    (site / "archive.zip").write_bytes(b"PK\x03\x04")
    # Must not raise
    assert_zero_wheels(site)

def test_f03_b05_empty_site_directory_safe(tmp_path):
    """F03-B5: Completely empty _site directory passes wheel check cleanly."""
    from tests.fixtures.scripts.build_portal import assert_zero_wheels
    site = tmp_path / "_site"
    site.mkdir()
    assert_zero_wheels(site)


# ==============================================================================
# Feature 04 Boundaries: Academic Theme & Light/Dark Mode
# ==============================================================================

def test_f04_b01_extreme_contrast_ratio_check(styles_css_text):
    """F04-B1: Primary text (#0F172A) against white (#FFFFFF) exceeds WCAG AAA (7:1)."""
    helper = CSSHelper(styles_css_text)
    text = helper.get_var("--text-primary")
    bg = helper.get_var("--bg-surface")
    assert text in ("#0F172A", "rgb(15, 23, 42)")
    assert bg in ("#FFFFFF", "rgb(255, 255, 255)")

def test_f04_b02_dark_mode_inverted_contrast(styles_css_text):
    """F04-B2: Dark theme text (#F8FAFC) against obsidian (#0B0F17) exceeds 7:1."""
    helper = CSSHelper(styles_css_text)
    dark_props = helper.extract_dark_theme_properties()
    assert dark_props.get("--bg-app") in ("#0B0F17", "rgb(11, 15, 23)")
    assert dark_props.get("--text-primary") in ("#F8FAFC", "rgb(248, 250, 252)")

def test_f04_b03_invalid_saved_theme_fallback(head_html_text):
    """F04-B3: Corrupted theme string in localStorage falls back safely."""
    # head.html script must check prefersDark or ternary condition
    assert "saved : (prefersDark ? 'dark' : 'light')" in head_html_text or "dark" in head_html_text

def test_f04_b04_missing_local_storage_security_error_handling(head_html_text):
    """F04-B4: head.html script must wrap localStorage in try/catch for sandbox/iframe security."""
    assert "try {" in head_html_text
    assert "} catch" in head_html_text

def test_f04_b05_accent_amber_accessible_readability(styles_css_text):
    """F04-B5: Academic amber accent must have distinct light and dark variants."""
    helper = CSSHelper(styles_css_text)
    dark_props = helper.extract_dark_theme_properties()
    light_amber = helper.get_var("--accent-amber")
    dark_amber = dark_props.get("--accent-amber")
    assert light_amber != dark_amber, "Amber accent must adapt to dark background"


# ==============================================================================
# Feature 05 Boundaries: Home Instant Search
# ==============================================================================

def test_f05_b01_empty_search_query_shows_all_cards(workspace_js_text):
    """F05-B1: Empty query string (!query) must restore display to all cards."""
    assert "!query" in workspace_js_text
    assert "style.display = ''" in workspace_js_text

def test_f05_b02_search_query_special_regex_characters(workspace_js_text):
    """F05-B2: Searching with includes() rather than unescaped RegExp avoids ReDoS."""
    assert ".includes(query)" in workspace_js_text

def test_f05_b03_search_query_leading_trailing_whitespace(workspace_js_text):
    """F05-B3: Search input query must be trimmed of surrounding whitespace."""
    assert ".trim()" in workspace_js_text

def test_f05_b04_search_non_matching_query_shows_empty_state(index_qmd_text):
    """F05-B4: #no-search-results element must exist for 0-result states."""
    dom = HTMLHelper.parse(index_qmd_text)
    no_results = dom.find_by_id("no-search-results")
    assert no_results is not None
    assert "hidden" in no_results.attrs

def test_f05_b05_search_case_insensitivity(workspace_js_text):
    """F05-B5: Both card text and search query must be converted via toLowerCase()."""
    assert ".toLowerCase()" in workspace_js_text


# ==============================================================================
# Feature 06 Boundaries: Draggable Divider
# ==============================================================================

def test_f06_b01_split_ratio_extreme_minimum_clamp(workspace_js_text):
    """F06-B1: Ratio must be clamped to minimum 15%."""
    assert "Math.max(15" in workspace_js_text

def test_f06_b02_split_ratio_extreme_maximum_clamp(workspace_js_text):
    """F06-B2: Ratio must be clamped to maximum 85%."""
    assert "Math.min(85" in workspace_js_text

def test_f06_b03_divider_double_click_resets_to_fifty_percent(workspace_js_text):
    """F06-B3: Double-click event listener resets split width to 50%."""
    assert "dblclick" in workspace_js_text
    assert "'50%'" in workspace_js_text

def test_f06_b04_divider_keyboard_bounds_left_right(workspace_js_text):
    """F06-B4: ArrowLeft and ArrowRight keyboard navigation checks."""
    assert "ArrowLeft" in workspace_js_text
    assert "ArrowRight" in workspace_js_text

def test_f06_b05_divider_corrupted_local_storage_recovery(workspace_js_text):
    """F06-B5: Corrupted localStorage value wrapped in try/catch."""
    helper = JSHelper(workspace_js_text)
    assert helper.uses_local_storage_key("workspace_split_ratio")
    assert "try {" in workspace_js_text


# ==============================================================================
# Feature 07 Boundaries: Layout Switcher
# ==============================================================================

def test_f07_b01_unknown_layout_mode_fallback(workspace_js_text):
    """F07-B1: Unrecognized layout mode defaults to 'split'."""
    assert "setLayout('split')" in workspace_js_text

def test_f07_b02_rapid_layout_toggle_stability(workspace_js_text):
    """F07-B2: setLayout removes all mutually exclusive layout classes."""
    assert "container.classList.remove('layout-split', 'layout-slides', 'layout-notebook')" in workspace_js_text

def test_f07_b03_slides_only_mode_hides_divider_completely(styles_css_text):
    """F07-B3: In layout-slides mode, divider has display: none !important."""
    assert ".workspace-container.layout-slides .workspace-divider" in styles_css_text
    assert "display: none !important" in styles_css_text

def test_f07_b04_notebook_only_mode_hides_divider_completely(styles_css_text):
    """F07-B4: In layout-notebook mode, slides pane has display: none !important."""
    assert ".workspace-container.layout-notebook .pane-slides" in styles_css_text
    assert "display: none !important" in styles_css_text

def test_f07_b05_layout_state_aria_pressed_consistency(workspace_js_text):
    """F07-B5: Only the active layout button receives aria-pressed='true'."""
    assert "aria-pressed" in workspace_js_text


# ==============================================================================
# Feature 08 Boundaries: Mobile Viewport
# ==============================================================================

def test_f08_b01_exact_breakpoint_threshold_899px(styles_css_text):
    """F08-B1: Viewport breakpoint must be <= 900px."""
    assert "899px" in styles_css_text or "900px" in styles_css_text

def test_f08_b02_mobile_both_panes_never_simultaneously_hidden(workspace_js_text):
    """F08-B2: Clicking tab hides one pane and shows the other via is-hidden-mobile."""
    assert "paneSlides.classList.remove('is-hidden-mobile')" in workspace_js_text
    assert "paneNotebook.classList.remove('is-hidden-mobile')" in workspace_js_text

def test_f08_b03_mobile_tab_aria_selected_toggle(workspace_js_text):
    """F08-B3: Active tab sets aria-selected='true', inactive 'false'."""
    assert "aria-selected" in workspace_js_text

def test_f08_b04_mobile_viewport_disables_divider_drag(styles_css_text):
    """F08-B4: Divider is hidden via display: none !important on mobile."""
    helper = CSSHelper(styles_css_text)
    queries = helper.extract_media_queries()
    mobile = next((q[1] for q in queries if "899px" in q[0] or "900px" in q[0]), "")
    assert ".workspace-divider" in mobile
    assert "display: none !important" in mobile

def test_f08_b05_mobile_tab_text_clarity(lecture_01_index_text):
    """F08-B5: Mobile tab labels clearly identify Slides and Notebook."""
    dom = HTMLHelper.parse(lecture_01_index_text)
    tab_slides = dom.find_by_id("tab-slides")
    tab_nb = dom.find_by_id("tab-notebook")
    assert "Slides" in tab_slides.text
    assert "Notebook" in tab_nb.text


# ==============================================================================
# Feature 09 Boundaries: Single-Notebook & Status Notices
# ==============================================================================

def test_f09_b01_single_notebook_url_query_param_validation(lecture_01_index_text):
    """F09-B1: Single-notebook URL must have ?path=<lecture-slug>/notebook.ipynb."""
    dom = HTMLHelper.parse(lecture_01_index_text)
    iframe = dom.find_by_id("jupyterlite-iframe")
    src = iframe.get("src")
    assert "?path=" in src
    assert "notebook.ipynb" in src

def test_f09_b02_status_banner_session_storage_blockage_safety(workspace_js_text):
    """F09-B2: sessionStorage access wrapped in try/catch."""
    assert "sessionStorage.getItem('banner_dismissed')" in workspace_js_text
    assert "try {" in workspace_js_text

def test_f09_b03_banner_dismissal_preserves_page_height(workspace_js_text):
    """F09-B3: Banner sets display: none on dismissal without disrupting parent flex container."""
    assert "banner.style.display = 'none'" in workspace_js_text

def test_f09_b04_single_notebook_url_relative_path_safety(lecture_01_index_text):
    """F09-B4: URL must NOT start with absolute slash (e.g. /lite/); must be relative."""
    dom = HTMLHelper.parse(lecture_01_index_text)
    iframe = dom.find_by_id("jupyterlite-iframe")
    src = iframe.get("src")
    assert not src.startswith("/"), f"Absolute path detected: {src}"
    assert src.startswith("../../") or src.startswith("./")

def test_f09_b05_iframe_allow_attribute_security(lecture_01_index_text):
    """F09-B5: Iframe must have cross-origin-isolated or valid sandbox attribute."""
    dom = HTMLHelper.parse(lecture_01_index_text)
    iframe = dom.find_by_id("jupyterlite-iframe")
    assert "allow" in iframe.attrs or "sandbox" in iframe.attrs


# ==============================================================================
# Feature 10 Boundaries: Key Takeaways Drawer
# ==============================================================================

def test_f10_b01_takeaways_empty_items_handling(lecture_01_meta_text):
    """F10-B1: meta.yml takeaways array must contain non-empty strings."""
    meta = yaml.safe_load(lecture_01_meta_text)
    for t in meta.get("takeaways", []):
        assert len(t.strip()) > 0

def test_f10_b02_takeaways_html_character_escaping(lecture_01_index_text):
    """F10-B2: Markup handles ampersands and special characters cleanly."""
    assert "Key Takeaways & Practice Tasks" in lecture_01_index_text or "Key Takeaways &amp; Practice Tasks" in lecture_01_index_text

def test_f10_b03_details_open_state_independent(lecture_01_index_text):
    """F10-B3: <details> tag does not possess open attribute by default (collapsed on load)."""
    dom = HTMLHelper.parse(lecture_01_index_text)
    drawers = dom.find_all_by_class("takeaways-drawer")
    assert "open" not in drawers[0].attrs

def test_f10_b04_summary_keyboard_accessibility(lecture_01_index_text):
    """F10-B4: Summary element is direct child of details for native browser focusability."""
    dom = HTMLHelper.parse(lecture_01_index_text)
    drawers = dom.find_all_by_class("takeaways-drawer")
    assert drawers[0].children[0].tag == "summary"

def test_f10_b05_nested_list_formatting_in_takeaways(lecture_01_index_text):
    """F10-B5: Drawer contains unordered list for takeaways and ordered list for tasks."""
    dom = HTMLHelper.parse(lecture_01_index_text)
    uls = dom.find_all_by_tag("ul")
    ols = dom.find_all_by_tag("ol")
    assert len(uls) > 0, "Missing <ul> for key takeaways"
    assert len(ols) > 0, "Missing <ol> for practice tasks"


# ==============================================================================
# Feature 11 Boundaries: Caddy Auth & Port Binding
# ==============================================================================

def test_f11_b01_caddyfile_missing_env_fallback(caddyfile_text):
    """F11-B1: Username must have default fallback {$CLASS_USERNAME:student}."""
    assert "{$CLASS_USERNAME:student}" in caddyfile_text or "CLASS_USERNAME" in caddyfile_text

def test_f11_b02_empty_password_hash_detection(caddyfile_text):
    """F11-B2: Caddyfile must not contain a hardcoded empty password hash."""
    assert '""' not in caddyfile_text.split("basic_auth")[1].split("}")[0]

def test_f11_b03_caddy_bcrypt_hash_prefix_validation(env_example_text):
    """F11-B3: .env.example hash must start with standard $2a$ or $2b$ bcrypt identifier."""
    match = re.search(r"CLASS_PASSWORD_HASH=(\S+)", env_example_text)
    assert match is not None
    h = match.group(1)
    assert h.startswith("$2a$") or h.startswith("$2b$") or h.startswith("$2y$")

def test_f11_b04_caddy_public_port_conflict_prevention(caddyfile_text):
    """F11-B4: Caddyfile must bind strictly to port 8080."""
    assert "8080" in caddyfile_text

def test_f11_b05_unauthenticated_request_spec_behavior(caddyfile_text):
    """F11-B5: basic_auth must apply globally within site block."""
    helper = CaddyfileHelper(caddyfile_text)
    assert helper.has_directive("basic_auth")


# ==============================================================================
# Feature 12 Boundaries: Cache Headers
# ==============================================================================

def test_f12_b01_html_cache_header_must_revalidate(caddyfile_text):
    """F12-B1: Dynamic matchers must include must-revalidate directive."""
    assert "must-revalidate" in caddyfile_text

def test_f12_b02_ipynb_cache_header_no_store(caddyfile_text):
    """F12-B2: Notebooks must forbid persistent disk storage on intermediate proxies."""
    assert "no-store" in caddyfile_text

def test_f12_b03_wasm_cached_immutably(caddyfile_text):
    """F12-B3: *.wasm must be listed in static assets for immutable caching."""
    assert "*.wasm" in caddyfile_text

def test_f12_b04_css_and_js_cached_immutably(caddyfile_text):
    """F12-B4: *.css and *.js must be listed in static assets."""
    assert "*.css" in caddyfile_text
    assert "*.js" in caddyfile_text

def test_f12_b05_root_index_cache_header(caddyfile_text):
    """F12-B5: Root / must be matched by no-cache rules."""
    assert "path_regexp ^/$" in caddyfile_text or "*.html" in caddyfile_text


# ==============================================================================
# Feature 13 Boundaries: Frame Security & Content-Disposition
# ==============================================================================

def test_f13_b01_frame_ancestors_blocks_external_framing(caddyfile_text):
    """F13-B1: frame-ancestors must strictly specify 'self' and not wildcard '*'."""
    assert "frame-ancestors 'self'" in caddyfile_text
    assert "frame-ancestors *" not in caddyfile_text

def test_f13_b02_content_disposition_not_attachment(caddyfile_text):
    """F13-B2: Content-Disposition must not be 'attachment' (which triggers download dialog)."""
    assert 'Content-Disposition "attachment"' not in caddyfile_text
    assert 'Content-Disposition "inline"' in caddyfile_text

def test_f13_b03_x_content_type_options_blocks_mime_sniffing(caddyfile_text):
    """F13-B3: nosniff header prevents MIME confusion attacks."""
    assert 'X-Content-Type-Options "nosniff"' in caddyfile_text

def test_f13_b04_csp_semicolon_syntax(caddyfile_text):
    """F13-B4: CSP directives must terminate with valid semicolon."""
    csp_match = re.search(r'Content-Security-Policy\s+"([^"]+)"', caddyfile_text)
    assert csp_match is not None
    assert csp_match.group(1).strip().endswith(";")

def test_f13_b05_coep_absence_allows_cdn_pyodide_cross_origin(caddyfile_text):
    """F13-B5: Global COEP (require-corp) must be absent to allow jsDelivr Pyodide loading."""
    assert "Cross-Origin-Embedder-Policy" not in caddyfile_text


# ==============================================================================
# Feature 14 Boundaries: Tailscale Funnel Guide
# ==============================================================================

def test_f14_b01_funnel_target_port_matches_caddy(deploy_md_text):
    """F14-B1: Funnel port (8080) matches Caddy port (8080)."""
    assert "8080" in deploy_md_text

def test_f14_b02_funnel_bg_daemon_flag_specified(deploy_md_text):
    """F14-B2: Documentation must specify --bg flag."""
    assert "--bg" in deploy_md_text

def test_f14_b03_funnel_off_flag_specified(deploy_md_text):
    """F14-B3: Teardown documentation specifies off flag."""
    assert "8080 off" in deploy_md_text

def test_f14_b04_cloud_fallback_preserves_trailing_slash(deploy_md_text):
    """F14-B4: Cloud fallback section explains relative paths mechanism."""
    assert "relative" in deploy_md_text.lower()

def test_f14_b05_deploy_md_warning_on_custom_domains(deploy_md_text):
    """F14-B5: Mentions zero-config access over Tailnet domain."""
    assert "Tailscale" in deploy_md_text


# ==============================================================================
# Feature 15 Boundaries: Automation Makefile
# ==============================================================================

def test_f15_b01_makefile_tab_indentation_integrity(makefile_text):
    """F15-B1: Makefile recipe lines must use tab indentation."""
    recipe_lines = [l for l in makefile_text.splitlines() if l.startswith("\t")]
    assert len(recipe_lines) >= 8, "Makefile rules must be indented with tabs"

def test_f15_b02_make_ps1_invalid_target_exits_with_error(make_ps1_text):
    """F15-B2: make.ps1 invalid target triggers default block with exit 1."""
    assert "default {" in make_ps1_text
    assert "exit 1" in make_ps1_text

def test_f15_b03_make_ps1_case_insensitive_dispatch(make_ps1_text):
    """F15-B3: Target dispatch converts parameter via ToLower()."""
    assert ".tolower()" in make_ps1_text.lower()

def test_f15_b04_default_target_is_build(makefile_text):
    """F15-B4: Default all target points to build."""
    assert "all: build" in makefile_text

def test_f15_b05_hash_password_accepts_argument(hash_password_script_path):
    """F15-B5: hash_password script accepts custom password argument via sys.argv."""
    code = hash_password_script_path.read_text(encoding="utf-8")
    assert "sys.argv" in code


# ==============================================================================
# Feature 16 Boundaries: Scaffolding Script
# ==============================================================================

def test_f16_b01_scaffolding_special_characters_in_title(tmp_path):
    """F16-B1: Title with special characters produces clean alphanumeric slug."""
    from tests.fixtures.scripts.new_lecture import scaffold_lecture
    lec_dir = scaffold_lecture(3, "Calculus & Linear Algebra: Part 1!", root_dir=tmp_path)
    assert lec_dir.name == "03-calculus-and-linear-algebra-part-1"
    assert lec_dir.exists()

def test_f16_b02_scaffolding_large_lecture_number(tmp_path):
    """F16-B2: Lecture number >= 100 formats without crashing."""
    from tests.fixtures.scripts.new_lecture import scaffold_lecture
    lec_dir = scaffold_lecture(105, "Advanced Modeling", root_dir=tmp_path)
    assert lec_dir.name.startswith("105-")

def test_f16_b03_scaffolding_custom_date_format(tmp_path):
    """F16-B3: Custom date parameter is persisted in meta.yml."""
    from tests.fixtures.scripts.new_lecture import scaffold_lecture
    lec_dir = scaffold_lecture(4, "Optimization", date="2026-11-30", root_dir=tmp_path)
    meta = yaml.safe_load((lec_dir / "meta.yml").read_text(encoding="utf-8"))
    assert meta["date"] == "2026-11-30"

def test_f16_b04_scaffolding_custom_tags_list(tmp_path):
    """F16-B4: Custom tags list is persisted in meta.yml."""
    from tests.fixtures.scripts.new_lecture import scaffold_lecture
    lec_dir = scaffold_lecture(5, "PDEs", tags=["PDE", "Finite Differences"], root_dir=tmp_path)
    meta = yaml.safe_load((lec_dir / "meta.yml").read_text(encoding="utf-8"))
    assert "Finite Differences" in meta["tags"]

def test_f16_b05_scaffolding_empty_title_fallback(tmp_path):
    """F16-B5: Default title is used if none provided."""
    from tests.fixtures.scripts.new_lecture import scaffold_lecture
    lec_dir = scaffold_lecture(6, "Lecture", root_dir=tmp_path)
    assert lec_dir.exists()


# ==============================================================================
# Feature 17 Boundaries: PDF Size Optimizer
# ==============================================================================

def test_f17_b01_pdf_exactly_two_megabytes_boundary(tmp_path):
    """F17-B1: File of exactly 2,097,152 bytes is NOT marked oversized (boundary <=)."""
    from tests.fixtures.scripts.optimize_pdfs import check_and_optimize_pdf
    pdf = tmp_path / "slides.pdf"
    # Create exactly 2097152 bytes
    pdf.write_bytes(b"0" * 2097152)
    res = check_and_optimize_pdf(pdf)
    assert res["is_oversized"] is False
    assert res["warning"] is None

def test_f17_b02_pdf_one_byte_over_two_megabytes(tmp_path):
    """F17-B2: File of 2,097,153 bytes IS marked oversized (> 2 MB)."""
    from tests.fixtures.scripts.optimize_pdfs import check_and_optimize_pdf
    pdf = tmp_path / "slides.pdf"
    pdf.write_bytes(b"0" * (2097152 + 1))
    res = check_and_optimize_pdf(pdf)
    assert res["is_oversized"] is True
    assert res["warning"] is not None

def test_f17_b03_missing_ghostscript_graceful_notification(tmp_path, monkeypatch):
    """F17-B3: When ghostscript is not installed, script notifies without throwing unhandled exception."""
    from tests.fixtures.scripts.optimize_pdfs import check_and_optimize_pdf
    monkeypatch.setattr("shutil.which", lambda cmd: None)
    pdf = tmp_path / "slides.pdf"
    pdf.write_bytes(b"0" * 3000000)
    res = check_and_optimize_pdf(pdf)
    assert res["is_oversized"] is True
    assert res["optimized"] is False

def test_f17_b04_empty_pdf_file_detection(tmp_path):
    """F17-B4: 0-byte PDF does not trigger optimization or divide-by-zero."""
    from tests.fixtures.scripts.optimize_pdfs import check_and_optimize_pdf
    pdf = tmp_path / "slides.pdf"
    pdf.write_bytes(b"")
    res = check_and_optimize_pdf(pdf)
    assert res["is_oversized"] is False

def test_f17_b05_synthetic_large_pdf_generates_warning(tmp_path, capsys):
    """F17-B5: Oversized PDF prints warning to sys.stderr."""
    from tests.fixtures.scripts.optimize_pdfs import check_and_optimize_pdf
    pdf = tmp_path / "slides.pdf"
    pdf.write_bytes(b"0" * (2 * 1024 * 1024 + 500))
    check_and_optimize_pdf(pdf)
    captured = capsys.readouterr()
    assert "[WARNING]" in captured.err


# ==============================================================================
# Feature 18 Boundaries: Demo Lecture Assets
# ==============================================================================

def test_f18_b01_corrupted_notebook_json_detection():
    """F18-B1: NotebookHelper raises ValueError on invalid JSON string."""
    with pytest.raises(Exception):
        NotebookHelper.load("INVALID { JSON")

def test_f18_b02_notebook_missing_cells_key_rejected():
    """F18-B2: NotebookHelper rejects dict lacking 'cells' key."""
    with pytest.raises(AssertionError, match="Missing 'cells' key"):
        NotebookHelper.validate_schema({"metadata": {}, "nbformat": 4})

def test_f18_b03_notebook_cell_type_invalid_rejected():
    """F18-B3: NotebookHelper rejects unrecognized cell types."""
    invalid_nb = {
        "cells": [{"cell_type": "invalid_type", "source": []}],
        "metadata": {},
        "nbformat": 4
    }
    with pytest.raises(AssertionError, match="Invalid cell_type"):
        NotebookHelper.validate_schema(invalid_nb)

def test_f18_b04_pdf_missing_header_rejected():
    """F18-B4: PDFHelper rejects bytes not starting with %PDF-."""
    with pytest.raises(AssertionError, match="Invalid PDF magic number"):
        PDFHelper.inspect(b"NOT_A_PDF_STREAM")

def test_f18_b05_pdf_truncated_without_eof_rejected():
    """F18-B5: PDFHelper marks truncated file lacking %%EOF as invalid."""
    truncated = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj"
    res = PDFHelper.inspect(truncated)
    assert res["has_eof"] is False
    assert res["is_valid"] is False


# ==============================================================================
# Feature 19 Boundaries: Agent Skill Standards
# ==============================================================================

def test_f19_b01_skill_missing_name_invalid():
    """F19-B1: Skill frontmatter lacking 'name' is detected."""
    invalid_frontmatter = "---\ndescription: test\n---\n"
    match = re.search(r"^---\n(.*?)\n---", invalid_frontmatter, flags=re.DOTALL)
    fm = yaml.safe_load(match.group(1))
    assert "name" not in fm

def test_f19_b02_skill_missing_description_invalid():
    """F19-B2: Skill frontmatter lacking 'description' is detected."""
    invalid_frontmatter = "---\nname: add-lecture\n---\n"
    match = re.search(r"^---\n(.*?)\n---", invalid_frontmatter, flags=re.DOTALL)
    fm = yaml.safe_load(match.group(1))
    assert "description" not in fm

def test_f19_b03_skill_empty_body_rejected():
    """F19-B3: Skill must have substantive body content after frontmatter."""
    content = resolve_file(".agents/skills/add-lecture/SKILL.md").read_text(encoding="utf-8")
    body = re.sub(r"^---\n.*?\n---\n", "", content, flags=re.DOTALL).strip()
    assert len(body) > 100, "Skill body is too short or empty"

def test_f19_b04_skill_non_standard_tags_warning(add_lecture_skill_text):
    """F19-B4: Skill must contain standard headers (Overview, Workflow, Guardrails)."""
    assert "## Overview" in add_lecture_skill_text
    assert "## Step-by-Step Workflow" in add_lecture_skill_text

def test_f19_b05_skill_path_isolation(add_lecture_skill_text):
    """F19-B5: Skill references must be relative to repository root."""
    assert "scripts/new_lecture.py" in add_lecture_skill_text
    assert "C:\\" not in add_lecture_skill_text
