"""
Cisco IOS Configuration Synthesizer & Exporter.
Compiles validated architectural models, subnet allocations, and security constraints
into copy-paste-ready Cisco IOS configurations for Cisco Packet Tracer, GNS3, and physical hardware.
"""

import ipaddress
from typing import List

from netarchitect.models.architecture_outputs import (
    DeviceConfig,
    MediaRecommendation,
    RoutingRecommendation,
    SubnetAllocation,
)
from netarchitect.models.scenario_inputs import (
    ScenarioInput,
)


class CiscoIOSConfigSynthesizer:
    """
    Produces hardened, production-ready Cisco IOS scripts conforming to NSA and Cisco
    Network Architecture Hardening guidelines. Mitigates DTP exploitation, double-tagging,
    and routing loop vulnerabilities.
    """

    NATIVE_QUARANTINE_VLAN = 999

    @classmethod
    def synthesize_all(
        cls,
        scenario: ScenarioInput,
        media_recs: List[MediaRecommendation],
        allocations: List[SubnetAllocation],
        routing_rec: RoutingRecommendation,
    ) -> List[DeviceConfig]:
        configs: List[DeviceConfig] = []

        # 1. Synthesize Core / Distribution Multilayer Switch Config
        configs.append(cls.synthesize_core_switch(scenario, allocations, routing_rec))

        # 2. Synthesize Access Switch Config
        configs.append(cls.synthesize_access_switch(scenario, allocations))

        # 3. Synthesize Edge / Core Router Config
        configs.append(cls.synthesize_router(scenario, media_recs, allocations, routing_rec))

        return configs

    @classmethod
    def synthesize_core_switch(
        cls,
        scenario: ScenarioInput,
        allocations: List[SubnetAllocation],
        routing_rec: RoutingRecommendation,
    ) -> DeviceConfig:
        hostname = f"{scenario.id.upper()}-CORE-SW01"
        vlan_ids = [a.vlan_id for a in allocations]
        allowed_vlans_str = ",".join(str(v) for v in sorted(vlan_ids)) if vlan_ids else "1"

        lines = [
            f"! ===========================================================================",
            f"! CISCO IOS CONFIGURATION: CORE / DISTRIBUTION MULTILAYER SWITCH",
            f"! Scenario: {scenario.name}",
            f"! Hostname: {hostname}",
            f"! Generated automatically by NetArchitect Recommendation Engine",
            f"! ===========================================================================",
            "enable",
            "configure terminal",
            f"hostname {hostname}",
            "no ip domain-lookup",
            "service password-encryption",
            "ip routing",
            "",
            "! --- VTP DOMAIN HARDENING ---",
            "vtp mode transparent",
            "",
            "! --- 802.1Q VLAN DATABASE DEFINITIONS ---",
        ]

        # Add VLANs
        for alloc in allocations:
            lines.extend([
                f"vlan {alloc.vlan_id}",
                f" name {alloc.name[:32]}",
                " exit",
            ])

        # Add Quarantine Native VLAN
        lines.extend([
            f"vlan {cls.NATIVE_QUARANTINE_VLAN}",
            " name QUARANTINE_NATIVE_VLAN",
            " state suspend",
            " exit",
            "",
            "! --- SPANNING TREE PROTOCOL (IEEE 802.1w RAPID PVST+) ---",
            "spanning-tree mode rapid-pvst",
            f"spanning-tree vlan {allowed_vlans_str} priority 4096",
            "spanning-tree portfast default",
            "spanning-tree portfast bpduguard default",
            "",
            "! --- HARDENED 802.1Q TRUNK UPLINKS (DTP DISABLED) ---",
            "interface range GigabitEthernet0/1 - 2",
            " description UPLINK-TO-ACCESS-SWITCHES",
            " switchport trunk encapsulation dot1q",
            " switchport mode trunk",
            " switchport nonegotiate",
            f" switchport trunk native vlan {cls.NATIVE_QUARANTINE_VLAN}",
            f" switchport trunk allowed vlan {allowed_vlans_str}",
            " spanning-tree guard root",
            " no shutdown",
            " exit",
            "",
            "! --- SWITCHED VIRTUAL INTERFACES (SVIs) & GATEWAYS ---",
        ])

        for alloc in allocations:
            lines.extend([
                f"interface Vlan{alloc.vlan_id}",
                f" description SVI-GATEWAY-FOR-{alloc.name}",
                f" ip address {alloc.default_gateway} {alloc.netmask}",
                " no shutdown",
                " exit",
            ])

        # Routing Section for Core Switch
        router_id = allocations[0].default_gateway if allocations else "1.1.1.1"
        lines.extend([
            "",
            "! --- DYNAMIC ROUTING CONFIGURATION ---",
            "router ospf 1",
            f" router-id {router_id}",
            " passive-interface default",
        ])

        for alloc in allocations:
            lines.append(f" no passive-interface Vlan{alloc.vlan_id}")

        for alloc in allocations:
            lines.append(f" network {alloc.network_address} {alloc.wildcard_mask} area 0")

        lines.extend([
            " exit",
            "",
            "end",
            "write memory",
            "",
        ])

        return DeviceConfig(
            hostname=hostname,
            device_role="Core-Switch",
            config_text="\n".join(lines),
        )

    @classmethod
    def synthesize_access_switch(
        cls,
        scenario: ScenarioInput,
        allocations: List[SubnetAllocation],
    ) -> DeviceConfig:
        hostname = f"{scenario.id.upper()}-ACCESS-SW01"
        vlan_ids = [a.vlan_id for a in allocations]
        allowed_vlans_str = ",".join(str(v) for v in sorted(vlan_ids)) if vlan_ids else "1"
        primary_vlan = allocations[0].vlan_id if allocations else 10

        lines = [
            f"! ===========================================================================",
            f"! CISCO IOS CONFIGURATION: ACCESS LAYER SWITCH",
            f"! Scenario: {scenario.name}",
            f"! Hostname: {hostname}",
            f"! Generated automatically by NetArchitect Recommendation Engine",
            f"! ===========================================================================",
            "enable",
            "configure terminal",
            f"hostname {hostname}",
            "no ip domain-lookup",
            "service password-encryption",
            "",
            "! --- VTP TRANSPARENT MODE ---",
            "vtp mode transparent",
            "",
            "! --- VLAN DEFINITIONS ---",
        ]

        for alloc in allocations:
            lines.extend([
                f"vlan {alloc.vlan_id}",
                f" name {alloc.name[:32]}",
                " exit",
            ])

        lines.extend([
            f"vlan {cls.NATIVE_QUARANTINE_VLAN}",
            " name QUARANTINE_NATIVE_VLAN",
            " state suspend",
            " exit",
            "",
            "! --- RAPID SPANNING TREE ---",
            "spanning-tree mode rapid-pvst",
            "",
            "! --- HARDENED TRUNK TO CORE SWITCH ---",
            "interface GigabitEthernet0/1",
            " description UPLINK-TO-CORE-DISTRIBUTION-SWITCH",
            " switchport trunk encapsulation dot1q",
            " switchport mode trunk",
            " switchport nonegotiate",
            f" switchport trunk native vlan {cls.NATIVE_QUARANTINE_VLAN}",
            f" switchport trunk allowed vlan {allowed_vlans_str}",
            " no shutdown",
            " exit",
            "",
            "! --- ACCESS EDGE PORTS (WITH PORTFAST & BPDU GUARD) ---",
            "interface range FastEthernet0/1 - 24",
            f" description ACCESS-ENDPOINTS-VLAN-{primary_vlan}",
            " switchport mode access",
            f" switchport access vlan {primary_vlan}",
            " spanning-tree portfast",
            " spanning-tree bpduguard enable",
            " no shutdown",
            " exit",
            "",
            "end",
            "write memory",
            "",
        ])

        return DeviceConfig(
            hostname=hostname,
            device_role="Access-Switch",
            config_text="\n".join(lines),
        )

    @classmethod
    def synthesize_router(
        cls,
        scenario: ScenarioInput,
        media_recs: List[MediaRecommendation],
        allocations: List[SubnetAllocation],
        routing_rec: RoutingRecommendation,
    ) -> DeviceConfig:
        hostname = f"{scenario.id.upper()}-BORDER-ROUTER01"
        is_bgp = "bgp" in routing_rec.protocol.lower()
        root_net = ipaddress.IPv4Network(scenario.root_network, strict=False)
        lan_ip = allocations[0].last_usable_ip if allocations else str(root_net.network_address + 1)
        lan_mask = allocations[0].netmask if allocations else str(root_net.netmask)
        ospf_router_id = allocations[0].default_gateway if allocations else "1.1.1.1"

        lines = [
            f"! ===========================================================================",
            f"! CISCO IOS CONFIGURATION: ENTERPRISE BORDER / CORE ROUTER",
            f"! Scenario: {scenario.name}",
            f"! Hostname: {hostname}",
            f"! Generated automatically by NetArchitect Recommendation Engine",
            f"! ===========================================================================",
            "enable",
            "configure terminal",
            f"hostname {hostname}",
            "no ip domain-lookup",
            "service password-encryption",
            "",
            "! --- INTERFACE CONFIGURATION ---",
            "interface GigabitEthernet0/0/0",
            " description LAN-INTERNAL-CORE-LINK",
            f" ip address {lan_ip} {lan_mask}",
            " no shutdown",
            " exit",
            "",
            "interface GigabitEthernet0/0/1",
            " description WAN-PUBLIC-UPLINK",
            " ip address 198.51.100.1 255.255.255.252",
            " no shutdown",
            " exit",
            "",
            "! --- HARDENED ROUTING ENGINE PROTOCOL ---",
        ]

        if is_bgp:
            lines.extend([
                f"router bgp {scenario.autonomous_system_number}",
                " bgp router-id 198.51.100.1",
                " bgp log-neighbor-changes",
                " neighbor 198.51.100.2 remote-as 65000",
                " neighbor 198.51.100.2 description CLOUD-VPC-TRANSIT-GW",
                f" network {root_net.network_address} mask {root_net.netmask}",
                " exit",
                "",
                "! --- OSPF INTERNAL REDISTRIBUTION ---",
                "router ospf 1",
                f" router-id {ospf_router_id}",
            ])
            for alloc in allocations:
                lines.append(f" network {alloc.network_address} {alloc.wildcard_mask} area 0")
            lines.append(" exit")

        else:
            lines.extend([
                "router ospf 1",
                f" router-id {ospf_router_id}",
                " log-adjacency-changes",
            ])
            for alloc in allocations:
                lines.append(f" network {alloc.network_address} {alloc.wildcard_mask} area 0")
            lines.append(" exit")

        # Security ACLs
        lines.extend([
            "",
            "! --- ENTERPRISE DEFENSE ACCESS CONTROL LISTS (ACLs) ---",
            "ip access-list extended ACL-ISOLATE-IOT-AND-GUEST",
            " remark Permit established return sessions",
            " permit tcp any any established",
            " remark Permit internal DNS and DHCP",
            " permit udp any any eq domain",
            " permit udp any any eq bootps",
            " permit udp any any eq bootpc",
            " remark Deny guest and IoT access to internal corporate subnets (RFC 1918)",
            " deny ip 10.0.0.0 0.255.255.255 10.10.10.0 0.0.0.255",
            " deny ip 172.16.0.0 0.15.255.255 172.16.199.0 0.0.0.255",
            " permit ip any any",
            " exit",
            "",
            "end",
            "write memory",
            "",
        ])

        return DeviceConfig(
            hostname=hostname,
            device_role="Core-Router",
            config_text="\n".join(lines),
        )

    @classmethod
    def generate_unified_config(cls, device_configs: List[DeviceConfig]) -> str:
        blocks = []
        for dev in device_configs:
            blocks.append(dev.config_text)
            blocks.append("\n" + ("#" * 80) + "\n")
        return "\n".join(blocks)

