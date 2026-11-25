"""
tests/conftest.py - Global Pytest Fixtures and Opaque-Box Test Helpers
for University Lecture Portal E2E Testing Track.
"""
import os
import re
import json
import struct
import shutil
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import pytest

# Workspace roots
WORKSPACE_ROOT = Path(os.environ.get("PORTAL_ROOT", r"e:\Active Website\Lecture website")).resolve()
TESTS_DIR = (Path(__file__).resolve().parent)
FIXTURES_DIR = TESTS_DIR / "fixtures"

# ==============================================================================
# Helper Utility Functions for Loading Workspace vs Canonical Fixtures
# ==============================================================================

def resolve_file(relative_path: str) -> Path:
    """Returns workspace file if exists, else canonical test fixture."""
    ws_file = WORKSPACE_ROOT / relative_path
    if ws_file.is_file():
        return ws_file
    fix_file = FIXTURES_DIR / relative_path
    if fix_file.is_file():
        return fix_file
    return ws_file

def get_text_content(relative_path: str) -> str:
    """Reads text content from workspace file or fallback fixture."""
    path = resolve_file(relative_path)
    if not path.exists():
        raise FileNotFoundError(f"Resource not found in workspace or fixtures: {relative_path}")
    return path.read_text(encoding="utf-8")

def get_binary_content(relative_path: str) -> bytes:
    """Reads binary bytes from workspace file or fallback fixture."""
    path = resolve_file(relative_path)
    if not path.exists():
        raise FileNotFoundError(f"Resource not found in workspace or fixtures: {relative_path}")
    return path.read_bytes()

# ==============================================================================
# Domain Test Helpers
# ==============================================================================

class SimpleDOMElement:
    """Lightweight representation of an HTML tag for assertion queries."""
    def __init__(self, tag: str, attrs: Dict[str, str], text: str = ""):
        self.tag = tag
        self.attrs = attrs
        self.text = text
        self.children: List['SimpleDOMElement'] = []

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self.attrs.get(key, default)

    @property
    def id(self) -> Optional[str]:
        return self.attrs.get("id")

    @property
    def classes(self) -> List[str]:
        return self.attrs.get("class", "").split()

    def has_class(self, cls: str) -> bool:
        return cls in self.classes


class HTMLHelper(HTMLParser):
    """Stdlib HTML Parser that parses HTML/QMD markup into an element tree."""
    def __init__(self):
        super().__init__()
        self.elements: List[SimpleDOMElement] = []
        self._stack: List[SimpleDOMElement] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]):
        attr_dict = {k: (v if v is not None else "") for k, v in attrs}
        elem = SimpleDOMElement(tag, attr_dict)
        if self._stack:
            self._stack[-1].children.append(elem)
        else:
            self.elements.append(elem)
        # Void elements do not expect an end tag
        if tag not in ("img", "input", "meta", "link", "br", "hr", "source"):
            self._stack.append(elem)

    def handle_endtag(self, tag: str):
        if self._stack and self._stack[-1].tag == tag:
            self._stack.pop()

    def handle_data(self, data: str):
        if self._stack:
            self._stack[-1].text += data

    @classmethod
    def parse(cls, html_content: str) -> 'HTMLHelper':
        # Strip frontmatter if present in .qmd files
        clean_html = re.sub(r"^---\n.*?\n---\n", "", html_content, flags=re.DOTALL)
        parser = cls()
        parser.feed(clean_html)
        return parser

    def find_by_id(self, elem_id: str) -> Optional[SimpleDOMElement]:
        def _search(nodes):
            for n in nodes:
                if n.id == elem_id:
                    return n
                sub = _search(n.children)
                if sub:
                    return sub
            return None
        return _search(self.elements)

    def find_all_by_class(self, class_name: str) -> List[SimpleDOMElement]:
        matches = []
        def _search(nodes):
            for n in nodes:
                if n.has_class(class_name):
                    matches.append(n)
                _search(n.children)
        _search(self.elements)
        return matches

    def find_all_by_tag(self, tag_name: str) -> List[SimpleDOMElement]:
        matches = []
        def _search(nodes):
            for n in nodes:
                if n.tag == tag_name:
                    matches.append(n)
                _search(n.children)
        _search(self.elements)
        return matches


