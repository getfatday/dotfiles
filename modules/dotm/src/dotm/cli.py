"""Click CLI for dotm — Universal dotfiles module manager."""

from __future__ import annotations

import sys

import click
from rich.console import Console

from dotm.config import ensure_config, exclude_module, include_module, get_dotfiles_repo

console = Console()


@click.group(invoke_without_command=True)
@click.version_option(version="0.1.0")
@click.pass_context
def main(ctx):
    """dotm — Universal dotfiles module manager."""
    ensure_config()
    if ctx.invoked_subcommand is None:
        ctx.invoke(plan)


# --- list ---


@main.command("list")
@click.option("--installed", "filter_mode", flag_value="installed", help="Show only installed modules")
@click.option("--available", "filter_mode", flag_value="available", help="Show only uninstalled modules")
@click.option("--excluded", "filter_mode", flag_value="excluded", help="Show only excluded modules")
def list_cmd(filter_mode):
    """List all dotfiles modules."""
    from dotm.modules import print_module_list
    print_module_list(filter_mode)


# --- status ---


@main.command()
def status():
    """Show dotfiles system status summary."""
    from dotm.modules import print_status
    print_status()


# --- verify ---


@main.command()
@click.argument("modules", nargs=-1)
def verify(modules):
    """Verify module installations are correct."""
    from dotm.verify import run_verification, print_verification
    names = list(modules) if modules else None
    results = run_verification(names)
    ok = print_verification(results)
    if not ok:
        sys.exit(1)


# --- install ---


@main.command()
@click.argument("module")
def install(module):
    """Install a dotfiles module."""
    from dotm.modules import list_all_modules, add_to_deploy, is_module_installed, run_ansible_for_module

    available = [m["name"] for m in list_all_modules()]
    if module not in available:
        console.print(f"[red]Module '{module}' not found.[/red]")
        console.print(f"Available: {', '.join(available)}")
        sys.exit(1)

    if is_module_installed(module):
        console.print(f"[yellow]Module '{module}' is already installed.[/yellow]")
    else:
        add_to_deploy(module)
        console.print(f"Added '{module}' to deploy.yml")

    # Remove from exclusion list if present
    include_module(module)

    console.print(f"[dim]Running ansible for '{module}'...[/dim]")
    result = run_ansible_for_module(module)
    if result.returncode == 0:
        console.print(f"[green]Module '{module}' installed successfully.[/green]")
    else:
        console.print(f"[red]Installation failed:[/red]")
        console.print(result.stderr[:500] if result.stderr else result.stdout[:500])
        sys.exit(1)


# --- uninstall ---


@main.command()
@click.argument("module")
def uninstall(module):
    """Uninstall a dotfiles module (removes symlinks, keeps packages)."""
    from dotm.modules import remove_from_deploy, remove_module_symlinks, is_module_installed

    if not is_module_installed(module):
        console.print(f"[yellow]Module '{module}' is not installed.[/yellow]")
        sys.exit(1)

    remove_from_deploy(module)
    removed = remove_module_symlinks(module)

    console.print(f"Removed '{module}' from deploy.yml")
    if removed:
        console.print(f"Removed {len(removed)} symlinks")
        for r in removed[:10]:
            console.print(f"  {r}")
    console.print(f"[green]Module '{module}' uninstalled.[/green]")
    console.print("[dim]Note: Homebrew packages were NOT uninstalled (other modules may need them).[/dim]")


# --- create ---


@main.command()
@click.argument("name")
@click.option("--brew", "brew_pkgs", help="Comma-separated Homebrew formulae")
@click.option("--cask", "cask_pkgs", help="Comma-separated Homebrew casks")
@click.option("--mas", "mas_ids", help="Comma-separated MAS app IDs")
@click.option("--interactive", is_flag=True, help="Guided module creation")
def create(name, brew_pkgs, cask_pkgs, mas_ids, interactive):
    """Create a new dotfiles module."""
    from dotm.modules import create_module, add_to_deploy
    from dotm.security import scan_module

    pkgs = [p.strip() for p in brew_pkgs.split(",")] if brew_pkgs else None
    casks = [c.strip() for c in cask_pkgs.split(",")] if cask_pkgs else None
    mas = [int(m.strip()) for m in mas_ids.split(",")] if mas_ids else None

    if interactive:
        if not pkgs:
            raw = click.prompt("Homebrew formulae (comma-separated, or empty)", default="")
            pkgs = [p.strip() for p in raw.split(",") if p.strip()] or None
        if not casks:
            raw = click.prompt("Homebrew casks (comma-separated, or empty)", default="")
            casks = [c.strip() for c in raw.split(",") if c.strip()] or None
        if not mas:
            raw = click.prompt("MAS app IDs (comma-separated, or empty)", default="")
            mas = [int(m.strip()) for m in raw.split(",") if m.strip()] or None

    has_stow = click.confirm("Create files/ directory for dotfiles?", default=False) if interactive else False

    try:
        mod_dir = create_module(name, homebrew_packages=pkgs, homebrew_casks=casks,
                                mas_apps=mas, stow=has_stow)
    except FileExistsError:
        console.print(f"[red]Module '{name}' already exists.[/red]")
        sys.exit(1)

    # Security scan
    findings = scan_module(mod_dir)
    if findings:
        console.print(f"[red]Security warning: {len(findings)} potential secret(s) found![/red]")
        sys.exit(1)

    add_to_deploy(name)
    console.print(f"[green]Created module '{name}' at {mod_dir}[/green]")
    console.print(f"Added to deploy.yml install list")


