"""
Input Data Contracts & Schemas (Pydantic v2).
Ensures end-to-end type safety, validation boundaries, and serialization per Ponytail.
"""

from enum import Enum
from typing import List, Optional
import ipaddress
from pydantic import BaseModel, Field, field_validator, model_validator
from netarchitect.exceptions import InvalidCIDRError, ScenarioValidationError


class MediumPreference(str, Enum):
    AUTO = "AUTO"
    COPPER = "COPPER"
    FIBER = "FIBER"


class SecurityZone(str, Enum):
    INTERNAL = "INTERNAL"
    GUEST = "GUEST"
    VOIP = "VOIP"
    DMZ = "DMZ"
    MANAGEMENT = "MANAGEMENT"
    FINTECH = "FINTECH"
    IOT = "IOT"


class ResiliencyMode(str, Enum):
    SINGLE_HOMED = "SINGLE_HOMED"
    DUAL_HOMED_RSTP = "DUAL_HOMED_RSTP"
    MULTI_CLOUD_HA = "MULTI_CLOUD_HA"


class LinkRequest(BaseModel):
    link_id: str = Field(default="LINK-01", description="Unique link identifier (e.g. LINK-CORE-BLDGB)")
    source: str = Field(default="Core-Node", description="Origin node/site")
    destination: str = Field(default="Remote-Node", description="Destination node/site")
    distance_meters: float = Field(..., gt=0, description="Link distance in meters")
    bandwidth_gbps: float = Field(default=10.0, gt=0, description="Target link bandwidth in Gbps")
    medium_preference: MediumPreference = Field(default=MediumPreference.AUTO)
    role: str = Field(default="Backbone", description="Role: Access, Backbone, Metro, WAN")

    @field_validator("medium_preference", mode="before")
    @classmethod
    def normalize_medium_pref(cls, v):
        if isinstance(v, str):
            return v.strip().upper()
        return v


class SubnetRequest(BaseModel):
    name: str = Field(..., description="Descriptive subnet name (e.g. Faculty_Workstations)")
    required_hosts: int = Field(..., ge=1, description="Number of usable IPv4 host endpoints required")
    vlan_id: int = Field(..., ge=1, le=4094, description="IEEE 802.1Q VLAN ID (1-4094)")
    security_zone: SecurityZone = Field(default=SecurityZone.INTERNAL)
    description: Optional[str] = Field(default=None, description="Optional administrative summary")

    @field_validator("security_zone", mode="before")
    @classmethod
    def normalize_security_zone(cls, v):
        if isinstance(v, str):
            return v.strip().upper()
        return v


class ScenarioInput(BaseModel):
    id: str = Field(default="custom-scenario", description="Unique slug for the scenario (e.g. campus-lan)")
    name: str = Field(default="Custom Network Scenario", description="Human-readable title")
    description: str = Field(default="Custom user-defined enterprise network architecture", description="Contextual scenario description")
    root_network: str = Field(..., description="IPv4 root CIDR (e.g. 10.10.0.0/16)")
    resiliency_mode: ResiliencyMode = Field(default=ResiliencyMode.DUAL_HOMED_RSTP)
    links: List[LinkRequest] = Field(default_factory=list)
    subnets: List[SubnetRequest] = Field(default_factory=list)
    autonomous_system_number: int = Field(default=65001, ge=1, le=65534)

    @field_validator("resiliency_mode", mode="before")
    @classmethod
    def normalize_resiliency(cls, v):
        if isinstance(v, str):
            return v.strip().upper()
        return v

    @field_validator("root_network")
    @classmethod
    def validate_root_cidr(cls, v: str) -> str:
        try:
            net = ipaddress.IPv4Network(v, strict=False)
            return str(net)
        except ValueError as e:
            raise InvalidCIDRError(f"Invalid IPv4 root prefix '{v}': {e}") from e

    @model_validator(mode="after")
    def validate_uniqueness(self) -> "ScenarioInput":
        vlan_ids = set()
        for s in self.subnets:
            if s.vlan_id in vlan_ids:
                raise ScenarioValidationError(f"Duplicate VLAN ID detected: {s.vlan_id} in subnet '{s.name}'")
            vlan_ids.add(s.vlan_id)
        
        link_ids = set()
        for link in self.links:
            if link.link_id in link_ids:
                raise ScenarioValidationError(f"Duplicate Link ID detected: '{link.link_id}'")
            link_ids.add(link.link_id)

        return self