class CSSHelper:
    """Helper to inspect CSS custom properties, rule blocks, and media queries."""
    def __init__(self, css_text: str):
        self.raw_css = css_text
        self.custom_properties = self._extract_custom_properties()

    def _extract_custom_properties(self) -> Dict[str, str]:
        props = {}
        matches = re.findall(r"(--[a-zA-Z0-9_-]+)\s*:\s*([^;]+);", self.raw_css)
        for name, value in matches:
            k = name.strip()
            if k not in props:
                props[k] = value.strip()
        return props

    def get_var(self, var_name: str) -> Optional[str]:
        return self.custom_properties.get(var_name)

    def has_rule(self, selector_pattern: str) -> bool:
        return bool(re.search(selector_pattern, self.raw_css))

    def extract_media_queries(self) -> List[Tuple[str, str]]:
        """Extracts @media query condition and inner block."""
        return re.findall(r"@media\s*([^{]+)\{([^}]+(?:\{[^}]*\}[^}]*)*)\}", self.raw_css, flags=re.DOTALL)

    def extract_dark_theme_properties(self) -> Dict[str, str]:
        dark_match = re.search(r'\[data-theme=["\']?dark["\']?\]\s*\{([^}]+)\}', self.raw_css)
        if not dark_match:
            return {}
        block = dark_match.group(1)
        matches = re.findall(r"(--[a-zA-Z0-9_-]+)\s*:\s*([^;]+);", block)
        return {k.strip(): v.strip() for k, v in matches}


class JSHelper:
    """Helper to verify JavaScript syntax, functions, storage keys, and event listeners."""
    def __init__(self, js_text: str):
        self.raw_js = js_text

    def has_function(self, func_name: str) -> bool:
        patterns = [
            rf"function\s+{func_name}\s*\(",
            rf"const\s+{func_name}\s*=\s*(?:function|\()",
            rf"let\s+{func_name}\s*=\s*(?:function|\()",
            rf"var\s+{func_name}\s*=\s*(?:function|\()",
            rf"{func_name}\s*:\s*function"
        ]
        return any(re.search(pat, self.raw_js) for pat in patterns)

    def uses_local_storage_key(self, key_name: str) -> bool:
        return bool(re.search(rf'localStorage\.(?:getItem|setItem)\([\'"]{key_name}[\'"]', self.raw_js))

    def uses_session_storage_key(self, key_name: str) -> bool:
        return bool(re.search(rf'sessionStorage\.(?:getItem|setItem)\([\'"]{key_name}[\'"]', self.raw_js))

    def listens_to_event(self, event_name: str) -> bool:
        return bool(re.search(rf'addEventListener\([\'"]{event_name}[\'"]', self.raw_js))

    def manipulates_class(self, class_name: str) -> bool:
        return bool(re.search(rf'classList\.(?:add|remove|toggle)\([\'"]{class_name}[\'"]', self.raw_js)) or class_name in self.raw_js


class CaddyfileHelper:
    """Helper to parse Caddyfile site blocks, directives, and headers."""
    def __init__(self, content: str):
        self.raw = content
        self.lines = [line.strip() for line in content.splitlines() if line.strip() and not line.strip().startswith("#")]

    def has_directive(self, directive_name: str) -> bool:
        return any(re.match(rf"^{directive_name}\b", line) for line in self.lines)

    def get_headers(self) -> Dict[str, str]:
        headers = {}
        matches = re.findall(r'header\s+@?[\w_-]*\s*\{([^}]+)\}', self.raw)
        # Also direct headers
        direct_headers = re.findall(r'header\s+([\w-]+)\s+"([^"]+)"', self.raw)
        for h, v in direct_headers:
            headers[h] = v
        for block in matches:
            for line in block.splitlines():
                parts = line.strip().split(None, 1)
                if len(parts) == 2:
                    val = parts[1].strip('"').strip("'")
                    headers[parts[0]] = val
        return headers

    def has_matcher(self, matcher_name: str) -> bool:
        return f"@{matcher_name}" in self.raw


