"""
Repo Cloning & Parsing — Layer 2
PRD Section 4.1: Clones repos locally, detects languages, maps file tree
and module structure. Feeds both analysis and PS3 graph.
"""
import os
import ast
import shutil
import tempfile
from typing import Dict, Any, List, Tuple
from git import Repo


# Max file size to read (100KB) — skip binaries and huge generated files
MAX_FILE_SIZE = 100_000

# Extensions we analyze
ANALYZABLE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rb",
    ".rs", ".cpp", ".c", ".h", ".cs", ".php", ".swift", ".kt",
}

# Temp directory root for clones
CLONE_ROOT = os.path.join(tempfile.gettempdir(), "devcareer_clones")


def clone_repo(clone_url: str, repo_name: str) -> str:
    """
    Clones a repo to a temp directory. Returns the local path.
    Uses a unique temp folder per clone to avoid collisions between
    concurrent audits and Windows file locking issues.
    """
    os.makedirs(CLONE_ROOT, exist_ok=True)
    local_path = tempfile.mkdtemp(prefix=f"{repo_name}_", dir=CLONE_ROOT)

    try:
        Repo.clone_from(clone_url, local_path, depth=1, single_branch=True)
    except Exception as e:
        shutil.rmtree(local_path, ignore_errors=True)
        raise ValueError(f"Failed to clone {repo_name}: {e}")

    return local_path


def parse_repo(local_path: str) -> Dict[str, Any]:
    """
    Walks the cloned repo file tree and extracts:
    - file list with language detection
    - file contents (for analyzable files under size limit)
    - entry points detected
    - test files detected
    - documentation files detected
    """
    files_data: List[Dict[str, Any]] = []
    entry_points: List[str] = []
    test_files: List[str] = []
    doc_files: List[str] = []
    language_file_counts: Dict[str, int] = {}

    for root, dirs, filenames in os.walk(local_path):
        # Skip hidden dirs and common noise
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in {
            "node_modules", "__pycache__", "venv", ".venv", "dist", "build",
            ".git", ".idea", ".vscode", "vendor",
        }]

        for fname in filenames:
            filepath = os.path.join(root, fname)
            relpath = os.path.relpath(filepath, local_path)
            _, ext = os.path.splitext(fname)
            ext_lower = ext.lower()

            # Detect documentation files
            if fname.lower() in {"readme.md", "readme.rst", "readme.txt", "readme",
                                  "contributing.md", "changelog.md", "docs.md"}:
                doc_files.append(relpath)

            # Only analyze code files
            if ext_lower not in ANALYZABLE_EXTENSIONS:
                continue

            # Track language distribution
            lang = _ext_to_language(ext_lower)
            language_file_counts[lang] = language_file_counts.get(lang, 0) + 1

            # Read file content if under size limit
            try:
                size = os.path.getsize(filepath)
                if size > MAX_FILE_SIZE:
                    continue

                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception:
                continue

            # Detect entry points
            is_entry = _is_entry_point(fname, content, ext_lower)
            if is_entry:
                entry_points.append(relpath)

            # Detect test files
            is_test = _is_test_file(fname, relpath)
            if is_test:
                test_files.append(relpath)

            files_data.append({
                "path": relpath,
                "language": lang,
                "size_bytes": size,
                "content": content,
                "is_entry_point": is_entry,
                "is_test": is_test,
                "line_count": content.count("\n") + 1,
            })

    return {
        "files": files_data,
        "entry_points": entry_points,
        "test_files": test_files,
        "doc_files": doc_files,
        "language_file_counts": language_file_counts,
        "total_files": len(files_data),
    }


def _ext_to_language(ext: str) -> str:
    mapping = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
        ".jsx": "React JSX", ".tsx": "React TSX", ".java": "Java",
        ".go": "Go", ".rb": "Ruby", ".rs": "Rust",
        ".cpp": "C++", ".c": "C", ".h": "C/C++ Header",
        ".cs": "C#", ".php": "PHP", ".swift": "Swift", ".kt": "Kotlin",
    }
    return mapping.get(ext, "Unknown")


def _is_entry_point(fname: str, content: str, ext: str) -> bool:
    lower = fname.lower()
    if lower in {"main.py", "app.py", "index.js", "index.ts", "server.py",
                  "server.js", "manage.py", "wsgi.py", "asgi.py", "main.go", "main.rs"}:
        return True
    if ext == ".py" and 'if __name__' in content:
        return True
    return False


def _is_test_file(fname: str, relpath: str) -> bool:
    lower = fname.lower()
    rel_lower = relpath.lower()
    if lower.startswith("test_") or lower.endswith("_test.py"):
        return True
    if ".test." in lower or ".spec." in lower:
        return True
    if "/tests/" in rel_lower or "/test/" in rel_lower or "/__tests__/" in rel_lower:
        return True
    return False


def cleanup_clone(path_or_repo_name: str):
    """
    Remove a cloned repo from the temp directory.
    Accepts either a full local path returned by `clone_repo` or a legacy repo name.
    """
    # If a full path was provided, delete it directly.
    if os.path.isabs(path_or_repo_name) and os.path.exists(path_or_repo_name):
        shutil.rmtree(path_or_repo_name, ignore_errors=True)
        return

    # Legacy fallback: attempt CLONE_ROOT/<repo_name>
    local_path = os.path.join(CLONE_ROOT, path_or_repo_name)
    if os.path.exists(local_path):
        shutil.rmtree(local_path, ignore_errors=True)
