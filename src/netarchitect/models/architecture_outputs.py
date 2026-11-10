"""
Output Data Contracts & Result Models.
Defines strongly-typed output models for recommendation reports, subnet plans,
and Cisco IOS configuration bundles.
"""

from typing import List

from pydantic import BaseModel, Field

from netarchitect.models.scenario_inputs import SecurityZone


class MediaRecommendation(BaseModel):
    link_id: str
    source: str
    destination: str
    distance_meters: float
    bandwidth_gbps: float
    medium_type: str
    standard: str
    wavelength_nm: int
    max_reach_meters: float
    attenuation_db_est: float
    rationale: str


class SubnetAllocation(BaseModel):
    name: str
    vlan_id: int
    security_zone: SecurityZone
    required_hosts: int
    allocated_hosts: int
    cidr: str
    network_address: str
    prefix_length: int
    netmask: str
    wildcard_mask: str
    default_gateway: str
    first_usable_ip: str
    last_usable_ip: str
    broadcast_address: str
    efficiency_pct: float
    rationale: str


class RoutingRecommendation(BaseModel):
    protocol: str
    autonomous_system: int
    topology_tier: str
    summary_routes: List[str] = Field(default_factory=list)
    convergence_profile: str
    rationale: str
    rfc_citation: str


class DeviceConfig(BaseModel):
    hostname: str
    device_role: str
    config_text: str


class PlanResult(BaseModel):
    scenario_id: str
    scenario_name: str
    timestamp: str
    root_network: str
    total_available_ips: int
    total_allocated_ips: int
    total_usable_hosts: int
    overall_efficiency_pct: float
    media_recommendations: List[MediaRecommendation]
    subnet_allocations: List[SubnetAllocation]
    routing_recommendation: RoutingRecommendation
    device_configs: List[DeviceConfig]
    unified_cisco_config: str
    executive_rationales: List[str]