class NotebookHelper:
    """Helper to validate Jupyter notebook JSON schema and content structure."""
    @staticmethod
    def load(content_or_dict: Any) -> Dict[str, Any]:
        if isinstance(content_or_dict, dict):
            return content_or_dict
        return json.loads(content_or_dict)

    @classmethod
    def validate_schema(cls, nb_data: Dict[str, Any]) -> bool:
        assert "cells" in nb_data, "Missing 'cells' key in notebook JSON"
        assert "metadata" in nb_data, "Missing 'metadata' key in notebook JSON"
        assert nb_data.get("nbformat") in (4, "4"), f"Expected nbformat 4, got {nb_data.get('nbformat')}"
        for idx, cell in enumerate(nb_data["cells"]):
            assert "cell_type" in cell, f"Cell {idx} missing 'cell_type'"
            assert "source" in cell, f"Cell {idx} missing 'source'"
            assert cell["cell_type"] in ("code", "markdown", "raw"), f"Invalid cell_type in cell {idx}"
        return True

    @classmethod
    def get_code_cells(cls, nb_data: Dict[str, Any]) -> List[str]:
        code_cells = []
        for cell in nb_data.get("cells", []):
            if cell.get("cell_type") == "code":
                src = cell.get("source", [])
                code_cells.append("".join(src) if isinstance(src, list) else src)
        return code_cells


class PDFHelper:
    """Helper to inspect binary PDF headers, trailer markers, and page counts."""
    @staticmethod
    def inspect(pdf_bytes: bytes) -> Dict[str, Any]:
        assert len(pdf_bytes) >= 10, "PDF byte stream is too short"
        assert pdf_bytes.startswith(b"%PDF-"), f"Invalid PDF magic number: {pdf_bytes[:5]}"
        version_match = re.search(rb"%PDF-(\d+\.\d+)", pdf_bytes[:20])
        version = version_match.group(1).decode("ascii") if version_match else "unknown"

        # Check for standard EOF marker
        has_eof = b"%%EOF" in pdf_bytes[-1024:]

        # Count page objects roughly via regex
        page_matches = re.findall(rb"/Type\s*/Page\b", pdf_bytes)
        page_count = len(page_matches)

        return {
            "version": version,
            "has_eof": has_eof,
            "size_bytes": len(pdf_bytes),
            "estimated_pages": page_count,
            "is_valid": has_eof and version != "unknown"
        }

# ==============================================================================
# Pytest Fixtures
# ==============================================================================

@pytest.fixture(scope="session")
def workspace_path() -> Path:
    return WORKSPACE_ROOT

@pytest.fixture(scope="session")
def fixtures_path() -> Path:
    return FIXTURES_DIR

@pytest.fixture
def quarto_yml_text() -> str:
    return get_text_content("_quarto.yml")

@pytest.fixture
def caddyfile_text() -> str:
    return get_text_content("Caddyfile")

@pytest.fixture
def env_example_text() -> str:
    return get_text_content(".env.example")

@pytest.fixture
def styles_css_text() -> str:
    return get_text_content("assets/styles.css")

@pytest.fixture
def workspace_js_text() -> str:
    return get_text_content("assets/workspace.js")

@pytest.fixture
def head_html_text() -> str:
    return get_text_content("assets/head.html")

@pytest.fixture
def index_qmd_text() -> str:
    return get_text_content("index.qmd")

@pytest.fixture
def lecture_01_meta_text() -> str:
    return get_text_content("lectures/01-intro-example/meta.yml")

@pytest.fixture
def lecture_01_index_text() -> str:
    return get_text_content("lectures/01-intro-example/index.qmd")

@pytest.fixture
def lecture_01_notebook_dict() -> Dict[str, Any]:
    return NotebookHelper.load(get_text_content("lectures/01-intro-example/notebook.ipynb"))

@pytest.fixture
def lecture_01_slides_bytes() -> bytes:
    return get_binary_content("lectures/01-intro-example/slides.pdf")

@pytest.fixture
def deploy_md_text() -> str:
    return get_text_content("DEPLOY.md")

@pytest.fixture
def makefile_text() -> str:
    return get_text_content("Makefile")

@pytest.fixture
def make_ps1_text() -> str:
    return get_text_content("make.ps1")

@pytest.fixture
def add_lecture_skill_text() -> str:
    return get_text_content(".agents/skills/add-lecture/SKILL.md")

@pytest.fixture
def new_lecture_script_path() -> Path:
    return resolve_file("scripts/new_lecture.py")

@pytest.fixture
def optimize_pdfs_script_path() -> Path:
    return resolve_file("scripts/optimize_pdfs.py")

@pytest.fixture
def build_portal_script_path() -> Path:
    return resolve_file("scripts/build_portal.py")

@pytest.fixture
def hash_password_script_path() -> Path:
    return resolve_file("scripts/hash_password.py")

@pytest.fixture
def site_dir(workspace_path) -> Optional[Path]:
    site = workspace_path / "_site"
    return site if site.is_dir() else None
