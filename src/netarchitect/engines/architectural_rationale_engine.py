"""
Self-Explaining Architecture Engine.
Synthesizes natural-language engineering rationales grounded in IEEE standards,
IETF RFCs, and optical/electrical transmission physics.
"""

from typing import List
from netarchitect.models.scenario_inputs import ScenarioInput, ResiliencyMode
from netarchitect.models.architecture_outputs import (
    MediaRecommendation,
    SubnetAllocation,
    RoutingRecommendation,
)


class ExplainabilityEngine:
    """
    Produces dynamic, mathematically and standard-grounded explanations
    for all NetArchitect design choices.
    """

    @classmethod
    def generate_executive_rationales(
        cls,
        scenario: ScenarioInput,
        media_recs: List[MediaRecommendation],
        allocations: List[SubnetAllocation],
        routing_rec: RoutingRecommendation,
    ) -> List[str]:
        rationales: List[str] = []

        # 1. Media & Transmission Physics
        has_copper = any("Cat6a" in m.medium_type for m in media_recs)
        has_mmf = any("OM4" in m.medium_type for m in media_recs)
        has_smf = any("OS2" in m.medium_type for m in media_recs)

        media_summary_parts = []
        if has_copper:
            media_summary_parts.append("Cat6a 10GBASE-T for horizontal runs <=100m (IEEE 802.3an)")
        if has_mmf:
            media_summary_parts.append("OM4 MMF 10GBASE-SR for intra-campus backbone runs <=400m (850nm dispersion limit)")
        if has_smf:
            media_summary_parts.append("OS2 SMF 10GBASE-LR/ER for long-span inter-building and MAN runs (zero modal dispersion)")

        rationales.append(
            f"Physical Media Strategy: Deployed {', '.join(media_summary_parts)}. "
            f"All link selections strictly adhere to IEEE 802.3 attenuation and transceiver optical budgets."
        )

        # 2. Resiliency & Layer 2 Topology
        if scenario.resiliency_mode == ResiliencyMode.DUAL_HOMED_RSTP:
            rationales.append(
                "Layer 2 Resiliency: Enforced IEEE 802.1w Rapid Spanning Tree Protocol (Rapid PVST+). "
                "Provides sub-second failure recovery (<1s) via edge port fast transitions and direct proposal-agreement handshakes, "
                "eliminating legacy 802.1D 30-50s listening/learning delays."
            )
        elif scenario.resiliency_mode == ResiliencyMode.MULTI_CLOUD_HA:
            rationales.append(
                "Layer 2/3 Resiliency: Dual-homed redundant gateways running HSRP/VRRP active-standby virtual routing, "
                "coupled with IPsec VPN tunnel failover across secondary WAN uplinks."
            )
        else:
            rationales.append(
                "Layer 2 Topology: Cost-optimized single-homed switching topology with loop prevention and BPDU guard enabled."
            )

        # 3. VLSM Allocation & Bitwise Optimization
        total_ips = sum(1 << (32 - a.prefix_length) for a in allocations)
        total_hosts = sum(a.required_hosts for a in allocations)
        overall_eff = round((total_hosts / total_ips) * 100.0, 1) if total_ips > 0 else 0.0

        rationales.append(
            f"Subnetting & Addressing: Implemented descending bitwise VLSM allocation within {scenario.root_network}. "
            f"Allocated {len(allocations)} non-overlapping subnets ({total_ips} total addresses reserved, {total_hosts} active hosts) "
            f"achieving {overall_eff}% address space efficiency. All wildcard masks derived via bitwise unsigned negation."
        )

        # 4. Routing Engine Rationale
        rationales.append(
            f"Routing Architecture: {routing_rec.protocol}. {routing_rec.rationale} (Reference: {routing_rec.rfc_citation})."
        )

        return rationales

