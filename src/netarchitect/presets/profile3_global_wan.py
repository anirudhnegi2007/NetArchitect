"""
Profile 3: Global WAN Preset Scenario.
Scale: 4 Global Cities + Cloud VPC, 2,000 IoT / scanners.
Focus: IPsec VPN, Multi-Area OSPF/BGP, route summarization, edge isolation.
"""

from netarchitect.models.scenario_inputs import (
    ScenarioInput,
    LinkRequest,
    SubnetRequest,
    MediumPreference,
    SecurityZone,
    ResiliencyMode,
)


def get_global_wan_scenario() -> ScenarioInput:
    return ScenarioInput(
        id="global-wan",
        name="Profile 3: Global WAN (Multinational Logistics & Cloud VPC)",
        description=(
            "Multinational enterprise WAN interconnecting New York Headquarters, London, Tokyo, and Frankfurt "
            "distribution hubs with an AWS Cloud Transit Gateway. Supports 2,000 automated IoT barcode scanners, "
            "IPsec cryptographic encapsulation across the public WAN, Multi-Area OSPF with route summarization, "
            "and eBGP peering to cloud autonomous systems."
        ),
        root_network="10.200.0.0/14",
        resiliency_mode=ResiliencyMode.MULTI_CLOUD_HA,
        autonomous_system_number=65003,
        links=[
            LinkRequest(
                link_id="LINK-WAN-NYC-CLOUD-DIRECT",
                source="NYC-HQ-BorderRouter",
                destination="AWS-DirectConnect-GW",
                distance_meters=15_000.0,
                bandwidth_gbps=10.0,
                medium_preference=MediumPreference.FIBER,
                role="Metro",
            ),
            LinkRequest(
                link_id="LINK-WAN-NYC-LONDON",
                source="NYC-HQ-BorderRouter",
                destination="London-Hub-Router",
                distance_meters=5_580_000.0,  # Transatlantic fiber run (~5,580 km)
                bandwidth_gbps=10.0,
                medium_preference=MediumPreference.FIBER,
                role="WAN",
            ),
            LinkRequest(
                link_id="LINK-WAN-NYC-FRANKFURT",
                source="NYC-HQ-BorderRouter",
                destination="Frankfurt-Hub-Router",
                distance_meters=6_200_000.0,  # ~6,200 km
                bandwidth_gbps=10.0,
                medium_preference=MediumPreference.FIBER,
                role="WAN",
            ),
            LinkRequest(
                link_id="LINK-WAN-LONDON-TOKYO",
                source="London-Hub-Router",
                destination="Tokyo-Hub-Router",
                distance_meters=9_560_000.0,  # ~9,560 km
                bandwidth_gbps=10.0,
                medium_preference=MediumPreference.FIBER,
                role="WAN",
            ),
        ],
        subnets=[
            SubnetRequest(
                name="NYC_Logistics_Center_IoT",
                required_hosts=700,
                vlan_id=310,
                security_zone=SecurityZone.IOT,
                description="Automated conveyor sorters, RFID portal scanners, and robotic forklifts",
            ),
            SubnetRequest(
                name="London_Distribution_Scanners",
                required_hosts=450,
                vlan_id=320,
                security_zone=SecurityZone.IOT,
                description="Handheld ruggedized 2D barcode scanners and package dimensioners",
            ),
            SubnetRequest(
                name="Tokyo_Automated_Facility",
                required_hosts=400,
                vlan_id=330,
                security_zone=SecurityZone.IOT,
                description="Automated Storage and Retrieval Systems (ASRS) and AGV telemetry",
            ),
            SubnetRequest(
                name="Frankfurt_Regional_Hub",
                required_hosts=350,
                vlan_id=340,
                security_zone=SecurityZone.IOT,
                description="Cross-dock terminal telemetry, cargo weighbridges, and manifest terminals",
            ),
            SubnetRequest(
                name="AWS_Cloud_Transit_VPC",
                required_hosts=100,
                vlan_id=350,
                security_zone=SecurityZone.DMZ,
                description="Cloud backend tracking services, event ingestion microservices, and SAP ERP connector",
            ),
        ],
    )

