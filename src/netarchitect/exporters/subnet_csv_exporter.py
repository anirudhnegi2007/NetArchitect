"""
Subnet CSV Exporter for NetArchitect.
Exports allocated subnet tables to standard CSV format for NOC and spreadsheet ingestion.
"""

import csv
from pathlib import Path
from typing import List, Union

from netarchitect.models.architecture_outputs import SubnetAllocation


class CSVExporter:
    """Exports SubnetAllocation objects to standard RFC 4180 CSV files."""

    @classmethod
    def save_subnets_to_csv(
        cls, allocations: List[SubnetAllocation], destination_path: Union[str, Path]
    ) -> Path:
        path = Path(destination_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            "Subnet Name",
            "VLAN ID",
            "Security Zone",
            "Required Hosts",
            "Allocated Hosts",
            "CIDR Prefix",
            "Network Address",
            "Subnet Mask",
            "Wildcard Mask",
            "Default Gateway",
            "First Usable IP",
            "Last Usable IP",
            "Broadcast Address",
            "Allocation Efficiency %",
        ]

        with open(path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(fieldnames)
            for a in allocations:
                writer.writerow([
                    a.name,
                    a.vlan_id,
                    a.security_zone.value if hasattr(a.security_zone, "value") else str(a.security_zone),
                    a.required_hosts,
                    a.allocated_hosts,
                    a.cidr,
                    a.network_address,
                    a.netmask,
                    a.wildcard_mask,
                    a.default_gateway,
                    a.first_usable_ip,
                    a.last_usable_ip,
                    a.broadcast_address,
                    f"{a.efficiency_pct}%",
                ])

        return path

