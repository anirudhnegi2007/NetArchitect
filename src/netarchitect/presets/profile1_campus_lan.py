"""
Profile 1: Enterprise Campus LAN Preset Scenario.
Scale: 3 Buildings, <400m reach, 1,600 endpoints, PoE Access Points.
Focus: Cat6a vs OM4 MMF, 802.1Q VLANs, Rapid-PVST (RSTP), Single-Area OSPF Area 0.
"""

from netarchitect.models.scenario_inputs import (
    LinkRequest,
    MediumPreference,
    ResiliencyMode,
    ScenarioInput,
    SecurityZone,
    SubnetRequest,
)


def get_campus_lan_scenario() -> ScenarioInput:
    return ScenarioInput(
        id="campus-lan",
        name="Profile 1: Enterprise Campus LAN",
        description=(
            "Multi-building enterprise campus comprising Core Administration, Academic Classrooms, "
            "and Student Residential Facilities. Enforces IEEE 802.3an Cat6a for horizontal distribution, "
            "OM4 multimode fiber for building uplinks, 802.1Q trunking, RSTP loop prevention, and OSPF Area 0."
        ),
        root_network="10.10.0.0/16",
        resiliency_mode=ResiliencyMode.DUAL_HOMED_RSTP,
        autonomous_system_number=65001,
        links=[
            LinkRequest(
                link_id="LINK-HORIZ-BLDGA",
                source="BldgA-IDFEAST",
                destination="BldgA-PoE-APs",
                distance_meters=65.0,
                bandwidth_gbps=10.0,
                medium_preference=MediumPreference.COPPER,
                role="Access",
            ),
            LinkRequest(
                link_id="LINK-HORIZ-BLDGB",
                source="BldgB-IDFWEST",
                destination="BldgB-Endpoints",
                distance_meters=85.0,
                bandwidth_gbps=10.0,
                medium_preference=MediumPreference.COPPER,
                role="Access",
            ),
            LinkRequest(
                link_id="LINK-HORIZ-BLDGC",
                source="BldgC-IDFRES",
                destination="BldgC-DormAPs",
                distance_meters=90.0,
                bandwidth_gbps=10.0,
                medium_preference=MediumPreference.COPPER,
                role="Access",
            ),
            LinkRequest(
                link_id="LINK-BACKBONE-CORE-BLDGB",
                source="Campus-MDF-Core",
                destination="BldgB-Dist-Switch",
                distance_meters=280.0,
                bandwidth_gbps=10.0,
                medium_preference=MediumPreference.AUTO,
                role="Backbone",
            ),
            LinkRequest(
                link_id="LINK-BACKBONE-CORE-BLDGC",
                source="Campus-MDF-Core",
                destination="BldgC-Dist-Switch",
                distance_meters=375.0,
                bandwidth_gbps=10.0,
                medium_preference=MediumPreference.AUTO,
                role="Backbone",
            ),
        ],
        subnets=[
            SubnetRequest(
                name="Student_Residential_WiFi",
                required_hosts=600,
                vlan_id=30,
                security_zone=SecurityZone.INTERNAL,
                description="High-density Wi-Fi 6 wireless access points in dormitories",
            ),
            SubnetRequest(
                name="Academic_Labs_Workstations",
                required_hosts=500,
                vlan_id=20,
                security_zone=SecurityZone.INTERNAL,
                description="Computer Science, Engineering, and General Academic computer labs",
            ),
            SubnetRequest(
                name="Faculty_Administration",
                required_hosts=300,
                vlan_id=10,
                security_zone=SecurityZone.MANAGEMENT,
                description="Faculty offices, administration, registrar, and financial servers",
            ),
            SubnetRequest(
                name="Campus_VoIP_Telephony",
                required_hosts=150,
                vlan_id=40,
                security_zone=SecurityZone.VOIP,
                description="Dedicated VLAN for Cisco IP Phones and SIP signaling",
            ),
            SubnetRequest(
                name="Facility_IoT_HVAC_Security",
                required_hosts=50,
                vlan_id=50,
                security_zone=SecurityZone.IOT,
                description="Environmental sensors, badge readers, and IP surveillance cameras",
            ),
        ],
    )

