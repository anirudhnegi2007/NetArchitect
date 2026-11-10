"""
NetArchitect Interactive Command-Line Interface (CLI).
Powered by Typer and Rich to deliver an exceptional terminal UX with
color-coded tables, formatted syntax highlighting, and progress indicators.
"""

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from netarchitect.exceptions import (
    AddressSpaceExhaustionError,
    NetArchitectError,
    PhysicalDistanceViolationError,
)
from netarchitect.models.scenario_inputs import ScenarioInput
from netarchitect.network_planner import NetworkPlanner
from netarchitect.presets.preset_registry import PresetRegistry

app = typer.Typer(
    name="netarchitect",
    help="NetArchitect: Algorithmic Network Planning & Self-Explaining Architecture Engine",
    add_completion=False,
)
console = Console()


@app.command("presets")
def list_presets():
    """Lists all built-in enterprise network preset profiles."""
    table = Table(
        title="🌐 NetArchitect Built-in Enterprise Presets",
        show_header=True,
        header_style="bold cyan",
        border_style="blue",
    )
    table.add_column("Profile ID", style="bold yellow", width=14)
    table.add_column("Name", style="bold white", width=28)
    table.add_column("Root Prefix", style="green", width=15)
    table.add_column("Scale & Endpoints", style="magenta", width=22)
    table.add_column("Key Architectural Focus", style="cyan")

    presets = PresetRegistry.get_all()
    for sc in presets:
        total_endpoints = sum(s.required_hosts for s in sc.subnets)
        table.add_row(
            sc.id,
            sc.name,
            sc.root_network,
            f"{len(sc.links)} Links | {total_endpoints} Nodes",
            sc.description[:80] + "...",
        )

    console.print(table)
    console.print("\n[dim]Run any profile via:[/dim] [bold green]python -m netarchitect.cli run <profile-id> --export[/bold green]\n")


def display_plan_results(result, export_path: Optional[Path] = None):
    """Renders high-craft terminal tables for recommendation results."""
    # 1. Executive Summary Panel
    summary_text = Text()
    summary_text.append(f"Scenario: {result.scenario_name}\n", style="bold cyan")
    summary_text.append(f"Root Prefix: {result.root_network} | Efficiency: {result.overall_efficiency_pct}%\n", style="bold yellow")
    summary_text.append(f"Capacity: {result.total_available_ips} IPs | Usable Hosts: {result.total_usable_hosts}\n\n", style="bold green")
    
    for rationale in result.executive_rationales:
        summary_text.append(f"• {rationale}\n", style="white")

    console.print(Panel(summary_text, title="📊 Architectural Evaluation & Executive Summary", border_style="cyan"))

    # 2. L1/L2 Physical Media Table
    media_table = Table(title="🔌 Physical Layer (L1/L2) Media & Physics Engine", header_style="bold magenta", border_style="magenta")
    media_table.add_column("Link ID", style="yellow")
    media_table.add_column("Path", style="white")
    media_table.add_column("Distance", style="cyan")
    media_table.add_column("Medium", style="bold green")
    media_table.add_column("Standard", style="bold blue")
    media_table.add_column("Optical/Elec Rationale", style="dim white")

    for m in result.media_recommendations:
        media_table.add_row(
            m.link_id,
            f"{m.source} ➔ {m.destination}",
            f"{m.distance_meters:.0f}m" if m.distance_meters < 1000 else f"{m.distance_meters/1000:.1f}km",
            m.medium_type,
            m.standard,
            m.rationale[:80] + "...",
        )
    console.print(media_table)

    # 3. L3 VLSM Allocation Table
    vlsm_table = Table(title="📐 Layer 3 Bitwise VLSM Subnet Allocations (Zero Overlap)", header_style="bold green", border_style="green")
    vlsm_table.add_column("Subnet Name", style="bold yellow")
    vlsm_table.add_column("VLAN", style="cyan", justify="center")
    vlsm_table.add_column("Allocated CIDR", style="bold green")
    vlsm_table.add_column("Default Gateway", style="white")
    vlsm_table.add_column("Usable Host Range", style="dim white")
    vlsm_table.add_column("Wildcard Mask", style="magenta")
    vlsm_table.add_column("Eff %", style="cyan", justify="right")

    for s in result.subnet_allocations:
        vlsm_table.add_row(
            s.name,
            str(s.vlan_id),
            s.cidr,
            s.default_gateway,
            f"{s.first_usable_ip} - {s.last_usable_ip}",
            s.wildcard_mask,
            f"{s.efficiency_pct}%",
        )
    console.print(vlsm_table)

    # 4. Routing Table
    r = result.routing_recommendation
    routing_panel = Panel(
        f"[bold cyan]Protocol:[/bold cyan] {r.protocol} (AS {r.autonomous_system})\n"
        f"[bold green]Topology Tier:[/bold green] {r.topology_tier}\n"
        f"[bold yellow]Convergence Profile:[/bold yellow] {r.convergence_profile}\n"
        f"[bold magenta]RFC Citation:[/bold magenta] {r.rfc_citation}\n"
        f"[white]Rationale:[/white] {r.rationale}",
        title="🧭 Routing Engine Decision",
        border_style="yellow",
    )
    console.print(routing_panel)

    if export_path:
        console.print(f"\n[bold green]✔ Cisco IOS Configuration Exported to:[/bold green] [bold white]{export_path}[/bold white]\n")


