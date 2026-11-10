"""
FastAPI Backend Application for NetArchitect Web Dashboard.
Exposes RESTful endpoints for querying presets, planning custom topologies,
and downloading Cisco IOS configurations.
"""

from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from netarchitect.exceptions import (
    AddressSpaceExhaustionError,
    NetArchitectError,
    PhysicalDistanceViolationError,
)
from netarchitect.models.architecture_outputs import PlanResult
from netarchitect.models.scenario_inputs import ScenarioInput
from netarchitect.network_planner import NetworkPlanner
from netarchitect.presets.preset_registry import PresetRegistry

app = FastAPI(
    title="NetArchitect Recommendation & Config Engine",
    description="Algorithmic Network Planning & Self-Explaining Architecture Engine",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).parent / "static"


@app.get("/api/presets", response_model=List[Dict[str, Any]])
def get_presets():
    """Returns metadata for all available built-in preset enterprise scenarios."""
    results = []
    for sc in PresetRegistry.get_all():
        total_endpoints = sum(s.required_hosts for s in sc.subnets)
        results.append({
            "id": sc.id,
            "name": sc.name,
            "description": sc.description,
            "root_network": sc.root_network,
            "resiliency_mode": sc.resiliency_mode,
            "links_count": len(sc.links),
            "subnets_count": len(sc.subnets),
            "total_endpoints": total_endpoints,
            "autonomous_system": sc.autonomous_system_number,
        })
    return results


@app.get("/api/presets/{preset_id}", response_model=PlanResult)
def run_preset(preset_id: str):
    """Executes an algorithmic plan for a named preset scenario."""
    scenario = PresetRegistry.get_by_id(preset_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found.")
    try:
        return NetworkPlanner.execute_plan(scenario)
    except NetArchitectError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/presets/{preset_id}/input", response_model=ScenarioInput)
def get_preset_input(preset_id: str):
    """Returns the raw ScenarioInput JSON for loading into the Custom JSON Editor."""
    scenario = PresetRegistry.get_by_id(preset_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found.")
    return scenario


@app.post("/api/plan", response_model=PlanResult)
def plan_scenario(scenario: ScenarioInput):
    """Ingests custom JSON scenario parameters, performs boundary checks, and returns architectural plan."""
    try:
        return NetworkPlanner.execute_plan(scenario)
    except PhysicalDistanceViolationError as e:
        raise HTTPException(status_code=422, detail={
            "error_type": "PhysicalDistanceViolationError",
            "message": str(e),
            "distance_meters": e.distance_meters,
            "medium": e.medium,
            "max_allowed_meters": e.max_allowed_meters,
        })
    except AddressSpaceExhaustionError as e:
        raise HTTPException(status_code=422, detail={
            "error_type": "AddressSpaceExhaustionError",
            "message": str(e),
            "required_hosts": e.required_hosts,
            "available_hosts": e.available_hosts,
            "root_prefix": e.root_prefix,
        })
    except NetArchitectError as e:
        raise HTTPException(status_code=400, detail={
            "error_type": "NetArchitectError",
            "message": str(e),
        })


@app.get("/api/export/{preset_id}/cisco", response_class=PlainTextResponse)
def export_cisco_config(preset_id: str):
    """Returns pure Cisco IOS configuration text for download or clipboard copy."""
    scenario = PresetRegistry.get_by_id(preset_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found.")
    plan = NetworkPlanner.execute_plan(scenario)
    return plan.unified_cisco_config


# Mount static directory for the single-page application dashboard
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", response_class=HTMLResponse)
    def serve_frontend():
        index_file = STATIC_DIR / "dashboard.html"
        return HTMLResponse(
            content=index_file.read_text(encoding="utf-8"),
            headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
        )

