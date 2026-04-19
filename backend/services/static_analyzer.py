"""
Static Code Analysis — Layer 3
PRD Section 4.1: Cyclomatic complexity, naming conventions, function length,
modularity score per file. Also: test coverage estimation + documentation completeness.
Uses radon for complexity, AST for everything else.
"""
import ast
import math
from typing import Dict, Any, List
from radon.complexity import cc_visit
from radon.metrics import mi_visit


def analyze_repo(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Runs static analysis on all Python files in the parsed repo data.
    Returns per-file metrics + aggregated repo-level metrics.
    """
    file_metrics: List[Dict[str, Any]] = []
    total_complexity = 0
    total_functions = 0
    naming_violations = 0
    total_doc_score = 0
    files_analyzed = 0

    python_files = [f for f in parsed_data["files"] if f["language"] == "Python" and not f["is_test"]]

    for file_data in python_files:
        content = file_data["content"]
        path = file_data["path"]

        metrics = _analyze_single_file(content, path)
        file_metrics.append(metrics)

        total_complexity += metrics["avg_complexity"]
        total_functions += metrics["function_count"]
        naming_violations += metrics["naming_violations"]
        total_doc_score += metrics["doc_score"]
        files_analyzed += 1

    avg_complexity = round(total_complexity / max(1, files_analyzed), 2)
    avg_doc_score = round(total_doc_score / max(1, files_analyzed), 1)

    # --- Test coverage estimation (PRD 4.1) ---
    test_files = parsed_data.get("test_files", [])
    source_files = [f for f in parsed_data["files"] if not f["is_test"]]
    test_coverage_signal = round(
        (len(test_files) / max(1, len(source_files))) * 100, 1
    )

    # --- Documentation completeness (PRD 4.1) ---
    doc_files = parsed_data.get("doc_files", [])
    has_readme = any("readme" in d.lower() for d in doc_files)
    doc_completeness = _compute_doc_completeness(has_readme, avg_doc_score, doc_files)

    return {
        "file_metrics": file_metrics,
        "summary": {
            "complexity_avg": avg_complexity,
            "total_functions": total_functions,
            "naming_violations": naming_violations,
            "doc_score": avg_doc_score,
            "test_coverage_signal": test_coverage_signal,
            "test_file_count": len(test_files),
            "doc_completeness": doc_completeness,
            "has_readme": has_readme,
            "files_analyzed": files_analyzed,
        },
    }


def _analyze_single_file(content: str, filepath: str) -> Dict[str, Any]:
    """Analyze a single Python file for complexity, naming, docs."""
    result = {
        "file": filepath,
        "avg_complexity": 0,
        "max_complexity": 0,
        "function_count": 0,
        "long_functions": [],
        "naming_violations": 0,
        "naming_issues": [],
        "doc_score": 0,
        "maintainability_index": 0,
    }

    # --- Radon complexity ---
    try:
        blocks = cc_visit(content)
        if blocks:
            complexities = [b.complexity for b in blocks]
            result["avg_complexity"] = round(sum(complexities) / len(complexities), 2)
            result["max_complexity"] = max(complexities)
            result["function_count"] = len(blocks)
    except Exception:
        pass

    # --- Radon maintainability index ---
    try:
        mi = mi_visit(content, True)
        result["maintainability_index"] = round(mi, 1)
    except Exception:
        pass

    # --- AST analysis for naming, docs, function length ---
    try:
        tree = ast.parse(content)
        _analyze_ast(tree, content, result)
    except SyntaxError:
        pass

    return result


def _analyze_ast(tree: ast.AST, content: str, result: Dict[str, Any]):
    """Extract naming violations, docstring presence, and long functions from AST."""
    lines = content.split("\n")
    functions_with_docs = 0
    total_defs = 0

    for node in ast.walk(tree):
        # Check function definitions
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            total_defs += 1
            name = node.name

            # Naming convention: Python functions should be snake_case
            if not name.startswith("_") and not _is_snake_case(name) and name != "__init__":
                result["naming_violations"] += 1
                result["naming_issues"].append({
                    "name": name,
                    "line": node.lineno,
                    "issue": f"Function '{name}' is not snake_case",
                })

            # Function length check
            func_lines = (node.end_lineno or node.lineno) - node.lineno + 1
            if func_lines > 50:
                result["long_functions"].append({
                    "name": name,
                    "line": node.lineno,
                    "length": func_lines,
                })

            # Docstring presence
            if (node.body and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, (ast.Constant, ast.Str))):
                functions_with_docs += 1

        # Check class definitions
        elif isinstance(node, ast.ClassDef):
            name = node.name
            if not _is_pascal_case(name):
                result["naming_violations"] += 1
                result["naming_issues"].append({
                    "name": name,
                    "line": node.lineno,
                    "issue": f"Class '{name}' is not PascalCase",
                })

    # Doc score: percentage of functions with docstrings
    if total_defs > 0:
        result["doc_score"] = round((functions_with_docs / total_defs) * 100, 1)


def _is_snake_case(name: str) -> bool:
    return name == name.lower() and " " not in name


def _is_pascal_case(name: str) -> bool:
    return name[0].isupper() and "_" not in name if name else False


def _compute_doc_completeness(has_readme: bool, avg_doc_score: float, doc_files: list) -> int:
    """Compute overall documentation completeness score 0-100."""
    score = 0
    if has_readme:
        score += 40
    score += min(40, avg_doc_score * 0.4)  # Up to 40 from docstrings
    score += min(20, len(doc_files) * 5)    # Up to 20 from extra doc files
    return round(min(100, score))
