"""Module CRUD operations for dotm."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import yaml
from rich.console import Console
from rich.table import Table

from dotm.config import (
    get_declared_capabilities,
    get_dotfiles_repo,
    get_excluded_modules,
    get_modules_dir,
    get_role,
)

console = Console()

# A capability name as it appears under a module's `requires:` and a role's list in profiles.yml.
CAPABILITY_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def module_requires(config: dict, name: str) -> list[str]:
    """The capabilities a module lists under `requires:` in its config.yml (absent means none).

    Raises ValueError when the key is present but is not a list of capability names.
    """
    value = config.get("requires")
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(c, str) and CAPABILITY_RE.match(c) for c in value):
        raise ValueError(
            f"module '{name}': requires must be a list of capability names "
            f"(lowercase letters, digits, dashes), got {value!r}"
        )
    return list(value)


def _load_profiles() -> dict:
    profiles_yml = get_dotfiles_repo() / "playbooks" / "profiles.yml"
    if not profiles_yml.exists():
        return {}
    with open(profiles_yml) as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def get_role_capabilities() -> dict[str, list[str]]:
    """Read the role -> provided capabilities map from profiles.yml."""
    roles = _load_profiles().get("role_capabilities") or {}
    return {str(r): [str(c) for c in (caps or [])] for r, caps in roles.items()}


def resolve_capabilities(role: str | None, declared: list[str] | None = None,
                         role_capabilities: dict[str, list[str]] | None = None) -> set[str]:
    """The capability set a machine has: what its role provides plus what it declares directly.

    Mirrors the resolution in playbooks/deploy.yml. A role profiles.yml does not define
    raises ValueError, as the play refuses it. No role and nothing declared is the empty set.
    """
    if role_capabilities is None:
        role_capabilities = get_role_capabilities()
    caps: set[str] = set(declared or [])
    if role:
        if role not in role_capabilities:
            raise ValueError(
                f"role '{role}' is not defined under role_capabilities in playbooks/profiles.yml "
                f"(known: {', '.join(sorted(role_capabilities)) or 'none'})"
            )
        caps.update(role_capabilities[role])
    return caps


def get_capabilities() -> set[str]:
    """This machine's capability set, from its local dotm config and profiles.yml."""
    return resolve_capabilities(get_role(), get_declared_capabilities())


def select_modules(candidates: list[str], capabilities: set[str],
                   modules_dir: Path | None = None) -> list[str]:
    """The candidates whose `requires:` the capability set covers, sorted and unique.

    Mirrors the selection in playbooks/deploy.yml: a module with no `requires:` key (or no
    config.yml) is always selected; the rest need every listed capability.
    """
    if modules_dir is None:
        modules_dir = get_modules_dir()
    selected = []
    for name in candidates:
        config_file = modules_dir / name / "config.yml"
        config: dict = {}
        if config_file.exists():
            with open(config_file) as f:
                config = yaml.safe_load(f) or {}
        if set(module_requires(config, name)) <= capabilities:
            selected.append(name)
    return sorted(set(selected))


def unprovided_requirements(modules: list[dict] | None = None) -> dict[str, list[str]]:
    """Module -> capabilities it requires that no role in profiles.yml provides."""
    provided = {c for caps in get_role_capabilities().values() for c in caps}
    missing = {}
    for mod in modules if modules is not None else list_all_modules():
        gap = [c for c in mod.get("requires", []) if c not in provided]
        if gap:
            missing[mod["name"]] = gap
    return missing


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
            "requires": module_requires(config, mod_dir.name),
        })
    return modules


def get_deploy_modules() -> list[str]:
    """Read the base_modules list from profiles.yml."""
    return _load_profiles().get("base_modules", [])


def is_module_installed(name: str) -> bool:
    """Check if a module is in the deploy.yml install list."""
    return name in get_deploy_modules()


def add_to_deploy(name: str) -> None:
    """Add a module to the base_modules list in profiles.yml."""
    profiles_yml = get_dotfiles_repo() / "playbooks" / "profiles.yml"
    with open(profiles_yml) as f:
        data = yaml.safe_load(f)

    base_modules = data.get("base_modules", [])
    if name in base_modules:
        return

    # Insert alphabetically
    base_modules.append(name)
    base_modules.sort()
    data["base_modules"] = base_modules

    # Rewrite the file preserving structure
    with open(profiles_yml) as f:
        lines = f.readlines()

    # Find the base_modules: block and reconstruct it
    new_lines = []
    in_base_block = False
    base_indent = ""
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("base_modules:"):
            in_base_block = True
            base_indent = line[: len(line) - len(stripped)]
            new_lines.append(line)
            for mod in base_modules:
                new_lines.append(f"{base_indent}  - {mod}\n")
            continue
        if in_base_block:
            if stripped.startswith("- ") and not stripped.startswith("- name:"):
                continue  # Skip old entries
            else:
                in_base_block = False
                new_lines.append(line)
        else:
            new_lines.append(line)

    with open(profiles_yml, "w") as f:
        f.writelines(new_lines)


def remove_from_deploy(name: str) -> None:
    """Remove a module from the base_modules list in profiles.yml."""
    profiles_yml = get_dotfiles_repo() / "playbooks" / "profiles.yml"
    with open(profiles_yml) as f:
        lines = f.readlines()

    # Only remove entries within the base_modules block
    new_lines = []
    in_base_block = False
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("base_modules:"):
            in_base_block = True
            new_lines.append(line)
            continue
        if in_base_block:
            if stripped.startswith("- "):
                if stripped.strip() == f"- {name}":
                    continue  # Skip this entry
                new_lines.append(line)
            else:
                in_base_block = False
                new_lines.append(line)
        else:
            new_lines.append(line)

    with open(profiles_yml, "w") as f:
        f.writelines(new_lines)


def create_module(name: str, *, homebrew_packages: list[str] | None = None,
                  homebrew_casks: list[str] | None = None,
                  mas_apps: list[int] | None = None,
                  stow: bool = False,
                  requires: list[str] | None = None) -> Path:
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
    if requires:
        config["requires"] = module_requires({"requires": requires}, name)

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

    inventory = repo / "playbooks" / "inventory"
    return subprocess.run(
        [
            "ansible-playbook", str(deploy_yml),
            "-i", str(inventory),
            "--extra-vars", f'{{"final_modules": ["{name}"]}}',
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
    table.add_column("Requires", style="magenta")

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
            ", ".join(mod["requires"]),
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
    console.print(f"  Role: {get_role() or 'none'}")
    for name, gap in sorted(unprovided_requirements(modules).items()):
        console.print(f"  [yellow]{name} requires {', '.join(gap)}, which no role provides[/yellow]")
