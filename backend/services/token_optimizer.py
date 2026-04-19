"""
Token Optimizer Layer for LLM context management.
Reduces token bloat before sending code payloads to Claude.

Techniques:
  1. AST-aware comment & docstring stripping (Python files).
  2. Import deduplication.
  3. Blank-line consolidation & right-strip (all languages).
  4. Semantic file ordering (entry-points → core logic → helpers → tests).
  5. Hard token-budget gating with graceful truncation.
"""

from __future__ import annotations

import ast
import json
import re
import textwrap
from typing import Any, Dict, List, Optional


# Rough estimation: 4 chars ≈ 1 token (OpenAI / Groq tokenizers average)
CHARS_PER_TOKEN = 4

# File extensions we can AST-parse for deeper optimisation
_PYTHON_EXTS = {".py"}


# ════════════════════════════════════════════════════════════════════════════
# Low-level text helpers
# ════════════════════════════════════════════════════════════════════════════

def minify_code(content: str) -> str:
    """Removes redundant blank lines and right-strips to reduce token count."""
    if not content:
        return ""
    # Consolidate multiple blank lines into a single one
    content = re.sub(r'\n\s*\n', '\n', content)
    # Right strip every line
    content = '\n'.join(line.rstrip() for line in content.splitlines())
    return content


def _estimate_tokens(text: str) -> int:
    """Rough token count from character length."""
    return len(text) // CHARS_PER_TOKEN


# ════════════════════════════════════════════════════════════════════════════
# AST-aware Python compression
# ════════════════════════════════════════════════════════════════════════════

