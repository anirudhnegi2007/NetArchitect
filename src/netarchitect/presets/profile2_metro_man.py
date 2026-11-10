"""
Profile 2: Metro MAN Preset Scenario.
Scale: HQ + 2 Remote Sites (15-35km), 450 users, FinTech Colocation.
Focus: OS2 SMF (10GBASE-LR/ER), EVPL, Sub-5ms QoS, dual-homed failover ring.
"""

from netarchitect.models.scenario_inputs import (
    ScenarioInput,
    LinkRequest,
    SubnetRequest,
    MediumPreference,
    SecurityZone,
    ResiliencyMode,
)


def get_metro_man_scenario() -> ScenarioInput:
    return ScenarioInput(
        id="metro-man",
        name="Profile 2: Metro MAN (FinTech & Data Center)",
        description=(
            "Metropolitan Area Network interconnecting Financial Corporate HQ with two primary colocation facilities. "
            "Requires OS2 Single-Mode Fiber operating at 1550nm for spans exceeding 10 km, strict sub-5ms latency QoS, "
            "and dual-homed resilient failover ring with single-area OSPF fast convergence."
        ),
        root_network="172.16.0.0/12",
        resiliency_mode=ResiliencyMode.DUAL_HOMED_RSTP,
        autonomous_system_number=65002,
        links=[
            LinkRequest(
                link_id="LINK-METRO-HQ-COLO-A",
                source="HQ-FinTech-Core",
                destination="Colo-A-Equinix",
                distance_meters=18_500.0,
                bandwidth_gbps=10.0,
                medium_preference=MediumPreference.FIBER,
                role="Metro",
            ),
            LinkRequest(
                link_id="LINK-METRO-HQ-COLO-B",
                source="HQ-FinTech-Core",
                destination="Colo-B-Interxion",
                distance_meters=32_400.0,
                bandwidth_gbps=10.0,
                medium_preference=MediumPreference.FIBER,
                role="Metro",
            ),
            LinkRequest(
                link_id="LINK-METRO-RING-COLOA-COLOB",
                source="Colo-A-Equinix",
                destination="Colo-B-Interxion",
                distance_meters=24_000.0,
                bandwidth_gbps=10.0,
                medium_preference=MediumPreference.FIBER,
                role="Metro",
            ),
        ],
        subnets=[
            SubnetRequest(
                name="HQ_Corporate_Financial_Staff",
                required_hosts=200,
                vlan_id=110,
                security_zone=SecurityZone.INTERNAL,
                description="HQ Trading floor, compliance, legal, and executive terminals",
            ),
            SubnetRequest(
                name="ColoA_High_Frequency_Trading",
                required_hosts=120,
                vlan_id=120,
                security_zone=SecurityZone.FINTECH,
                description="Direct market feed servers, order matching engines, FPGA trade executors",
            ),
            SubnetRequest(
                name="ColoB_Clearing_Risk_Analytics",
                required_hosts=80,
                vlan_id=130,
                security_zone=SecurityZone.FINTECH,
                description="Post-trade clearing, risk calculation clusters, and backup order books",
            ),
            SubnetRequest(
                name="Out_of_Band_Management_OOB",
                required_hosts=30,
                vlan_id=199,
                security_zone=SecurityZone.MANAGEMENT,
                description="Chassis IPMI, console servers, PDU monitoring, and out-of-band management",
            ),
            SubnetRequest(
                name="EVPL_Point_to_Point_Transit",
                required_hosts=20,
                vlan_id=200,
                security_zone=SecurityZone.INTERNAL,
                description="Metro transit point-to-point links between core routers and EVPL providers",
            ),
        ],
    )

