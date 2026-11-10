"""
Unit tests for Layer 3 Routing Protocol Decision Engine.
Verifies OSPF Area 0, BFD convergence, Multi-Area OSPF, and eBGP selection logic.
"""

from netarchitect.engines.routing_protocol_engine import RoutingProtocolEngine
from netarchitect.engines.vlsm_subnet_allocator import BitwiseVLSMAllocator
from netarchitect.models.scenario_inputs import (
    ResiliencyMode,
    ScenarioInput,
    SubnetRequest,
)
from netarchitect.presets.profile1_campus_lan import get_campus_lan_scenario
from netarchitect.presets.profile2_metro_man import get_metro_man_scenario
from netarchitect.presets.profile3_global_wan import get_global_wan_scenario


def test_campus_lan_selects_ospf_area_0():
    sc = get_campus_lan_scenario()
    allocations, _, _, _ = BitwiseVLSMAllocator.allocate(sc.root_network, sc.subnets)
    rec = RoutingProtocolEngine.evaluate_routing(sc, allocations)

    assert "OSPF Area 0" in rec.protocol
    assert "RFC 2328" in rec.rfc_citation
    assert "Dijkstra" in rec.rationale


def test_metro_man_selects_ospf_with_bfd_fast_convergence():
    sc = get_metro_man_scenario()
    allocations, _, _, _ = BitwiseVLSMAllocator.allocate(sc.root_network, sc.subnets)
    rec = RoutingProtocolEngine.evaluate_routing(sc, allocations)

    assert "OSPF" in rec.protocol
    assert "BFD" in rec.convergence_profile
    assert "RFC 5880" in rec.rfc_citation


def test_global_wan_selects_ebgp_and_multiarea_ospf():
    sc = get_global_wan_scenario()
    allocations, _, _, _ = BitwiseVLSMAllocator.allocate(sc.root_network, sc.subnets)
    rec = RoutingProtocolEngine.evaluate_routing(sc, allocations)

    assert "eBGP" in rec.protocol
    assert "RFC 4271" in rec.rfc_citation


def test_custom_multi_cloud_ha_selects_ebgp_isolation():
    sc = ScenarioInput(
        id="cloud-hybrid",
        name="Hybrid Cloud Core",
        description="Multi-cloud boundary test",
        root_network="10.80.0.0/16",
        resiliency_mode=ResiliencyMode.MULTI_CLOUD_HA,
        autonomous_system_number=65400,
        subnets=[SubnetRequest(name="AppTier", required_hosts=100, vlan_id=10)],
    )
    allocations, _, _, _ = BitwiseVLSMAllocator.allocate(sc.root_network, sc.subnets)
    rec = RoutingProtocolEngine.evaluate_routing(sc, allocations)

    assert "eBGP" in rec.protocol
    assert rec.autonomous_system == 65400
    assert "10.80.0.0/16" in rec.summary_routes
