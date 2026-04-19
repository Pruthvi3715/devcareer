"""
Architecture Mapper — Layer 3 (PS3 Feature)
PRD Section 4.1: Dependency map, call graph, entry points, high-impact files.
Uses networkx + AST/regex to build dependency graphs from Python + JS/TS imports.
"""
import ast
import os
import re
from typing import Dict, Any, List
import networkx as nx


def _norm_path(p: str) -> str:
    """Single canonical form for graph ids (forward slashes) so edges, NLQ, and UI stay aligned."""
    return (p or "").replace("\\", "/")


def build_architecture_graph(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Builds a networkx dependency graph from the parsed repo.
    Returns serialized graph data matching PRD RepoArchGraph schema.
    """
    graph = nx.DiGraph()

    python_files = [f for f in parsed_data["files"] if f["language"] == "Python"]
    js_ts_files = [
        f for f in parsed_data["files"]
        if f["language"] in {"JavaScript", "TypeScript", "React JSX", "React TSX"}
    ]

    if python_files:
        _build_python_graph(graph, python_files)
    if js_ts_files:
        _build_js_ts_graph(graph, js_ts_files)

    # Compute centrality metrics
    in_degree = dict(graph.in_degree())
    out_degree = dict(graph.out_degree())

    try:
        betweenness = nx.betweenness_centrality(graph)
    except Exception:
        betweenness = {n: 0 for n in graph.nodes}

    # High-impact files: highest in-degree centrality (most imported)
    high_impact = sorted(in_degree.items(), key=lambda x: x[1], reverse=True)[:5]
    high_impact_files = [{"file": _norm_path(f), "in_degree": d} for f, d in high_impact if d > 0]
    high_impact_paths = {h["file"] for h in high_impact_files}

    # Orphaned modules: no in-edges AND no out-edges
    orphaned = [n for n in graph.nodes if in_degree.get(n, 0) == 0 and out_degree.get(n, 0) == 0
                and not graph.nodes[n].get("is_entry_point") and not graph.nodes[n].get("is_test")]

    # Entry points
    entry_points = [n for n in graph.nodes if graph.nodes[n].get("is_entry_point")]

    # Serialize graph for JSON (ids normalized; labels + types for UI / React Flow)
    nodes = []
    for n, data in graph.nodes(data=True):
        nid = _norm_path(n)
        entry = bool(data.get("is_entry_point", False))
        in_d = in_degree.get(n, 0)
        nodes.append({
            "id": nid,
            "label": os.path.basename(nid) or nid,
            "in_degree": in_d,
            "out_degree": out_degree.get(n, 0),
            "betweenness": round(betweenness.get(n, 0), 4),
            "is_entry_point": entry,
            "is_orphaned": n in orphaned,
            "line_count": data.get("line_count", 0),
            # Frontend reads `type` / `change_risk` for node styling
            "type": "entry_point" if entry else "module",
            "change_risk": "HIGH" if nid in high_impact_paths else "LOW",
        })

    edges = []
    for u, v, data in graph.edges(data=True):
        edges.append({
            "source": _norm_path(u),
            "target": _norm_path(v),
            "import_name": data.get("import_name", ""),
        })

    return {
        "nodes": nodes,
        "edges": edges,
        "high_impact_files": high_impact_files,
        "orphaned_modules": orphaned,
        "entry_points": entry_points,
        "stats": {
            "total_nodes": graph.number_of_nodes(),
            "total_edges": graph.number_of_edges(),
            "orphaned_count": len(orphaned),
        },
    }


def _build_python_graph(graph: nx.DiGraph, python_files: List[Dict[str, Any]]) -> None:
    # Map module paths for internal import resolution (canonical / paths)
    module_map: Dict[str, str] = {}
    for f in python_files:
        path = _norm_path(f["path"])
        # Convert file path to module-style name: src/utils/helpers.py → src.utils.helpers
        mod_name = path.replace("/", ".").removesuffix(".py")
        module_map[mod_name] = path
        short = mod_name.split(".")[-1]
        module_map.setdefault(short, path)

    # Add nodes
    for f in python_files:
        path = _norm_path(f["path"])
        graph.add_node(
            path,
            language=f["language"],
            line_count=f["line_count"],
            is_entry_point=f["is_entry_point"],
            is_test=f["is_test"],
        )

    # Parse imports to build edges
    for f in python_files:
        path = _norm_path(f["path"])
        try:
            tree = ast.parse(f["content"])
        except SyntaxError:
            continue

        imports = _extract_imports(tree)
        for imp in imports:
            target = _resolve_import(imp, module_map)
            if target:
                target = _norm_path(target)
            if target and target != path:
                graph.add_edge(path, target, import_name=imp)


def _build_js_ts_graph(graph: nx.DiGraph, files: List[Dict[str, Any]]) -> None:
    """
    Best-effort JS/TS dependency graph.

    We only resolve *relative* imports (./, ../) to files that exist in the parsed set.
    This is intentionally lightweight (no bundler config, no tsconfig path aliases).
    """
    path_set = {f["path"].replace("\\", "/") for f in files}

    # Map extensionless candidates to existing files
    def resolve_relative(source_path: str, spec: str) -> str | None:
        if not (spec.startswith("./") or spec.startswith("../")):
            return None

        src_dir = os.path.dirname(source_path).replace("\\", "/")
        joined = os.path.normpath(os.path.join(src_dir, spec)).replace("\\", "/")

        candidates = [
            joined,
            f"{joined}.ts",
            f"{joined}.tsx",
            f"{joined}.js",
            f"{joined}.jsx",
            f"{joined}.mjs",
            f"{joined}.cjs",
            f"{joined}/index.ts",
            f"{joined}/index.tsx",
            f"{joined}/index.js",
            f"{joined}/index.jsx",
        ]
        for c in candidates:
            if c in path_set:
                return c
        return None

    # Add nodes
    for f in files:
        p = f["path"].replace("\\", "/")
        graph.add_node(
            p,
            language=f["language"],
            line_count=f["line_count"],
            is_entry_point=f["is_entry_point"],
            is_test=f["is_test"],
        )

    # Build edges via regex import extraction
    for f in files:
        p = f["path"].replace("\\", "/")
        imports = _extract_js_ts_imports(f["content"])
        for spec in imports:
            target = resolve_relative(p, spec)
            if target and target != p:
                graph.add_edge(p, target, import_name=spec)


def _extract_imports(tree: ast.AST) -> List[str]:
    """Extract all import names from an AST."""
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports


_JS_IMPORT_RE = re.compile(
    r"""(?mx)
    ^\s*import\s+(?:type\s+)?(?:[\w*\s{},]+\s+from\s+)?["'](?P<spec>[^"']+)["']\s*;?\s*$
    |^\s*export\s+.*\s+from\s+["'](?P<spec2>[^"']+)["']\s*;?\s*$
    |^\s*const\s+\w+\s*=\s*require\(\s*["'](?P<spec3>[^"']+)["']\s*\)\s*;?\s*$
    |^\s*require\(\s*["'](?P<spec4>[^"']+)["']\s*\)\s*;?\s*$
    """
)


def _extract_js_ts_imports(content: str) -> List[str]:
    specs: List[str] = []
    for m in _JS_IMPORT_RE.finditer(content):
        spec = m.group("spec") or m.group("spec2") or m.group("spec3") or m.group("spec4")
        if spec:
            specs.append(spec)
    return specs


def _resolve_import(import_name: str, module_map: Dict[str, str]) -> str | None:
    """Try to resolve an import name to a file path in the repo."""
    # Direct match
    if import_name in module_map:
        return module_map[import_name]

    # Try last segment
    parts = import_name.split(".")
    for i in range(len(parts)):
        candidate = ".".join(parts[i:])
        if candidate in module_map:
            return module_map[candidate]

    return None
