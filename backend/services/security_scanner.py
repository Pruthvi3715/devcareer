"""
Security Anti-pattern Detection — Layer 3
PRD Section 4.1: Hardcoded secrets, SQL injection risks, exposed API keys, weak auth patterns.
Uses pattern matching + AST analysis (no external tool deps for hackathon speed).
"""
import ast
import re
from typing import Dict, Any, List


# Regex patterns for common security anti-patterns
SECRET_PATTERNS = [
    (r'(?i)(api[_-]?key|apikey|secret|token|password|passwd|pwd)\s*=\s*["\'][^"\']{8,}["\']',
     "Hardcoded secret/credential"),
    (r'(?i)(aws_access_key_id|aws_secret_access_key)\s*=\s*["\'][^"\']+["\']',
     "Hardcoded AWS credential"),
    (r'sk-[a-zA-Z0-9]{20,}', "Exposed API key (OpenAI/Stripe pattern)"),
    (r'ghp_[a-zA-Z0-9]{36}', "Exposed GitHub personal access token"),
    (r'-----BEGIN (RSA |EC )?PRIVATE KEY-----', "Private key in source code"),
]

SQL_INJECTION_PATTERNS = [
    (r'(?i)(execute|cursor\.execute)\s*\(\s*["\'].*%s', "SQL injection via string formatting"),
    (r'(?i)(execute|cursor\.execute)\s*\(\s*f["\']', "SQL injection via f-string"),
    (r'(?i)(execute|cursor\.execute)\s*\(\s*["\'].*\+', "SQL injection via concatenation"),
    (r'(?i)\.raw\s*\(\s*f["\']', "Django raw SQL with f-string"),
]

WEAK_AUTH_PATTERNS = [
    (r'(?i)compare_digest|hmac\.compare', None),  # Good pattern — anti-match
    (r'==\s*(password|passwd|pwd|hash|token|secret)', "Timing-attack vulnerable comparison"),
    (r'(?i)md5\s*\(', "Weak hash algorithm (MD5)"),
    (r'(?i)sha1\s*\(', "Weak hash algorithm (SHA1)"),
    (r'(?i)verify\s*=\s*False', "SSL verification disabled"),
]


def scan_repo(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scans all code files for security anti-patterns.
    Returns findings list with file, line, severity, category.
    """
    findings: List[Dict[str, Any]] = []

    for file_data in parsed_data["files"]:
        if file_data["is_test"]:
            continue

        content = file_data["content"]
        path = file_data["path"]
        lines = content.split("\n")

        # Secret detection
        for pattern, description in SECRET_PATTERNS:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    findings.append({
                        "file": path,
                        "lines": [i],
                        "severity": "critical",
                        "category": "security",
                        "finding": f"{description}: {line.strip()[:80]}",
                        "fix": "Move secrets to environment variables. Use python-dotenv or a secrets manager.",
                    })

        # SQL injection
        for pattern, description in SQL_INJECTION_PATTERNS:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    findings.append({
                        "file": path,
                        "lines": [i],
                        "severity": "critical",
                        "category": "security",
                        "finding": f"{description}: {line.strip()[:80]}",
                        "fix": "Use parameterized queries. Replace string formatting with query parameters.",
                    })

        # Weak auth / crypto
        for pattern, description in WEAK_AUTH_PATTERNS:
            if description is None:
                continue  # Skip anti-match patterns
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    findings.append({
                        "file": path,
                        "lines": [i],
                        "severity": "major" if "hash" in description.lower() else "critical",
                        "category": "security",
                        "finding": f"{description}: {line.strip()[:80]}",
                        "fix": _get_fix_for_category(description),
                    })

        # AST-based: eval/exec usage
        if file_data["language"] == "Python":
            _check_dangerous_calls(content, path, findings)

    return {
        "findings": findings,
        "summary": {
            "total": len(findings),
            "critical": sum(1 for f in findings if f["severity"] == "critical"),
            "major": sum(1 for f in findings if f["severity"] == "major"),
            "minor": sum(1 for f in findings if f["severity"] == "minor"),
        },
    }


def _check_dangerous_calls(content: str, path: str, findings: list):
    """Check for eval(), exec(), and other dangerous Python calls via AST."""
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in ("eval", "exec"):
                findings.append({
                    "file": path,
                    "lines": [node.lineno],
                    "severity": "critical",
                    "category": "security",
                    "finding": f"Use of {node.func.id}() — potential code injection vulnerability",
                    "fix": f"Remove {node.func.id}(). Parse data with json.loads() or ast.literal_eval() instead.",
                })
            elif node.func.id == "input" and "password" in content[max(0, node.col_offset - 50):node.col_offset + 50].lower():
                findings.append({
                    "file": path,
                    "lines": [node.lineno],
                    "severity": "major",
                    "category": "security",
                    "finding": "Password collected via input() — plaintext terminal echo",
                    "fix": "Use getpass.getpass() to hide password input.",
                })


def _get_fix_for_category(description: str) -> str:
    if "timing" in description.lower():
        return "Use hmac.compare_digest() instead of == for constant-time comparison."
    if "md5" in description.lower() or "sha1" in description.lower():
        return "Use bcrypt, argon2, or SHA-256 minimum. See OWASP Password Storage Cheatsheet."
    if "ssl" in description.lower():
        return "Set verify=True. Never disable SSL verification in production."
    return "Review and fix the security issue."
