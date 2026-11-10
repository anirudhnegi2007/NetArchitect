"""
Unit tests for Layer 3 Bitwise VLSM Subnet Allocator.
Covers wildcard mask calculations across edge-case subnets, address space exhaustion
boundaries, descending sort packing, and strict non-overlap mathematical invariants.
"""

import ipaddress
import pytest
from netarchitect.models.scenario_inputs import SubnetRequest, SecurityZone
from netarchitect.models.architecture_outputs import SubnetAllocation
from netarchitect.engines.vlsm_subnet_allocator import BitwiseVLSMAllocator
from netarchitect.exceptions import AddressSpaceExhaustionError, SubnetOverlapError


@pytest.mark.parametrize(
    "required_hosts,expected_prefix,expected_netmask,expected_wildcard,expected_usable",
    [
        (1, 30, "255.255.255.252", "0.0.0.3", 2),
        (2, 30, "255.255.255.252", "0.0.0.3", 2),
        (3, 29, "255.255.255.248", "0.0.0.7", 6),
        (6, 29, "255.255.255.248", "0.0.0.7", 6),
        (7, 28, "255.255.255.240", "0.0.0.15", 14),
        (14, 28, "255.255.255.240", "0.0.0.15", 14),
        (15, 27, "255.255.255.224", "0.0.0.31", 30),
        (30, 27, "255.255.255.224", "0.0.0.31", 30),
        (31, 26, "255.255.255.192", "0.0.0.63", 62),
        (62, 26, "255.255.255.192", "0.0.0.63", 62),
        (63, 25, "255.255.255.128", "0.0.0.127", 126),
        (126, 25, "255.255.255.128", "0.0.0.127", 126),
        (127, 24, "255.255.255.0", "0.0.0.255", 254),
        (254, 24, "255.255.255.0", "0.0.0.255", 254),
        (255, 23, "255.255.254.0", "0.0.1.255", 510),
        (510, 23, "255.255.254.0", "0.0.1.255", 510),
        (511, 22, "255.255.252.0", "0.0.3.255", 1022),
        (1022, 22, "255.255.252.0", "0.0.3.255", 1022),
        (4094, 20, "255.255.240.0", "0.0.15.255", 4094),
        (16382, 18, "255.255.192.0", "0.0.63.255", 16382),
        (65534, 16, "255.255.0.0", "0.0.255.255", 65534),
    ],
)
def test_wildcard_masks_and_prefixes_across_edge_case_subnets(
    required_hosts, expected_prefix, expected_netmask, expected_wildcard, expected_usable
):
    subnets = [SubnetRequest(name="EdgeSubnet", required_hosts=required_hosts, vlan_id=10)]
    allocations, _, _, _ = BitwiseVLSMAllocator.allocate("10.0.0.0/8", subnets)

    alloc = allocations[0]
    assert alloc.prefix_length == expected_prefix
    assert alloc.netmask == expected_netmask
    assert alloc.wildcard_mask == expected_wildcard
    assert alloc.allocated_hosts == expected_usable

    mask_int = int(ipaddress.IPv4Address(alloc.netmask))
    wildcard_int = int(ipaddress.IPv4Address(alloc.wildcard_mask))
    net_int = int(ipaddress.IPv4Address(alloc.network_address))
    assert (mask_int ^ 0xFFFFFFFF) == wildcard_int
    assert (mask_int & wildcard_int) == 0
    assert (net_int & wildcard_int) == 0


def test_vlsm_non_overlapping_allocations_across_mixed_sizes():
    subnets = [
        SubnetRequest(name="P2P-Link-1", required_hosts=2, vlan_id=60),
        SubnetRequest(name="Campus-Core", required_hosts=500, vlan_id=10),
        SubnetRequest(name="IoT-Sensors", required_hosts=62, vlan_id=40),
        SubnetRequest(name="Student-WiFi", required_hosts=1000, vlan_id=20),
        SubnetRequest(name="Faculty", required_hosts=250, vlan_id=30),
        SubnetRequest(name="Mgmt-OOB", required_hosts=14, vlan_id=50),
        SubnetRequest(name="P2P-Link-2", required_hosts=2, vlan_id=70),
    ]

    allocations, total_avail, total_alloc, eff = BitwiseVLSMAllocator.allocate("10.50.0.0/16", subnets)
    assert len(allocations) == 7
    assert total_avail == 65536
    assert total_alloc > 0
    assert 0 < eff <= 100.0

    intervals = []
    for a in allocations:
        net = ipaddress.IPv4Network(a.cidr)
        start = int(net.network_address)
        end = start + net.num_addresses - 1
        intervals.append((start, end, a.cidr))

    for i in range(len(intervals)):
        for j in range(i + 1, len(intervals)):
            s1, e1, c1 = intervals[i]
            s2, e2, c2 = intervals[j]
            assert (e1 < s2 or e2 < s1), f"Subnets {c1} and {c2} overlap!"


