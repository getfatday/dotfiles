"""Auto-create modules from analysis results."""

from __future__ import annotations

from rich.console import Console
from rich.prompt import Confirm

from dotm.analyze import run_analysis
from dotm.modules import create_module, add_to_deploy
from dotm.security import scan_module

console = Console()

# Common groupings for unmanaged packages
PACKAGE_GROUPS = {
    "python": {"python", "python3", "python@3.12", "python@3.13", "pipx", "pyenv", "ruff", "black", "mypy"},
    "go": {"go", "golangci-lint", "gopls", "gore", "delve"},
    "ruby": {"ruby", "rbenv", "ruby-build", "cocoapods", "fastlane"},
    "java": {"java", "openjdk", "maven", "gradle", "kotlin"},
    "cloud": {"awscli", "azure-cli", "google-cloud-sdk", "terraform", "pulumi"},
    "network": {"curl", "wget", "httpie", "nmap", "mtr", "iperf3", "wireshark"},
    "media-tools": {"ffmpeg", "imagemagick", "yt-dlp", "exiftool", "gifsicle"},
    "compression": {"p7zip", "xz", "zstd", "lz4", "pigz"},
    "text-tools": {"jq", "yq", "fzf", "ripgrep", "fd", "bat", "eza", "sd"},
}


def suggest_groups(unmanaged: list[str]) -> dict[str, list[str]]:
    """Group unmanaged packages into suggested module names."""
    grouped: dict[str, list[str]] = {}
    remaining = set(unmanaged)

    for group_name, members in PACKAGE_GROUPS.items():
        matched = remaining & members
        if matched:
            grouped[group_name] = sorted(matched)
            remaining -= matched

    # Everything else goes into "misc" or individual modules
    if remaining:
        grouped["misc"] = sorted(remaining)

    return grouped


def run_catalog(dry_run: bool = False) -> None:
    """Analyze unmanaged packages and create modules for them."""
    results = run_analysis(brew=True, cask=True, mas=True)
    created = []

    # Process formulae
    if "brew" in results and results["brew"]["unmanaged"]:
        groups = suggest_groups(results["brew"]["unmanaged"])
        console.print(f"\n[bold]Suggested module groupings for {len(results['brew']['unmanaged'])} unmanaged formulae:[/bold]")
        for group_name, pkgs in groups.items():
            console.print(f"  [cyan]{group_name}[/cyan]: {', '.join(pkgs)}")

        if not dry_run:
            for group_name, pkgs in groups.items():
                if group_name == "misc" and len(pkgs) > 10:
                    console.print(f"\n[yellow]Skipping 'misc' ({len(pkgs)} packages) — too many to auto-group[/yellow]")
                    continue
                if Confirm.ask(f"\nCreate module [cyan]{group_name}[/cyan] with {len(pkgs)} packages?"):
                    try:
                        mod_dir = create_module(group_name, homebrew_packages=pkgs)
                        scan_result = scan_module(mod_dir)
                        if scan_result:
                            console.print(f"  [red]Security warning:[/red] {scan_result}")
                        else:
                            add_to_deploy(group_name)
                            created.append(group_name)
                            console.print(f"  [green]Created module '{group_name}'[/green]")
                    except FileExistsError:
                        console.print(f"  [yellow]Module '{group_name}' already exists, skipping[/yellow]")

    # Process casks
    if "cask" in results and results["cask"]["unmanaged"]:
        console.print(f"\n[bold]Unmanaged casks:[/bold]")
        for cask in results["cask"]["unmanaged"]:
            console.print(f"  [yellow]{cask}[/yellow]")
        if not dry_run:
            for cask in results["cask"]["unmanaged"]:
                if Confirm.ask(f"Create module [cyan]{cask}[/cyan]?"):
                    try:
                        create_module(cask, homebrew_casks=[cask])
                        add_to_deploy(cask)
                        created.append(cask)
                        console.print(f"  [green]Created module '{cask}'[/green]")
                    except FileExistsError:
                        console.print(f"  [yellow]Module '{cask}' already exists[/yellow]")

    # Process MAS apps
    if "mas" in results and results["mas"]["unmanaged"]:
        console.print(f"\n[bold]Unmanaged MAS apps:[/bold]")
        for app_id, app_name in results["mas"]["unmanaged"].items():
            console.print(f"  [yellow]{app_name}[/yellow] ({app_id})")

    if dry_run:
        console.print("\n[dim]Dry run — no modules created.[/dim]")
    elif created:
        console.print(f"\n[green]Created {len(created)} modules: {', '.join(created)}[/green]")
    else:
        console.print("\n[dim]No modules created.[/dim]")
