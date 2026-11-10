"""
End-to-end tests for Preset Profiles, Input Schema Validation, and FastAPI REST Endpoints.
"""

import ipaddress
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

from netarchitect.models.scenario_inputs import (
    ScenarioInput,
    LinkRequest,
    SubnetRequest,
    MediumPreference,
    SecurityZone,
)
from netarchitect.presets.preset_registry import PresetRegistry
from netarchitect.network_planner import NetworkPlanner
from netarchitect.web.api_server import app
from netarchitect.exceptions import InvalidCIDRError, ScenarioValidationError


@pytest.mark.parametrize("preset_id", ["campus-lan", "metro-man", "global-wan"])
def test_all_builtin_presets_execute_cleanly(preset_id):
    sc = PresetRegistry.get_by_id(preset_id)
    assert sc is not None
    result = NetworkPlanner.execute_plan(sc)

    assert result.scenario_id == preset_id
    assert len(result.media_recommendations) > 0
    assert len(result.subnet_allocations) > 0
    assert len(result.executive_rationales) >= 4
    assert len(result.device_configs) == 3

    router_cfg = next(d for d in result.device_configs if d.device_role == "Core-Router").config_text
    for line in router_cfg.splitlines():
        if line.strip().startswith("ip address "):
            parts = line.strip().split()
            ipaddress.IPv4Address(parts[2])
            ipaddress.IPv4Address(parts[3])


def test_duplicate_vlan_id_raises_validation_error():
    with pytest.raises(ValidationError, match="Duplicate VLAN ID"):
        ScenarioInput(
            id="dup-vlan",
            name="Dup VLAN Test",
            description="Test",
            root_network="10.0.0.0/16",
            subnets=[
                SubnetRequest(name="Sub-A", required_hosts=20, vlan_id=10),
                SubnetRequest(name="Sub-B", required_hosts=30, vlan_id=10),
            ],
        )


def test_duplicate_link_id_raises_validation_error():
    with pytest.raises(ValidationError, match="Duplicate Link ID"):
        ScenarioInput(
            id="dup-link",
            name="Dup Link Test",
            description="Test",
            root_network="10.0.0.0/16",
            links=[
                LinkRequest(link_id="L1", source="A", destination="B", distance_meters=50.0),
                LinkRequest(link_id="L1", source="C", destination="D", distance_meters=60.0),
            ],
        )


def test_invalid_cidr_raises_invalid_cidr_error():
    with pytest.raises(InvalidCIDRError):
        ScenarioInput.validate_root_cidr("999.999.0.0/16")

    with pytest.raises(ValidationError, match="Invalid IPv4 root prefix"):
        ScenarioInput(
            id="bad-cidr",
            name="Bad CIDR",
            description="Test",
            root_network="999.999.0.0/16",
        )


def test_minimal_custom_json_with_case_insensitive_enums():
    sc = ScenarioInput(
        root_network="10.20.5.9/16",  # Non-canonical host bits automatically aligned
        resiliency_mode="single_homed",
        links=[{"distance_meters": 65.0, "medium_preference": "copper"}],
        subnets=[{"name": "Sales", "required_hosts": 50, "vlan_id": 20, "security_zone": "internal"}],
    )
    assert sc.root_network == "10.20.0.0/16"
    assert sc.links[0].medium_preference == MediumPreference.COPPER
    assert sc.subnets[0].security_zone == SecurityZone.INTERNAL


def test_api_presets_input_and_cisco_export_endpoints():
    client = TestClient(app)

    r_presets = client.get("/api/presets")
    assert r_presets.status_code == 200
    assert len(r_presets.json()) == 3

    r_input = client.get("/api/presets/campus-lan/input")
    assert r_input.status_code == 200
    assert r_input.json()["id"] == "campus-lan"

    r_cisco = client.get("/api/export/metro-man/cisco")
    assert r_cisco.status_code == 200
    assert "router ospf 1" in r_cisco.text


def test_api_custom_plan_valid_and_minimal_json():
    client = TestClient(app)
    minimal_payload = {
        "root_network": "192.168.50.0/24",
        "links": [{"distance_meters": 80, "medium_preference": "auto"}],
        "subnets": [{"name": "Devs", "required_hosts": 40, "vlan_id": 15}],
    }
    res = client.post("/api/plan", json=minimal_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["root_network"] == "192.168.50.0/24"
    assert data["subnet_allocations"][0]["cidr"] == "192.168.50.0/26"


def test_api_custom_plan_returns_422_on_distance_exhaustion_and_bad_cidr():
    client = TestClient(app)

    # 1. Copper > 100m
    r_err1 = client.post(
        "/api/plan",
        json={
            "root_network": "10.0.0.0/24",
            "links": [{"link_id": "BAD-L1", "distance_meters": 150.0, "medium_preference": "COPPER"}],
            "subnets": [{"name": "S1", "required_hosts": 10, "vlan_id": 10}],
        },
    )
    assert r_err1.status_code == 422
    assert r_err1.json()["detail"]["error_type"] == "PhysicalDistanceViolationError"

    # 2. Address exhaustion
    r_err2 = client.post(
        "/api/plan",
        json={
            "root_network": "192.168.1.0/24",
            "subnets": [{"name": "TooBig", "required_hosts": 300, "vlan_id": 10}],
        },
    )
    assert r_err2.status_code == 422
    assert r_err2.json()["detail"]["error_type"] == "AddressSpaceExhaustionError"

    # 3. Invalid CIDR (returns structured 422 instead of 500!)
    r_err3 = client.post(
        "/api/plan",
        json={"root_network": "invalid-cidr", "subnets": []},
    )
    assert r_err3.status_code == 422
    assert isinstance(r_err3.json()["detail"], list)
