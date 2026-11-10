"""
Unit tests for Cisco IOS Configuration Synthesizer.
Verifies Core Switch SVIs, Access Switch PortFast/BPDU Guard, Router ACLs,
eBGP blocks, and non-octet boundary interface IP assignment.
"""

from netarchitect.models.scenario_inputs import ScenarioInput, SubnetRequest
from netarchitect.network_planner import NetworkPlanner
from netarchitect.presets.profile1_campus_lan import get_campus_lan_scenario
from netarchitect.presets.profile3_global_wan import get_global_wan_scenario


def test_core_switch_svi_and_ospf_network_statements():
    sc = get_campus_lan_scenario()
    plan = NetworkPlanner.execute_plan(sc)

    core_sw = next(d for d in plan.device_configs if d.device_role == "Core-Switch")
    cfg = core_sw.config_text

    assert "ip routing" in cfg
    assert "vtp mode transparent" in cfg
    assert "spanning-tree mode rapid-pvst" in cfg
    assert "spanning-tree guard root" in cfg

    for subnet in plan.subnet_allocations:
        assert f"interface Vlan{subnet.vlan_id}" in cfg
        assert f"ip address {subnet.default_gateway} {subnet.netmask}" in cfg
        assert f"network {subnet.network_address} {subnet.wildcard_mask} area 0" in cfg


def test_access_switch_portfast_bpduguard_and_trunk_security():
    sc = get_campus_lan_scenario()
    plan = NetworkPlanner.execute_plan(sc)

    acc_sw = next(d for d in plan.device_configs if d.device_role == "Access-Switch")
    cfg = acc_sw.config_text

    assert "switchport nonegotiate" in cfg
    assert "switchport trunk native vlan 999" in cfg
    assert "switchport trunk encapsulation dot1q" not in cfg  # Catalyst 2960 compatibility
    assert "spanning-tree portfast" in cfg
    assert "spanning-tree bpduguard enable" in cfg

    # Verify unified config uses valid IOS '!' comments and distinct OSPF router-ids
    assert "########" not in plan.unified_cisco_config
    core_sw = next(d for d in plan.device_configs if d.device_role == "Core-Switch").config_text
    router = next(d for d in plan.device_configs if d.device_role == "Core-Router").config_text
    assert "router-id 10.10.0.1" in core_sw
    assert "router-id 198.51.100.1" in router


def test_router_acl_and_wan_interface_emissions():
    sc = get_campus_lan_scenario()
    plan = NetworkPlanner.execute_plan(sc)

    router = next(d for d in plan.device_configs if d.device_role == "Core-Router")
    cfg = router.config_text

    assert "interface GigabitEthernet0/0/0" in cfg
    assert "interface GigabitEthernet0/0/1" in cfg
    assert "ip access-list extended ACL-ISOLATE-IOT-AND-GUEST" in cfg
    assert "permit tcp any any established" in cfg
    assert "router ospf 1" in cfg


def test_router_bgp_configuration_for_global_wan():
    sc = get_global_wan_scenario()
    plan = NetworkPlanner.execute_plan(sc)

    router = next(d for d in plan.device_configs if d.device_role == "Core-Router")
    cfg = router.config_text

    assert f"router bgp {sc.autonomous_system_number}" in cfg
    assert "neighbor 198.51.100.2 remote-as 65000" in cfg
    assert "network 10.200.0.0 mask 255.252.0.0" in cfg


def test_router_valid_ip_on_split_slash25_and_empty_subnets():
    sc_empty = ScenarioInput(
        id="empty-subnets-test",
        name="Empty Subnets",
        description="Edge case",
        root_network="172.16.0.0/20",
        links=[],
        subnets=[],
    )
    res_empty = NetworkPlanner.execute_plan(sc_empty)
    assert len(res_empty.device_configs) == 3

    sc_split = ScenarioInput(
        id="split-25-test",
        name="Split 25",
        description="Edge case",
        root_network="192.168.10.0/24",
        subnets=[
            SubnetRequest(name="Half-1", required_hosts=100, vlan_id=10),
            SubnetRequest(name="Half-2", required_hosts=100, vlan_id=20),
        ],
    )
    res_split = NetworkPlanner.execute_plan(sc_split)
    router_cfg = next(d for d in res_split.device_configs if d.device_role == "Core-Router").config_text
    assert "ip address 192.168.10.126 255.255.255.128" in router_cfg