class _DocstringStripper(ast.NodeTransformer):
    """Remove docstrings from functions, classes, and the module level."""

    def _strip_docstring(self, node: ast.AST) -> ast.AST:
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, (ast.Constant, ast.Str))
        ):
            node.body = node.body[1:] or [ast.Pass()]
        return node

    def visit_Module(self, node: ast.Module) -> ast.Module:
        self.generic_visit(node)
        return self._strip_docstring(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        self.generic_visit(node)
        return self._strip_docstring(node)

    visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        self.generic_visit(node)
        return self._strip_docstring(node)


def _strip_comments(source: str) -> str:
    """Remove single-line comments while preserving shebangs and encodings."""
    lines: list[str] = []
    for line in source.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#"):
            # Keep shebangs (#!) and encoding declarations
            if stripped.startswith("#!") or "coding" in stripped[:30]:
                lines.append(line)
            # Drop everything else
            continue
        # Inline trailing comments: split on ' #' outside strings (rough)
        # Only strip if '#' is preceded by whitespace (avoid colour codes etc.)
        idx = line.find("  #")
        if idx > 0:
            before = line[:idx].rstrip()
            if before:
                lines.append(before)
                continue
        lines.append(line)
    return "\n".join(lines)


def _deduplicate_imports(source: str) -> str:
    """Remove duplicate import lines (exact match)."""
    seen: set[str] = set()
    lines: list[str] = []
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith(("import ", "from ")):
            if stripped in seen:
                continue
            seen.add(stripped)
        lines.append(line)
    return "\n".join(lines)


def compress_python(source: str) -> str:
    """
    Best-effort AST-aware compression for Python source:
      1. Strip docstrings via AST transform.
      2. Remove comments.
      3. Deduplicate imports.
      4. Minify whitespace.
    Falls back to text-only compression if the source isn't valid Python.
    """
    compressed = source
    try:
        tree = ast.parse(source)
        tree = _DocstringStripper().visit(tree)
        ast.fix_missing_locations(tree)
        compressed = ast.unparse(tree)
    except SyntaxError:
        # Not valid Python — fall back to text-level stripping
        compressed = _strip_comments(source)

    compressed = _deduplicate_imports(compressed)
    compressed = minify_code(compressed)
    return compressed


def compress_generic(source: str) -> str:
    """Text-level compression for non-Python files."""
    source = _strip_comments(source)
    source = minify_code(source)
    return source


def compress_file(content: str, path: str) -> str:
    """Auto-select compression strategy based on file extension."""
    ext = "." + path.rsplit(".", 1)[-1].lower() if "." in path else ""
    if ext in _PYTHON_EXTS:
        return compress_python(content)
    return compress_generic(content)


# ════════════════════════════════════════════════════════════════════════════
# Semantic file ranking
# ════════════════════════════════════════════════════════════════════════════

_ENTRY_POINT_NAMES = {
    "main.py", "app.py", "server.py", "manage.py", "wsgi.py", "asgi.py",
    "index.py", "index.js", "index.ts", "main.js", "main.ts", "server.js",
    "server.ts", "app.js", "app.ts",
}

_TEST_INDICATORS = {"test_", "_test.", ".test.", "tests/", "test/", "spec/", "__tests__/"}

_CONFIG_INDICATORS = {
    "setup.py", "setup.cfg", "pyproject.toml", "package.json",
    "tsconfig.json", "webpack.config", ".eslintrc", "Makefile",
    "Dockerfile", "docker-compose",
}


def _semantic_sort_key(f: Dict[str, Any]) -> tuple:
    """
    Returns a sort key tuple for ordering files by review importance:
      (is_not_entry_point, is_test, is_config, -line_count)
    Lower tuple values = higher priority.
    """
    path = (f.get("path") or "").replace("\\", "/").lower()
    basename = path.split("/")[-1] if "/" in path else path

    is_entry_point = f.get("is_entry_point", False) or basename in _ENTRY_POINT_NAMES
    is_test = f.get("is_test", False) or any(ind in path for ind in _TEST_INDICATORS)
    is_config = any(ind in basename for ind in _CONFIG_INDICATORS)

    return (
        not is_entry_point,  # entry points first
        is_test,              # tests last
        is_config,            # config files after functional code
        -f.get("line_count", 0),  # larger files first (more logic to review)
    )


# ════════════════════════════════════════════════════════════════════════════
# Public API — payload optimizers
# ════════════════════════════════════════════════════════════════════════════

def optimize_code_review_payload(
    files: List[Dict[str, Any]],
    max_tokens: int = 50000,
) -> List[Dict[str, Any]]:
    """
    Selects and compresses files to fit within a strict token budget.
    Uses AST-aware compression for Python files and text compression for others.
    Files are prioritized by semantic importance.
    """
    max_chars = max_tokens * CHARS_PER_TOKEN
    current_chars = 0
    optimized_files: list[Dict[str, Any]] = []

    sorted_files = sorted(files, key=_semantic_sort_key)

    for f in sorted_files:
        original_content = f.get("content", "")
        if not original_content or not original_content.strip():
            continue

        path = f.get("path", "unknown")
        compressed = compress_file(original_content, path)
        file_chars = len(compressed)

        if current_chars + file_chars > max_chars:
            # Fit a truncated version if there's enough room
            allowed_chars = max_chars - current_chars
            if allowed_chars > 500:
                truncated = compressed[:allowed_chars] + "\n... [truncated by token optimizer]"
                new_f = dict(f)
                new_f["content"] = truncated
                optimized_files.append(new_f)
            break

        new_f = dict(f)
        new_f["content"] = compressed
        optimized_files.append(new_f)
        current_chars += file_chars

    return optimized_files


def optimize_architecture_graph(
    graph_data: Dict[str, Any],
    max_tokens: int = 15000,
) -> str:
    """
    Minifies and limits the size of the architecture graph representation.
    """
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])

    # Strip whitespace with separators
    graph_json = json.dumps({"nodes": nodes, "edges": edges}, separators=(',', ':'))

    max_chars = max_tokens * CHARS_PER_TOKEN
    if len(graph_json) > max_chars:
        graph_json = graph_json[:max_chars] + '... [truncated by token optimizer]"}'

    return graph_json


# ════════════════════════════════════════════════════════════════════════════
# Utility: measure compression ratio (for logging / testing)
# ════════════════════════════════════════════════════════════════════════════

def compression_stats(original: str, compressed: str) -> Dict[str, Any]:
    """Return a dict with original/compressed sizes and reduction percentage."""
    orig_tokens = _estimate_tokens(original)
    comp_tokens = _estimate_tokens(compressed)
    reduction = (1 - comp_tokens / max(1, orig_tokens)) * 100
    return {
        "original_chars": len(original),
        "compressed_chars": len(compressed),
        "original_tokens_est": orig_tokens,
        "compressed_tokens_est": comp_tokens,
        "reduction_pct": round(reduction, 1),
    }
