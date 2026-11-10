"""
NetArchitect Main Planning Orchestrator.
Coordinates the end-to-end execution of L1/L2 media physics, L3 bitwise VLSM allocation,
routing protocol selection, explainable rationale synthesis, and Cisco IOS code emission.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Union

from netarchitect.engines.architectural_rationale_engine import ExplainabilityEngine
from netarchitect.engines.physical_media_engine import L1L2MediaEngine
from netarchitect.engines.routing_protocol_engine import RoutingProtocolEngine
from netarchitect.engines.vlsm_subnet_allocator import BitwiseVLSMAllocator
from netarchitect.exporters.cisco_ios_config_generator import CiscoIOSConfigSynthesizer
from netarchitect.exporters.plan_json_exporter import JSONExporter
from netarchitect.exporters.subnet_csv_exporter import CSVExporter
from netarchitect.models.architecture_outputs import PlanResult
from netarchitect.models.scenario_inputs import ScenarioInput


class NetworkPlanner:
    """
    Central orchestration facade conforming to the Ponytail architecture:
    Ingests -> Validates -> Computes Physics & Math -> Explains -> Synthesizes.
    """

    @classmethod
    def execute_plan(cls, scenario: ScenarioInput) -> PlanResult:
        # 1. Physical Layer Media & Distance Physics Engine
        media_recommendations = L1L2MediaEngine.evaluate_all(scenario.links)

        # 2. Layer 3 Bitwise Non-Overlapping VLSM Allocator
        (
            allocations,
            total_avail,
            total_alloc,
            efficiency_pct,
        ) = BitwiseVLSMAllocator.allocate(scenario.root_network, scenario.subnets)

        # 3. Routing Protocol Decision Engine
        routing_recommendation = RoutingProtocolEngine.evaluate_routing(scenario, allocations)

        # 4. Self-Explaining Architecture Rationale Engine
        executive_rationales = ExplainabilityEngine.generate_executive_rationales(
            scenario, media_recommendations, allocations, routing_recommendation
        )

        # 5. Cisco IOS Configuration Synthesis Engine
        device_configs = CiscoIOSConfigSynthesizer.synthesize_all(
            scenario, media_recommendations, allocations, routing_recommendation
        )
        unified_cisco = CiscoIOSConfigSynthesizer.generate_unified_config(device_configs)

        total_usable_hosts = sum(a.allocated_hosts for a in allocations)

        return PlanResult(
            scenario_id=scenario.id,
            scenario_name=scenario.name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            root_network=scenario.root_network,
            total_available_ips=total_avail,
            total_allocated_ips=total_alloc,
            total_usable_hosts=total_usable_hosts,
            overall_efficiency_pct=efficiency_pct,
            media_recommendations=media_recommendations,
            subnet_allocations=allocations,
            routing_recommendation=routing_recommendation,
            device_configs=device_configs,
            unified_cisco_config=unified_cisco,
            executive_rationales=executive_rationales,
        )

    @classmethod
    def export_verification_artifacts(
        cls, plan_result: PlanResult, output_dir: Union[str, Path] = "exports"
    ) -> Path:
        """
        Exports deployment-ready Cisco IOS .cfg scripts, JSON architecture plans,
        and VLSM subnet CSV tables for Packet Tracer, GNS3, and grading verification.
        """
        target_dir = Path(output_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        preset_slug_map = {
            "campus-lan": "profile1_campus_lan",
            "metro-man": "profile2_metro_man",
            "global-wan": "profile3_global_wan",
        }
        base_name = preset_slug_map.get(
            plan_result.scenario_id, plan_result.scenario_id.replace("-", "_")
        )

        # Write unified Cisco IOS configuration
        cfg_path = target_dir / f"{base_name}.cfg"
        cfg_path.write_text(plan_result.unified_cisco_config, encoding="utf-8")

        # Write structured JSON architecture plan
        json_path = target_dir / f"{base_name}_plan.json"
        JSONExporter.save_to_file(plan_result, json_path)

        # Write tabular CSV subnet allocation table
        csv_path = target_dir / f"{base_name}_subnets.csv"
        CSVExporter.save_subnets_to_csv(plan_result.subnet_allocations, csv_path)

        return cfg_path

