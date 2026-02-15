"""Drift detection for brew, cask, MAS, and dotfiles."""

from __future__ import annotations

import subprocess
from pathlib import Path

from rich.console import Console
from rich.table import Table

from dotm.modules import list_all_modules

console = Console()


def _run(cmd: list[str]) -> list[str]:
    """Run a command and return output lines, empty list on failure."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return []
        return [line.strip() for line in result.stdout.strip().splitlines() if line.strip()]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []


def get_managed_packages() -> set[str]:
    """Collect all homebrew_packages from all modules."""
    return {pkg for m in list_all_modules() for pkg in m["homebrew_packages"]}


def get_managed_casks() -> set[str]:
    """Collect all homebrew_casks from all modules."""
    return {cask for m in list_all_modules() for cask in m["homebrew_casks"]}


def get_managed_mas() -> set[int]:
    """Collect all mas_installed_apps from all modules."""
    return {app for m in list_all_modules() for app in m["mas_installed_apps"]}


def analyze_brew() -> dict:
    """Find unmanaged Homebrew formulae."""
    installed = set(_run(["brew", "list", "--formula", "-1"]))
    managed = get_managed_packages()
    unmanaged = sorted(installed - managed)
    return {"installed": len(installed), "managed": len(managed & installed), "unmanaged": unmanaged}


def analyze_cask() -> dict:
    """Find unmanaged Homebrew casks."""
    installed = set(_run(["brew", "list", "--cask", "-1"]))
    managed = get_managed_casks()
    unmanaged = sorted(installed - managed)
    return {"installed": len(installed), "managed": len(managed & installed), "unmanaged": unmanaged}


def analyze_mas() -> dict:
    """Find unmanaged Mac App Store apps."""
    raw = _run(["mas", "list"])
    installed = {}
    for line in raw:
        parts = line.split(None, 1)
        if parts:
            try:
                app_id = int(parts[0])
                app_name = parts[1] if len(parts) > 1 else str(app_id)
                # Strip version info in parentheses
                if "(" in app_name:
                    app_name = app_name[:app_name.rfind("(")].strip()
                installed[app_id] = app_name
            except ValueError:
                continue
    managed = get_managed_mas()
    unmanaged = {k: v for k, v in installed.items() if k not in managed}
    return {"installed": len(installed), "managed": len(managed & set(installed.keys())), "unmanaged": unmanaged}


def analyze_dotfiles() -> dict:
    """Find dotfiles in ~/ not managed by any module."""
    home = Path.home()
    dotmodules = home / ".dotmodules"

    # Collect all managed symlink targets
    managed_targets: set[Path] = set()
    if dotmodules.exists():
        for mod_dir in dotmodules.iterdir():
            files_dir = mod_dir / "files"
            if files_dir.exists():
                for f in files_dir.rglob("*"):
                    if not f.is_dir():
                        managed_targets.add(f.resolve())

    # Scan common config locations for orphan symlinks pointing outside dotmodules
    orphan_symlinks: list[str] = []
    scan_paths = [
        home / ".config",
        home / ".local" / "bin",
    ]
    # Also check top-level dotfiles
    for item in home.iterdir():
        if item.name.startswith(".") and item.is_symlink():
            target = item.resolve()
            if target not in managed_targets and ".dotmodules" not in str(target):
                orphan_symlinks.append(str(item.relative_to(home)))

    for scan_dir in scan_paths:
        if not scan_dir.exists():
            continue
        for item in scan_dir.rglob("*"):
            if item.is_symlink():
                target = item.resolve()
                if target not in managed_targets and ".dotmodules" not in str(target):
                    orphan_symlinks.append(str(item.relative_to(home)))

    return {"orphan_symlinks": sorted(orphan_symlinks[:50])}  # Cap at 50


def run_analysis(*, brew: bool = False, cask: bool = False, mas: bool = False,
                 dotfiles: bool = False, all_: bool = False) -> dict:
    """Run requested analyses and return combined results."""
    results = {}
    if all_ or brew:
        results["brew"] = analyze_brew()
    if all_ or cask:
        results["cask"] = analyze_cask()
    if all_ or mas:
        results["mas"] = analyze_mas()
    if all_ or dotfiles:
        results["dotfiles"] = analyze_dotfiles()
    return results


def print_analysis(results: dict) -> None:
    """Pretty-print analysis results."""
    if "brew" in results:
        data = results["brew"]
        console.print(f"\n[bold]Homebrew Formulae[/bold]")
        console.print(f"  Installed: {data['installed']}, Managed: {data['managed']}")
        if data["unmanaged"]:
            table = Table(title="Unmanaged Formulae", show_lines=False)
            table.add_column("Package", style="yellow")
            for pkg in data["unmanaged"]:
                table.add_row(pkg)
            console.print(table)
        else:
            console.print("  [green]All formulae are managed![/green]")

    if "cask" in results:
        data = results["cask"]
        console.print(f"\n[bold]Homebrew Casks[/bold]")
        console.print(f"  Installed: {data['installed']}, Managed: {data['managed']}")
        if data["unmanaged"]:
            table = Table(title="Unmanaged Casks", show_lines=False)
            table.add_column("Cask", style="yellow")
            for cask in data["unmanaged"]:
                table.add_row(cask)
            console.print(table)
        else:
            console.print("  [green]All casks are managed![/green]")

    if "mas" in results:
        data = results["mas"]
        console.print(f"\n[bold]Mac App Store[/bold]")
        console.print(f"  Installed: {data['installed']}, Managed: {data['managed']}")
        if data["unmanaged"]:
            table = Table(title="Unmanaged MAS Apps", show_lines=False)
            table.add_column("ID", style="white")
            table.add_column("Name", style="yellow")
            for app_id, app_name in sorted(data["unmanaged"].items()):
                table.add_row(str(app_id), app_name)
            console.print(table)
        else:
            console.print("  [green]All MAS apps are managed![/green]")

    if "dotfiles" in results:
        data = results["dotfiles"]
        console.print(f"\n[bold]Dotfiles[/bold]")
        if data["orphan_symlinks"]:
            console.print(f"  Found {len(data['orphan_symlinks'])} orphan symlinks:")
            for s in data["orphan_symlinks"]:
                console.print(f"    {s}", style="yellow")
        else:
            console.print("  [green]No orphan symlinks found.[/green]")
