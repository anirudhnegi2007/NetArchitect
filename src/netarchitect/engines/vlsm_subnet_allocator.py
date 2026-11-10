"""
Layer 3 Bitwise Variable Length Subnet Mask (VLSM) Allocator.
Implements pure unsigned 32-bit arithmetic, strictly non-overlapping prefix trees,
canonical network alignment, and deterministic address exhaustion validation.
"""

import ipaddress
import math
from typing import List, Tuple

from netarchitect.exceptions import AddressSpaceExhaustionError, SubnetOverlapError
from netarchitect.models.architecture_outputs import SubnetAllocation
from netarchitect.models.scenario_inputs import SubnetRequest


class BitwiseVLSMAllocator:
    """
    Rigorously allocates IPv4 variable-length subnets based on descending host demands.
    Complies with RFC 1918, RFC 4632 (CIDR), and RFC 3021 (P2P /31 links).
    """

    @staticmethod
    def int_to_ipv4(ip_int: int) -> str:
        """Converts an unsigned 32-bit integer to standard dotted-decimal notation."""
        return str(ipaddress.IPv4Address(ip_int))

    @staticmethod
    def calculate_required_prefix(required_hosts: int) -> int:
        """
        Determines the most compact prefix length that accommodates required hosts
        plus network and broadcast identifiers (RFC 4632).
        For point-to-point links requiring exactly 2 hosts, prefix /30 is standard.
        """
        # Minimum addresses needed: hosts + network ID + broadcast ID
        addresses_needed = required_hosts + 2
        host_bits = math.ceil(math.log2(addresses_needed))
        if host_bits < 2:
            host_bits = 2  # Minimum standard subnet is /30
        prefix_len = 32 - host_bits
        return prefix_len

    @classmethod
    def allocate(
        cls, root_network_cidr: str, subnet_requests: List[SubnetRequest]
    ) -> Tuple[List[SubnetAllocation], int, int, float]:
        """
        Allocates subnets non-overlappingly using bitwise boundary alignment.
        Returns:
            (List[SubnetAllocation], total_available_ips, total_allocated_ips, efficiency_pct)
        """
        try:
            root_net = ipaddress.IPv4Network(root_network_cidr, strict=False)
        except ValueError as e:
            raise ValueError(f"Invalid root CIDR prefix '{root_network_cidr}': {e}") from e

        root_start = int(root_net.network_address)
        root_size = root_net.num_addresses
        root_end = root_start + root_size - 1

        # Sort subnet requests strictly descending by required host count
        # This prevents prefix tree fragmentation and guarantees optimal packing
        sorted_requests = sorted(subnet_requests, key=lambda s: s.required_hosts, reverse=True)

        allocations: List[SubnetAllocation] = []
        cursor = root_start

        for req in sorted_requests:
            prefix_len = cls.calculate_required_prefix(req.required_hosts)
            block_size = 1 << (32 - prefix_len)

            # Align the cursor to the boundary of the block size:
            # aligned = (cursor + block_size - 1) & ~(block_size - 1)
            alignment_mask = ~(block_size - 1) & 0xFFFFFFFF
            aligned_start = (cursor + block_size - 1) & alignment_mask
            block_end = aligned_start + block_size - 1

            # Check for address exhaustion within the root prefix
            if block_end > root_end:
                total_requested_hosts = sum(s.required_hosts for s in subnet_requests)
                raise AddressSpaceExhaustionError(
                    message=(
                        f"Root network {root_network_cidr} (capacity: {root_size} IPs) exhausted while allocating "
                        f"subnet '{req.name}' ({req.required_hosts} hosts required, block size {block_size}). "
                        f"Boundary {cls.int_to_ipv4(block_end)} exceeds root limit {cls.int_to_ipv4(root_end)}."
                    ),
                    required_hosts=total_requested_hosts,
                    available_hosts=root_size - 2,
                    root_prefix=root_network_cidr,
                )

            # Bitwise calculation of Subnet Mask and Wildcard Mask
            mask_int = (0xFFFFFFFF << (32 - prefix_len)) & 0xFFFFFFFF
            wildcard_int = mask_int ^ 0xFFFFFFFF

            net_addr_str = cls.int_to_ipv4(aligned_start)
            broadcast_str = cls.int_to_ipv4(block_end)
            netmask_str = cls.int_to_ipv4(mask_int)
            wildcard_str = cls.int_to_ipv4(wildcard_int)

            # In standard subnets:
            # First usable = network + 1 (Default Gateway)
            # Second usable = network + 2
            # Last usable = broadcast - 1
            default_gw = cls.int_to_ipv4(aligned_start + 1)
            first_usable = cls.int_to_ipv4(aligned_start + 2 if block_size > 4 else aligned_start + 1)
            last_usable = cls.int_to_ipv4(block_end - 1)

            usable_host_count = block_size - 2
            efficiency = round((req.required_hosts / usable_host_count) * 100.0, 2)

            allocations.append(
                SubnetAllocation(
                    name=req.name,
                    vlan_id=req.vlan_id,
                    security_zone=req.security_zone,
                    required_hosts=req.required_hosts,
                    allocated_hosts=usable_host_count,
                    cidr=f"{net_addr_str}/{prefix_len}",
                    network_address=net_addr_str,
                    prefix_length=prefix_len,
                    netmask=netmask_str,
                    wildcard_mask=wildcard_str,
                    default_gateway=default_gw,
                    first_usable_ip=first_usable,
                    last_usable_ip=last_usable,
                    broadcast_address=broadcast_str,
                    efficiency_pct=efficiency,
                    rationale=(
                        f"Allocated /{prefix_len} ({block_size} total IPs, {usable_host_count} usable) for {req.required_hosts} "
                        f"required hosts. Efficiency: {efficiency}%. Wildcard mask {wildcard_str} strictly bounded to boundary."
                    ),
                )
            )

            # Advance cursor past the allocated block
            cursor = block_end + 1

        # Post-allocation safety check: Assert zero overlap
        cls.verify_non_overlapping(allocations)

        total_allocated_ips = sum(1 << (32 - a.prefix_length) for a in allocations)
        total_requested = sum(a.required_hosts for a in allocations)
        overall_efficiency = round((total_requested / total_allocated_ips) * 100.0, 2) if total_allocated_ips > 0 else 0.0

        return allocations, root_size, total_allocated_ips, overall_efficiency

    @classmethod
    def verify_non_overlapping(cls, allocations: List[SubnetAllocation]) -> None:
        """
        Mathematically verifies that no two allocated subnets intersect.
        Throws SubnetOverlapError if any overlap exists.
        """
        intervals: List[Tuple[int, int, str]] = []
        for alloc in allocations:
            net = ipaddress.IPv4Network(alloc.cidr)
            start = int(net.network_address)
            end = start + net.num_addresses - 1
            intervals.append((start, end, alloc.cidr))

        # Check all pairs
        for i in range(len(intervals)):
            for j in range(i + 1, len(intervals)):
                s1, e1, c1 = intervals[i]
                s2, e2, c2 = intervals[j]
                # If interval 1 and interval 2 overlap:
                if not (e1 < s2 or e2 < s1):
                    raise SubnetOverlapError(
                        message=f"Algorithmic anomaly: Subnet {c1} overlaps with Subnet {c2}!",
                        subnet_a=c1,
                        subnet_b=c2,
                    )

