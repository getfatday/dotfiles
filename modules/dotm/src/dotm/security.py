"""Secret scanning for dotfiles modules."""

from __future__ import annotations

import re
from pathlib import Path

from rich.console import Console

console = Console()

# Patterns that indicate secrets
SECRET_PATTERNS = [
    (re.compile(r"-----BEGIN.*PRIVATE KEY-----"), "Private key"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS access key"),
    (re.compile(r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token)\s*[:=]\s*['\"]?[A-Za-z0-9/+=]{20,}"), "API key/token"),
    (re.compile(r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"]?.{8,}"), "Password"),
    (re.compile(r"ghp_[A-Za-z0-9]{36}"), "GitHub personal access token"),
    (re.compile(r"gho_[A-Za-z0-9]{36}"), "GitHub OAuth token"),
    (re.compile(r"github_pat_[A-Za-z0-9_]{82}"), "GitHub fine-grained PAT"),
    (re.compile(r"sk-[A-Za-z0-9]{48}"), "OpenAI API key"),
    (re.compile(r"xox[bporas]-[A-Za-z0-9-]+"), "Slack token"),
    (re.compile(r"(?i)bearer\s+[A-Za-z0-9_.~+/=-]{20,}"), "Bearer token"),
]

# File extensions to skip (binary/non-text)
SKIP_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".webp", ".svg",
    ".zip", ".tar", ".gz", ".bz2", ".xz",
    ".pdf", ".doc", ".docx",
    ".pyc", ".pyo", ".class", ".o", ".so", ".dylib",
    ".woff", ".woff2", ".ttf", ".eot",
}

# Files to skip entirely
SKIP_FILES = {
    ".DS_Store", "Thumbs.db", ".git",
}


def scan_file(filepath: Path) -> list[tuple[int, str, str]]:
    """Scan a single file for secret patterns. Returns list of (line_num, pattern_name, line)."""
    if filepath.suffix.lower() in SKIP_EXTENSIONS:
        return []
    if filepath.name in SKIP_FILES:
        return []

    findings = []
    try:
        content = filepath.read_text(errors="ignore")
    except (OSError, UnicodeDecodeError):
        return []

    for i, line in enumerate(content.splitlines(), 1):
        for pattern, name in SECRET_PATTERNS:
            if pattern.search(line):
                findings.append((i, name, line.strip()[:120]))
    return findings


def scan_module(module_path: Path) -> list[tuple[Path, int, str, str]]:
    """Scan all files in a module for secrets. Returns list of (file, line, pattern, text)."""
    findings = []
    for f in module_path.rglob("*"):
        if f.is_file() and ".git" not in f.parts:
            for line_num, pattern_name, text in scan_file(f):
                findings.append((f, line_num, pattern_name, text))
    return findings


def scan_repo(repo_path: Path) -> list[tuple[Path, int, str, str]]:
    """Scan the entire dotfiles repo for secrets."""
    findings = []
    modules_dir = repo_path / "modules"
    if modules_dir.exists():
        for mod_dir in modules_dir.iterdir():
            if mod_dir.is_dir():
                findings.extend(scan_module(mod_dir))
    return findings


def scan_changed_files(repo_path: Path) -> list[tuple[Path, int, str, str]]:
    """Scan only git-changed files for secrets."""
    import subprocess

    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "--cached", "HEAD"],
            capture_output=True, text=True, cwd=repo_path, timeout=10,
        )
        staged = result.stdout.strip().splitlines()
        result = subprocess.run(
            ["git", "diff", "--name-only"],
            capture_output=True, text=True, cwd=repo_path, timeout=10,
        )
        unstaged = result.stdout.strip().splitlines()
        changed = set(staged + unstaged)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []

    findings = []
    for rel_path in changed:
        f = repo_path / rel_path
        if f.is_file():
            for line_num, pattern_name, text in scan_file(f):
                findings.append((f, line_num, pattern_name, text))
    return findings


def print_scan_results(findings: list[tuple[Path, int, str, str]], base_path: Path | None = None) -> bool:
    """Print scan results. Returns True if secrets were found."""
    if not findings:
        console.print("[green]No secrets detected.[/green]")
        return False

    console.print(f"[red bold]Found {len(findings)} potential secret(s)![/red bold]")
    for filepath, line_num, pattern_name, text in findings:
        display_path = filepath.relative_to(base_path) if base_path else filepath
        console.print(f"  [red]{display_path}:{line_num}[/red] — {pattern_name}")
        console.print(f"    {text}", style="dim")
    return True
