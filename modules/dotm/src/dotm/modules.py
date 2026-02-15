"""Module CRUD operations for dotm."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import yaml
from rich.console import Console
from rich.table import Table

from dotm.config import get_dotfiles_repo, get_excluded_modules, get_modules_dir

console = Console()


def list_all_modules() -> list[dict]:
    """List all modules with their metadata."""
    modules_dir = get_modules_dir()
    if not modules_dir.exists():
        return []

    modules = []
    for mod_dir in sorted(modules_dir.iterdir()):
        config_file = mod_dir / "config.yml"
        if not mod_dir.is_dir() or not config_file.exists():
            continue
        with open(config_file) as f:
            config = yaml.safe_load(f) or {}
        modules.append({
            "name": mod_dir.name,
            "path": mod_dir,
            "config": config,
            "homebrew_packages": config.get("homebrew_packages", []),
            "homebrew_casks": config.get("homebrew_casks", []),
            "homebrew_taps": config.get("homebrew_taps", []),
            "mas_installed_apps": config.get("mas_installed_apps", []),
            "stow_dirs": config.get("stow_dirs", []),
            "mergeable_files": config.get("mergeable_files", []),
        })
    return modules


def get_deploy_modules() -> list[str]:
    """Read the install list from deploy.yml."""
    deploy_yml = get_dotfiles_repo() / "playbooks" / "deploy.yml"
    if not deploy_yml.exists():
        return []
    with open(deploy_yml) as f:
        data = yaml.safe_load(f)
    if not data or not isinstance(data, list):
        return []
    for play in data:
        dotmodules = play.get("vars", {}).get("dotmodules", {})
        return dotmodules.get("install", [])
    return []


def is_module_installed(name: str) -> bool:
    """Check if a module is in the deploy.yml install list."""
    return name in get_deploy_modules()


def add_to_deploy(name: str) -> None:
    """Add a module to the deploy.yml install list."""
    deploy_yml = get_dotfiles_repo() / "playbooks" / "deploy.yml"
    with open(deploy_yml) as f:
        content = f.read()
    with open(deploy_yml) as f:
        data = yaml.safe_load(f)

    install_list = data[0]["vars"]["dotmodules"]["install"]
    if name in install_list:
        return

    # Insert alphabetically
    install_list.append(name)
    install_list.sort()

    # Rewrite the file preserving structure
    with open(deploy_yml) as f:
        lines = f.readlines()

    # Find the install: block and reconstruct it
    new_lines = []
    in_install_block = False
    install_indent = ""
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("install:"):
            in_install_block = True
            install_indent = line[: len(line) - len(stripped)]
            new_lines.append(line)
            for mod in install_list:
                new_lines.append(f"{install_indent}  - {mod}\n")
            continue
        if in_install_block:
            if stripped.startswith("- ") and not stripped.startswith("- name:"):
                continue  # Skip old entries
            else:
                in_install_block = False
                new_lines.append(line)
        else:
            new_lines.append(line)

    with open(deploy_yml, "w") as f:
        f.writelines(new_lines)


def remove_from_deploy(name: str) -> None:
    """Remove a module from the deploy.yml install list."""
    deploy_yml = get_dotfiles_repo() / "playbooks" / "deploy.yml"
    with open(deploy_yml) as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped == f"- {name}" and not stripped.startswith("- name:"):
            # Check context — only skip if we're in the install block
            # Simple heuristic: these are indented module entries
            continue
        new_lines.append(line)

    with open(deploy_yml, "w") as f:
        f.writelines(new_lines)


def create_module(name: str, *, homebrew_packages: list[str] | None = None,
                  homebrew_casks: list[str] | None = None,
                  mas_apps: list[int] | None = None,
                  stow: bool = False) -> Path:
    """Create a new module directory with config.yml."""
    modules_dir = get_modules_dir()
    mod_dir = modules_dir / name

    if mod_dir.exists():
        raise FileExistsError(f"Module '{name}' already exists at {mod_dir}")

    mod_dir.mkdir(parents=True)

    config: dict = {}
    if homebrew_packages:
        config["homebrew_packages"] = homebrew_packages
    if homebrew_casks:
        config["homebrew_casks"] = homebrew_casks
    if mas_apps:
        config["mas_installed_apps"] = mas_apps
    if stow:
        config["stow_dirs"] = [name]
        (mod_dir / "files").mkdir()

    with open(mod_dir / "config.yml", "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    return mod_dir


def remove_module_symlinks(name: str) -> list[Path]:
    """Remove symlinks from ~/ that point into a module's files/ directory."""
    dotmodules_dir = Path.home() / ".dotmodules" / name / "files"
    if not dotmodules_dir.exists():
        return []

    removed = []
    home = Path.home()

    for src_file in dotmodules_dir.rglob("*"):
        if src_file.is_dir():
            continue
        rel = src_file.relative_to(dotmodules_dir)
        target = home / rel
        if target.is_symlink() and target.resolve() == src_file.resolve():
            target.unlink()
            removed.append(target)

    return removed


def run_ansible_for_module(name: str) -> subprocess.CompletedProcess:
    """Run ansible-playbook targeting a specific module."""
    repo = get_dotfiles_repo()
    deploy_yml = repo / "playbooks" / "deploy.yml"

    return subprocess.run(
        [
            "ansible-playbook", str(deploy_yml),
            "--extra-vars", f'{{"dotmodules": {{"install": ["{name}"]}}}}',
            "--connection", "local",
        ],
        capture_output=True,
        text=True,
        cwd=str(repo),
    )


def print_module_list(filter_mode: str | None = None) -> None:
    """Print a formatted table of modules."""
    modules = list_all_modules()
    deployed = get_deploy_modules()
    excluded = get_excluded_modules()

    table = Table(title="Dotfiles Modules")
    table.add_column("Module", style="cyan")
    table.add_column("Installed", style="green")
    table.add_column("Excluded", style="yellow")
    table.add_column("Packages", style="white")
    table.add_column("Casks", style="white")
    table.add_column("MAS", style="white")

    for mod in modules:
        name = mod["name"]
        installed = name in deployed
        is_excluded = name in excluded

        if filter_mode == "installed" and not installed:
            continue
        if filter_mode == "available" and installed:
            continue
        if filter_mode == "excluded" and not is_excluded:
            continue

        table.add_row(
            name,
            "yes" if installed else "no",
            "yes" if is_excluded else "",
            str(len(mod["homebrew_packages"])) if mod["homebrew_packages"] else "",
            str(len(mod["homebrew_casks"])) if mod["homebrew_casks"] else "",
            str(len(mod["mas_installed_apps"])) if mod["mas_installed_apps"] else "",
        )

    console.print(table)


def print_status() -> None:
    """Print a summary status of the dotfiles system."""
    modules = list_all_modules()
    deployed = get_deploy_modules()
    excluded = get_excluded_modules()

    installed_count = sum(1 for m in modules if m["name"] in deployed)
    excluded_count = len(excluded)

    total_pkgs = sum(len(m["homebrew_packages"]) for m in modules)
    total_casks = sum(len(m["homebrew_casks"]) for m in modules)
    total_mas = sum(len(m["mas_installed_apps"]) for m in modules)

    console.print(f"[bold]Dotfiles Status[/bold]")
    console.print(f"  Modules: {len(modules)} total, {installed_count} installed, {excluded_count} excluded")
    console.print(f"  Managed: {total_pkgs} packages, {total_casks} casks, {total_mas} MAS apps")
    console.print(f"  Repo: {get_dotfiles_repo()}")
