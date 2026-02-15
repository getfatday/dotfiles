"""Verification checks for dotfiles modules."""

from __future__ import annotations

import subprocess
from pathlib import Path

from rich.console import Console

from dotm.modules import list_all_modules, get_deploy_modules

console = Console()


def _run(cmd: list[str]) -> set[str]:
    """Run a command and return output as a set of lines."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return set()
        return {line.strip() for line in result.stdout.strip().splitlines() if line.strip()}
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return set()


def verify_module(mod: dict) -> list[tuple[str, bool, str]]:
    """Verify a single module's state. Returns list of (check_name, passed, detail)."""
    checks = []
    name = mod["name"]
    home = Path.home()
    dotmodules_dir = home / ".dotmodules" / name

    # Check homebrew packages
    if mod["homebrew_packages"]:
        installed = _run(["brew", "list", "--formula", "-1"])
        for pkg in mod["homebrew_packages"]:
            present = pkg in installed
            checks.append((f"brew:{pkg}", present, "installed" if present else "missing"))

    # Check homebrew casks
    if mod["homebrew_casks"]:
        installed = _run(["brew", "list", "--cask", "-1"])
        for cask in mod["homebrew_casks"]:
            present = cask in installed
            checks.append((f"cask:{cask}", present, "installed" if present else "missing"))

    # Check homebrew taps
    if mod["homebrew_taps"]:
        taps = _run(["brew", "tap"])
        for tap in mod["homebrew_taps"]:
            present = tap in taps
            checks.append((f"tap:{tap}", present, "tapped" if present else "missing"))

    # Check MAS apps
    if mod["mas_installed_apps"]:
        mas_raw = _run(["mas", "list"])
        mas_ids = set()
        for line in mas_raw:
            parts = line.split(None, 1)
            if parts:
                try:
                    mas_ids.add(int(parts[0]))
                except ValueError:
                    pass
        for app_id in mod["mas_installed_apps"]:
            present = app_id in mas_ids
            checks.append((f"mas:{app_id}", present, "installed" if present else "missing"))

    # Check stow symlinks
    if mod["stow_dirs"]:
        files_dir = dotmodules_dir / "files"
        if files_dir.exists():
            for src_file in files_dir.rglob("*"):
                if src_file.is_dir():
                    continue
                rel = src_file.relative_to(files_dir)
                target = home / rel
                if target.is_symlink():
                    actual = target.resolve()
                    expected = src_file.resolve()
                    if actual == expected:
                        checks.append((f"link:{rel}", True, "ok"))
                    else:
                        checks.append((f"link:{rel}", False, f"points to {actual}"))
                elif target.exists():
                    # File exists but isn't a symlink — might be a mergeable file
                    if rel.name in mod.get("mergeable_files", []):
                        checks.append((f"merge:{rel}", True, "exists (mergeable)"))
                    else:
                        checks.append((f"link:{rel}", False, "exists but not a symlink"))
                else:
                    checks.append((f"link:{rel}", False, "missing"))
        else:
            checks.append(("stow:files_dir", False, f"{files_dir} not found"))

    return checks


def run_verification(module_names: list[str] | None = None) -> dict[str, list[tuple[str, bool, str]]]:
    """Run verification for specified modules (or all installed)."""
    modules = list_all_modules()
    deployed = get_deploy_modules()

    if module_names:
        modules = [m for m in modules if m["name"] in module_names]
    else:
        modules = [m for m in modules if m["name"] in deployed]

    results = {}
    for mod in modules:
        results[mod["name"]] = verify_module(mod)
    return results


def print_verification(results: dict[str, list[tuple[str, bool, str]]]) -> bool:
    """Print verification results. Returns True if all passed."""
    all_passed = True
    for mod_name, checks in sorted(results.items()):
        if not checks:
            console.print(f"  [dim]{mod_name}: no checks[/dim]")
            continue
        passed = sum(1 for _, ok, _ in checks if ok)
        failed = len(checks) - passed
        if failed:
            all_passed = False
            console.print(f"  [red]{mod_name}: {passed}/{len(checks)} passed[/red]")
            for check_name, ok, detail in checks:
                if not ok:
                    console.print(f"    [red]FAIL[/red] {check_name}: {detail}")
        else:
            console.print(f"  [green]{mod_name}: {passed}/{len(checks)} passed[/green]")
    return all_passed


def run_doctor() -> list[tuple[str, bool, str]]:
    """Run system-wide health checks."""
    checks = []

    # uv installed?
    result = subprocess.run(["which", "uv"], capture_output=True, text=True)
    checks.append(("uv", result.returncode == 0, "installed" if result.returncode == 0 else "not found"))

    # Dotfiles repo accessible?
    from dotm.config import get_dotfiles_repo
    repo = get_dotfiles_repo()
    checks.append(("dotfiles_repo", repo.exists(), str(repo) if repo.exists() else f"{repo} not found"))

    # Ansible installed?
    result = subprocess.run(["which", "ansible-playbook"], capture_output=True, text=True)
    checks.append(("ansible", result.returncode == 0, "installed" if result.returncode == 0 else "not found"))

    # Stow installed?
    result = subprocess.run(["which", "stow"], capture_output=True, text=True)
    checks.append(("stow", result.returncode == 0, "installed" if result.returncode == 0 else "not found"))

    # Ansible collections?
    result = subprocess.run(
        ["ansible-galaxy", "collection", "list", "geerlingguy.mac"],
        capture_output=True, text=True,
    )
    checks.append(("ansible_collections", result.returncode == 0,
                    "geerlingguy.mac found" if result.returncode == 0 else "geerlingguy.mac missing"))

    # Broken symlinks in ~/
    home = Path.home()
    broken = []
    for item in home.iterdir():
        if item.is_symlink() and not item.exists():
            broken.append(item.name)
    checks.append(("broken_symlinks", len(broken) == 0,
                    "none" if not broken else f"{len(broken)} broken: {', '.join(broken[:5])}"))

    # Launchd agent?
    result = subprocess.run(
        ["launchctl", "list"],
        capture_output=True, text=True,
    )
    agent_loaded = "com.getfatday.dotm-sync" in result.stdout
    checks.append(("launchd_agent", agent_loaded,
                    "loaded" if agent_loaded else "not loaded"))

    # Security scan
    from dotm.security import scan_repo
    findings = scan_repo(repo)
    checks.append(("secrets_scan", len(findings) == 0,
                    "clean" if not findings else f"{len(findings)} potential secret(s) found"))

    return checks


def print_doctor(checks: list[tuple[str, bool, str]]) -> bool:
    """Print doctor results. Returns True if all passed."""
    all_ok = True
    console.print("[bold]System Health Check[/bold]\n")
    for name, ok, detail in checks:
        icon = "[green]OK[/green]" if ok else "[red]FAIL[/red]"
        console.print(f"  {icon}  {name}: {detail}")
        if not ok:
            all_ok = False
    return all_ok
