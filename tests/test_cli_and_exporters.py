"""
Tests for Typer CLI Commands, File Exporters (CSV, JSON, CFG),
and Explainability Rationale Engine.
"""

import csv
import json

from typer.testing import CliRunner

from netarchitect.cli import app as cli_app
from netarchitect.exporters.plan_json_exporter import JSONExporter
from netarchitect.exporters.subnet_csv_exporter import CSVExporter
from netarchitect.network_planner import NetworkPlanner
from netarchitect.presets.profile1_campus_lan import get_campus_lan_scenario

runner = CliRunner()


def test_cli_presets_and_run_commands(tmp_path):
    res_presets = runner.invoke(cli_app, ["presets"])
    assert res_presets.exit_code == 0
    assert "campus-lan" in res_presets.output
    assert "metro-man" in res_presets.output
    assert "global-wan" in res_presets.output

    res_run = runner.invoke(cli_app, ["run", "campus-lan", "--export", "--output-dir", str(tmp_path)])
    assert res_run.exit_code == 0
    assert (tmp_path / "profile1_campus_lan.cfg").exists()
    assert (tmp_path / "profile1_campus_lan_plan.json").exists()
    assert (tmp_path / "profile1_campus_lan_subnets.csv").exists()

    res_unknown = runner.invoke(cli_app, ["run", "unknown-profile"])
    assert res_unknown.exit_code == 1


def test_cli_custom_json_plan_and_boundary_error_exit_codes(tmp_path):
    bad_file = tmp_path / "bad_copper.json"
    bad_file.write_text(
        json.dumps({
            "root_network": "10.0.0.0/24",
            "links": [{"link_id": "L1", "distance_meters": 250.0, "medium_preference": "COPPER"}],
            "subnets": [{"name": "Sub1", "required_hosts": 10, "vlan_id": 10}],
        }),
        encoding="utf-8",
    )
    res_bad = runner.invoke(cli_app, ["plan", "--file", str(bad_file)])
    assert res_bad.exit_code == 1
    assert "PHYSICAL DISTANCE VIOLATION" in res_bad.output


def test_json_and_csv_exporters_write_valid_artifacts(tmp_path):
    sc = get_campus_lan_scenario()
    plan = NetworkPlanner.execute_plan(sc)

    json_path = JSONExporter.save_to_file(plan, tmp_path / "plan.json")
    csv_path = CSVExporter.save_subnets_to_csv(plan.subnet_allocations, tmp_path / "subnets.csv")

    parsed_json = json.loads(json_path.read_text(encoding="utf-8"))
    assert parsed_json["scenario_id"] == "campus-lan"
    assert len(parsed_json["subnet_allocations"]) == 5

    with open(csv_path, mode="r", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    assert rows[0][0] == "Subnet Name"
    assert len(rows) == 6  # header + 5 subnets


def test_explainability_engine_generates_rfc_and_ieee_citations():
    sc = get_campus_lan_scenario()
    plan = NetworkPlanner.execute_plan(sc)
    joined = "\n".join(plan.executive_rationales)

    assert "802.3an" in joined
    assert "802.1w" in joined
    assert "RFC 2328" in joined
    assert "bitwise" in joined.lower()

