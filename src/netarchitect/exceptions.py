"""
NetArchitect Exception Hierarchy.
Defines strongly-typed, domain-specific networking exceptions ensuring resilient
error handling and graceful degradation per the Ponytail clean architecture pattern.
"""

class NetArchitectError(Exception):
    """Base exception for all NetArchitect domain errors."""
    pass


class PhysicalDistanceViolationError(NetArchitectError):
    """
    Raised when requested physical transmission medium exceeds IEEE 802.3
    standard attenuation or modal dispersion limits.
    """
    def __init__(self, message: str, distance_meters: float, medium: str, max_allowed_meters: float):
        super().__init__(message)
        self.distance_meters = distance_meters
        self.medium = medium
        self.max_allowed_meters = max_allowed_meters


class AddressSpaceExhaustionError(NetArchitectError):
    """
    Raised when requested host capacities exceed the total addressable space
    of the assigned root IPv4 network prefix.
    """
    def __init__(self, message: str, required_hosts: int, available_hosts: int, root_prefix: str):
        super().__init__(message)
        self.required_hosts = required_hosts
        self.available_hosts = available_hosts
        self.root_prefix = root_prefix


class SubnetOverlapError(NetArchitectError):
    """
    Raised when an algorithmic allocation error produces overlapping subnet ranges.
    """
    def __init__(self, message: str, subnet_a: str, subnet_b: str):
        super().__init__(message)
        self.subnet_a = subnet_a
        self.subnet_b = subnet_b


class InvalidCIDRError(NetArchitectError, ValueError):
    """Raised when an IPv4 CIDR string is malformed or not RFC 1918 compliant."""
    pass


class ScenarioValidationError(NetArchitectError, ValueError):
    """Raised when scenario parameters fail physical or logical validation rules."""
    pass