def test_vlsm_descending_sort_order_prevents_fragmentation():
    subnets = [
        SubnetRequest(name="Small", required_hosts=5, vlan_id=10),
        SubnetRequest(name="Huge", required_hosts=1000, vlan_id=20),
        SubnetRequest(name="Medium", required_hosts=200, vlan_id=30),
    ]
    allocations, _, _, _ = BitwiseVLSMAllocator.allocate("172.20.0.0/16", subnets)
    assert [a.name for a in allocations] == ["Huge", "Medium", "Small"]
    assert allocations[0].prefix_length == 22


def test_exact_slash24_capacity_fit_254_hosts():
    exact_fit = [SubnetRequest(name="Full-24", required_hosts=254, vlan_id=10)]
    allocs, total_avail, total_alloc, _ = BitwiseVLSMAllocator.allocate("192.168.1.0/24", exact_fit)
    assert len(allocs) == 1
    assert allocs[0].cidr == "192.168.1.0/24"
    assert total_avail == total_alloc == 256


def test_single_host_overflow_raises_address_space_exhaustion():
    split_overflow = [
        SubnetRequest(name="Half-A", required_hosts=126, vlan_id=10),
        SubnetRequest(name="Half-B", required_hosts=126, vlan_id=20),
        SubnetRequest(name="Overflow-P2P", required_hosts=2, vlan_id=30),
    ]
    with pytest.raises(AddressSpaceExhaustionError) as exc_info:
        BitwiseVLSMAllocator.allocate("192.168.1.0/24", split_overflow)
    assert exc_info.value.root_prefix == "192.168.1.0/24"

    single_host_overflow = [SubnetRequest(name="Too-Big-By-1", required_hosts=255, vlan_id=10)]
    with pytest.raises(AddressSpaceExhaustionError):
        BitwiseVLSMAllocator.allocate("192.168.1.0/24", single_host_overflow)


def test_slash16_exhaustion_with_large_host_demand():
    subnets = [SubnetRequest(name="Massive-Subnet", required_hosts=70_000, vlan_id=10)]
    with pytest.raises(AddressSpaceExhaustionError) as exc_info:
        BitwiseVLSMAllocator.allocate("10.0.0.0/16", subnets)
    assert exc_info.value.available_hosts == 65534
    assert exc_info.value.required_hosts == 70000


def test_empty_subnet_requests_handled_gracefully():
    allocs, avail, alloc_ips, eff = BitwiseVLSMAllocator.allocate("10.0.0.0/24", [])
    assert allocs == []
    assert avail == 256
    assert alloc_ips == 0
    assert eff == 0.0


def test_overlap_detector_catches_intersecting_cidrs():
    s1 = SubnetAllocation(
        name="A", vlan_id=10, security_zone=SecurityZone.INTERNAL,
        required_hosts=100, allocated_hosts=126, cidr="10.0.0.0/25",
        network_address="10.0.0.0", prefix_length=25, netmask="255.255.255.128",
        wildcard_mask="0.0.0.127", default_gateway="10.0.0.1",
        first_usable_ip="10.0.0.2", last_usable_ip="10.0.0.126",
        broadcast_address="10.0.0.127", efficiency_pct=79.37, rationale="test"
    )
    s2 = SubnetAllocation(
        name="B", vlan_id=20, security_zone=SecurityZone.INTERNAL,
        required_hosts=50, allocated_hosts=62, cidr="10.0.0.64/26",
        network_address="10.0.0.64", prefix_length=26, netmask="255.255.255.192",
        wildcard_mask="0.0.0.63", default_gateway="10.0.0.65",
        first_usable_ip="10.0.0.66", last_usable_ip="10.0.0.126",
        broadcast_address="10.0.0.127", efficiency_pct=80.65, rationale="test"
    )
    with pytest.raises(SubnetOverlapError):
        BitwiseVLSMAllocator.verify_non_overlapping([s1, s2])