# --- analyze ---


@main.command()
@click.option("--brew", is_flag=True, help="Analyze Homebrew formulae")
@click.option("--cask", is_flag=True, help="Analyze Homebrew casks")
@click.option("--mas", is_flag=True, help="Analyze Mac App Store apps")
@click.option("--dotfiles", is_flag=True, help="Analyze dotfiles")
@click.option("--all", "all_", is_flag=True, help="Run all analyses")
def analyze(brew, cask, mas, dotfiles, all_):
    """Detect drift — packages installed outside module management."""
    from dotm.analyze import run_analysis, print_analysis
    if not any([brew, cask, mas, dotfiles, all_]):
        all_ = True
    results = run_analysis(brew=brew, cask=cask, mas=mas, dotfiles=dotfiles, all_=all_)
    print_analysis(results)


# --- catalog ---


@main.command()
@click.option("--dry-run", is_flag=True, help="Preview without creating modules")
def catalog(dry_run):
    """Auto-create modules from unmanaged packages."""
    from dotm.catalog import run_catalog
    run_catalog(dry_run=dry_run)


# --- sync ---


@main.command()
@click.option("--quiet", is_flag=True, help="Only output errors (for launchd)")
def sync(quiet):
    """Pull latest changes and apply modules."""
    from dotm.sync import run_sync
    ok = run_sync(quiet=quiet)
    if not ok:
        sys.exit(1)


# --- exclude ---


@main.command()
@click.argument("module")
def exclude(module):
    """Exclude a module from sync/apply."""
    exclude_module(module)
    console.print(f"[yellow]Excluded '{module}' — it will be skipped during sync.[/yellow]")


# --- include ---


@main.command("include")
@click.argument("module")
def include_cmd(module):
    """Re-include an excluded module."""
    include_module(module)
    console.print(f"[green]Included '{module}' — it will be applied during sync.[/green]")


# --- push ---


@main.command()
@click.option("--message", "-m", help="Commit message")
@click.option("--dry-run", is_flag=True, help="Scan and preview without pushing")
def push(message, dry_run):
    """Security scan, commit, and push module changes."""
    from dotm.sync import run_push
    ok = run_push(message=message, dry_run=dry_run)
    if not ok:
        sys.exit(1)


# --- doctor ---


@main.command()
def doctor():
    """Diagnose common issues with the dotfiles system."""
    from dotm.verify import run_doctor, print_doctor
    checks = run_doctor()
    ok = print_doctor(checks)
    if not ok:
        sys.exit(1)


# --- bootstrap ---


@main.command()
@click.option("--host", help="Remote host IP/hostname")
@click.option("--user", default="ianderson", help="Remote user")
def bootstrap(host, user):
    """Bootstrap dotfiles on a remote Mac."""
    import subprocess

    if not host:
        console.print("[red]--host is required[/red]")
        sys.exit(1)

    repo = get_dotfiles_repo()
    console.print(f"[dim]Bootstrapping {user}@{host}...[/dim]")

    # Copy the repo to the remote host
    result = subprocess.run(
        ["ssh", f"{user}@{host}", "test", "-d", "~/src/dotfiles"],
        capture_output=True,
    )
    if result.returncode != 0:
        console.print("[dim]Cloning dotfiles repo on remote...[/dim]")
        subprocess.run(
            ["ssh", f"{user}@{host}", "git", "clone",
             "https://github.com/getfatday/dotfiles.git", "~/src/dotfiles"],
            check=True,
        )

    console.print("[dim]Running sync on remote...[/dim]")
    result = subprocess.run(
        ["ssh", f"{user}@{host}", "~/.local/bin/dotm", "sync"],
        text=True,
    )
    if result.returncode == 0:
        console.print(f"[green]Bootstrap complete for {user}@{host}.[/green]")
    else:
        console.print(f"[red]Bootstrap failed.[/red]")
        sys.exit(1)


# --- plan ---


@main.command()
@click.argument("prompt", nargs=-1)
def plan(prompt):
    """Open Claude Code in the dotfiles repo for interactive planning."""
    import shutil
    import subprocess

    claude_bin = shutil.which("claude")
    if not claude_bin:
        console.print("[red]Claude Code CLI not found.[/red]")
        console.print("Install it: npm install -g @anthropic-ai/claude-code")
        sys.exit(1)

    repo_path = get_dotfiles_repo()
    if not repo_path.exists():
        console.print(f"[red]Dotfiles repo not found at {repo_path}[/red]")
        sys.exit(1)

    cmd = [claude_bin]
    if prompt:
        cmd.extend(["-p", " ".join(prompt)])

    console.print(f"[dim]Launching Claude Code in {repo_path}...[/dim]")
    result = subprocess.run(cmd, cwd=repo_path)
    sys.exit(result.returncode)
