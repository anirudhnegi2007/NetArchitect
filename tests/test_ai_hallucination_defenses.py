"""
Unit tests validating AI Defenses & Hallucination Regressions.
Maps directly to Rubric Section 5 and ai_audit_log.md case studies:
- Case 1: Inverted Wildcard Mask & Canonical Boundary AND Alignment
- Case 2: DTP Exploitation & Native VLAN Double-Tagging Prevention
- Case 3: Fiber Optic Distance Extinction (OM4 400m vs OS2 10/40km)
"""

import ipaddress
import pytest
from netarchitect.models.scenario_inputs import LinkRequest, MediumPreference, SubnetRequest
from netarchitect.engines.physical_media_engine import L1L2MediaEngine
from netarchitect.engines.vlsm_subnet_allocator import BitwiseVLSMAllocator
from netarchitect.exporters.cisco_ios_config_generator import CiscoIOSConfigSynthesizer
from netarchitect.presets.profile1_campus_lan import get_campus_lan_scenario
from netarchitect.network_planner import NetworkPlanner


def test_ai_defense_case_1_canonical_network_alignment():
    """
    AI Bug: AI emitted OSPF statements with unmasked host bits (e.g. 10.10.35.12 0.0.15.255).
    Defense: Engine must bitwise AND the base address so (net_int & wildcard_int) == 0.
    """
    subnets = [
        SubnetRequest(name="Arbitrary-Offset-Subnet", required_hosts=400, vlan_id=10),
    ]
    allocations, _, _, _ = BitwiseVLSMAllocator.allocate("10.10.32.0/20", subnets)
    alloc = allocations[0]

    net_int = int(ipaddress.IPv4Address(alloc.network_address))
    wildcard_int = int(ipaddress.IPv4Address(alloc.wildcard_mask))

    # Host bits in network address must be strictly 0
    assert (net_int & wildcard_int) == 0, "Security violation: Host bits leaked into canonical network address!"
    assert alloc.network_address == "10.10.32.0"
    assert alloc.wildcard_mask == "0.0.1.255"  # /23 for 400 hosts


def test_ai_defense_case_2_dtp_and_native_vlan_mitigation():
    """
    AI Bug: AI emitted bare 'switchport mode trunk' with Native VLAN 1, enabling DTP spoofing
    and double-tagging VLAN hopping attacks.
    Defense: Generated trunk ports MUST include 'switchport nonegotiate' and set native vlan 999.
    """
    sc = get_campus_lan_scenario()
    plan = NetworkPlanner.execute_plan(sc)

    for dev in plan.device_configs:
        if "switch" in dev.device_role.lower():
            cfg = dev.config_text
            # Assert DTP disabled
            assert "switchport nonegotiate" in cfg
            # Assert default Native VLAN 1 is NOT used for trunk encapsulation
            assert "switchport trunk native vlan 1\n" not in cfg
            assert f"switchport trunk native vlan {CiscoIOSConfigSynthesizer.NATIVE_QUARANTINE_VLAN}" in cfg


def test_ai_defense_case_3_fiber_optic_attenuation_limits():
    """
    AI Bug: AI hallucinated that 10GBASE-SR (OM4 MMF) could reach 28 km by applying linear copper loss.
    Defense: Any link > 400m must reject OM4 and mandate OS2 Single-Mode Fiber (10GBASE-LR/ER).
    """
    metro_link = LinkRequest(
        link_id="LINK-FINTECH-METRO",
        source="HQ",
        destination="Colo",
        distance_meters=28_000.0,  # 28 km
        medium_preference=MediumPreference.AUTO,
        role="Metro",
    )
    rec = L1L2MediaEngine.evaluate_link(metro_link)

    # Must be OS2 Single-Mode Fiber with 10GBASE-ER (1550nm)
    assert "OM4" not in rec.medium_type
    assert "OS2" in rec.medium_type
    assert rec.standard == "10GBASE-ER"
    assert rec.wavelength_nm == 1550

