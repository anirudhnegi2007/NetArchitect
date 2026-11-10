"""
Structured JSON Exporter for NetArchitect.
Serializes recommendation plans, subnet mappings, and rationale trees into JSON.
"""

from pathlib import Path
from typing import Union

from netarchitect.models.architecture_outputs import PlanResult


class JSONExporter:
    """Exports PlanResult objects to formatted JSON strings or files on disk."""

    @staticmethod
    def to_json_str(plan_result: PlanResult, indent: int = 2) -> str:
        return plan_result.model_dump_json(indent=indent)

    @classmethod
    def save_to_file(cls, plan_result: PlanResult, destination_path: Union[str, Path]) -> Path:
        path = Path(destination_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        content = cls.to_json_str(plan_result)
        path.write_text(content, encoding="utf-8")
        return path

