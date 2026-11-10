"""
NetArchitect Presets Package.
Exports preset scenarios and registry.
"""

from netarchitect.presets.preset_registry import PresetRegistry
from netarchitect.presets.profile1_campus_lan import get_campus_lan_scenario
from netarchitect.presets.profile2_metro_man import get_metro_man_scenario
from netarchitect.presets.profile3_global_wan import get_global_wan_scenario

__all__ = [
    "get_campus_lan_scenario",
    "get_metro_man_scenario",
    "get_global_wan_scenario",
    "PresetRegistry",
]