@app.command("run")
def run_profile(
    profile_id: str = typer.Argument(..., help="Preset profile ID (campus-lan, metro-man, global-wan)"),
    export: bool = typer.Option(False, "--export", "-e", help="Export Cisco IOS .cfg to disk"),
    output_dir: str = typer.Option("exports", "--output-dir", "-o", help="Target output folder"),
):
    """Executes an enterprise network preset profile and displays recommendations."""
    scenario = PresetRegistry.get_by_id(profile_id)
    if not scenario:
        console.print(f"[bold red]Error:[/bold red] Profile '{profile_id}' not found.")
        console.print("Available presets: [bold yellow]campus-lan, metro-man, global-wan[/bold yellow]")
        raise typer.Exit(code=1)

    try:
        with console.status(f"[bold cyan]Evaluating {scenario.name} through NetArchitect engines...[/bold cyan]"):
            result = NetworkPlanner.execute_plan(scenario)
            export_path = None
            if export:
                export_path = NetworkPlanner.export_verification_artifacts(result, output_dir=output_dir)

        display_plan_results(result, export_path)

    except NetArchitectError as e:
        console.print(f"[bold red]Architectural Error Encountered:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command("plan")
def plan_custom(
    file: Path = typer.Option(..., "--file", "-f", help="Path to custom scenario JSON file", exists=True),
    export: bool = typer.Option(False, "--export", "-e", help="Export Cisco IOS .cfg to disk"),
    output_dir: str = typer.Option("exports", "--output-dir", "-o", help="Target output folder"),
):
    """Ingests custom network parameters from JSON, validates constraints, and plans architecture."""
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
        scenario = ScenarioInput(**data)
    except Exception as e:
        console.print(f"[bold red]Validation Error parsing '{file}':[/bold red] {e}")
        raise typer.Exit(code=1)

    try:
        with console.status(f"[bold cyan]Planning custom scenario '{scenario.name}'...[/bold cyan]"):
            result = NetworkPlanner.execute_plan(scenario)
            export_path = None
            if export:
                export_path = NetworkPlanner.export_verification_artifacts(result, output_dir=output_dir)

        display_plan_results(result, export_path)

    except PhysicalDistanceViolationError as e:
        console.print(Panel(
            f"[bold red]PHYSICAL DISTANCE VIOLATION DETECTED[/bold red]\n\n"
            f"{e}\n\n"
            f"[bold yellow]Remediation Guidance:[/bold yellow] Switch to single-mode fiber (OS2) or multimode (OM4) "
            f"to operate within IEEE 802.3 standards.",
            title="Boundary Error Caught",
            border_style="red"
        ))
        raise typer.Exit(code=1)
    except AddressSpaceExhaustionError as e:
        console.print(Panel(
            f"[bold red]ADDRESS SPACE EXHAUSTION DETECTED[/bold red]\n\n"
            f"{e}\n\n"
            f"[bold yellow]Remediation Guidance:[/bold yellow] Expand the root network prefix (e.g., from /{scenario.root_network.split('/')[1]} to a larger CIDR).",
            title="Subnetting Error Caught",
            border_style="red"
        ))
        raise typer.Exit(code=1)
    except NetArchitectError as e:
        console.print(f"[bold red]Planning Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command("web")
def launch_web(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Bind host"),
    port: int = typer.Option(8000, "--port", "-p", help="Port number"),
):
    """Launches the interactive Web UI Dashboard and REST API."""
    import uvicorn
    console.print(f"[bold green]Starting NetArchitect Web Dashboard on http://{host}:{port}[/bold green]")
    uvicorn.run("netarchitect.web.api_server:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    app()

