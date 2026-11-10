"""
Preset Scenario Registry.
Provides access and enumeration of the three preset profiles.
"""

from typing import Dict, List, Optional

from netarchitect.models.scenario_inputs import ScenarioInput
from netarchitect.presets.profile1_campus_lan import get_campus_lan_scenario
from netarchitect.presets.profile2_metro_man import get_metro_man_scenario
from netarchitect.presets.profile3_global_wan import get_global_wan_scenario


class PresetRegistry:
    """Registry maintaining references to all built-in enterprise network profiles."""

    @classmethod
    def get_all(cls) -> List[ScenarioInput]:
        return [
            get_campus_lan_scenario(),
            get_metro_man_scenario(),
            get_global_wan_scenario(),
        ]

    @classmethod
    def get_by_id(cls, scenario_id: str) -> Optional[ScenarioInput]:
        normalized = scenario_id.strip().lower().replace("_", "-")
        for sc in cls.get_all():
            if sc.id == normalized:
                return sc
        return None

    @classmethod
    def as_dict(cls) -> Dict[str, ScenarioInput]:
        return {sc.id: sc for sc in cls.get_all()}

