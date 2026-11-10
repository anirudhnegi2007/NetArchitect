# NetArchitect: System Architecture & Technical Specification

**Course Code:** CIC-307 — Computer Networks Mini-Project  
**Author:** Anirudh Negi (05414802724)  
**Engine:** Algorithmic Network Planning & Self-Explaining Architecture Engine  
**Version:** 1.0.0 (Production Architecture)  

---

## 1. System Overview & Core Philosophy

**NetArchitect** is an algorithmic network planning utility designed to bridge high-level enterprise infrastructure requirements with production-grade, mathematically verified network deployments. 

Unlike traditional heuristic templates or opaque LLM generation, NetArchitect operates on **deterministic constraint satisfaction**:
1. **Mathematical Guarantees:** Bitwise VLSM allocations with strict non-overlapping prefix trees.
2. **Physical Boundary Enforcement:** Hard real-world limits derived from IEEE 802.3 Ethernet and ITU-T optical dispersion specifications.
3. **Explainable Rationale Engine:** Every hardware, media, protocol, and subnet selection is accompanied by human-readable engineering justifications citing IEEE standards and IETF RFCs.
4. **Copy-Paste Production Artifacts:** Generates syntax-validated Cisco IOS configuration files ready for immediate deployment to Cisco Catalyst switches, ISR/ASR routers, and network emulators (Cisco Packet Tracer, GNS3, EVE-NG).

---

## 2. End-to-End System Pipeline

```
+----------------------------------------------------------------------------------------------------+
|                                    NETARCHITECT SYSTEM PIPELINE                                    |
+----------------------------------------------------------------------------------------------------+

   [ Preset Profiles / Custom JSON ]
                 |
                 v
   +-----------------------------+
   |  1. Input Ingestion Engine  | <--- Pydantic schema validation & boundary sanity checks
   +-----------------------------+
                 |
                 v
   +-----------------------------+
   |    2. L1/L2 Media Engine    | <--- Distance physics, IEEE 802.3an/ae, 850nm dispersion,
   +-----------------------------+      RSTP convergence & 802.1Q VLAN trunking constraints
                 |
                 v
   +-----------------------------+
   |   3. L3 VLSM & Routing      | <--- Bitwise descending prefix tree allocator, RFC 1918,
   +-----------------------------+      OSPF Area 0 / Multi-Area / eBGP decision engine
                 |
                 v
   +-----------------------------+
   | 4. Self-Explaining Engine   | <--- Generates dynamic rationale logs with RFC/IEEE citations
   +-----------------------------+
                 |
                 v
   +-----------------------------+
   |  5. Cisco IOS Exporter      | <--- Compiles validated models into ready-to-run Cisco IOS
   +-----------------------------+      configs (.cfg) for Switches, Routers, SVIs, & ACLs
                 |
                 +---> stdout / Interactive Terminal (Rich UI)
                 +---> JSON Export (REST API / Dashboard)
                 +---> Packet Tracer / GNS3 .cfg files
```

---

## 3. Detailed Component Architecture

### Component 1: Input Ingestion & Schema Validation (`netarchitect.parsers`)
* **Role:** Parses incoming scenario descriptors (preset profiles or custom user JSON).
* **Validation Rules:**
  * Root IPv4 prefix validation (RFC 1918 private scopes: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`).
  * Non-negative link distances and positive integer host requirements.
  * Resiliency topology flags: `dual-homed`, `single-homed`, `redundant-core`.
  * Traffic priority classes: `realtime-voice` (EF), `financial-trading` (AF41), `best-effort` (BE).
* **Exceptions Handled:**
  * `InvalidCIDRFormatError`: Malformed IPv4 prefix strings.
  * `NonPrivateAddressWarning`: Detection of routable public addresses without NAT boundary specification.

### Component 2: Physical & Data Link Media Engine (`netarchitect.engines.l1_l2`)
* **Role:** Enforces transmission media physics, transceiver optics, and data-link protocols.
* **Algorithmic Rules:**

| Link Reach ($d$) | Medium | Transceiver Standard | Wavelength | Engineering Rationale |
|---|---|---|:---:|---|
| $d \le 100\text{ m}$ | Cat6a UTP/STP | 10GBASE-T | Electrical | IEEE 802.3an standard limit. Attenuation and alien crosstalk (ANEXT) restrict 10G copper to 100m. |
| $100\text{ m} < d \le 400\text{ m}$ | OM4 Multimode Fiber (MMF 50/125 $\mu$m) | 10GBASE-SR | $850\text{ nm}$ | Modal dispersion limits VCSEL laser pulses over MMF. Reaches up to 400m on OM4 (vs 300m on OM3). |
| $400\text{ m} < d \le 10\text{ km}$ | OS2 Single-Mode Fiber (SMF 9/125 $\mu$m) | 10GBASE-LR | $1310\text{ nm}$ | IEEE 802.3ae standard. Zero modal dispersion allows 10 km reach over 1310 nm DFB laser. |
| $10\text{ km} < d \le 40\text{ km}$ | OS2 Single-Mode Fiber (SMF 9/125 $\mu$m) | 10GBASE-ER | $1550\text{ nm}$ | Operates in silica minimum-loss window ($0.25\text{ dB/km}$) with higher transmitter launch power. |
| $d > 40\text{ km}$ | OS2 SMF + Optical Amplification / DWDM | 10GBASE-ZR / DWDM | $1550\text{ nm}$ | Optical path attenuation exceeds 10GBASE-ER $15\text{ dB}$ budget; requires EDFA or DWDM transponders. |

* **Boundary Exceptions:**
  * If a copper medium (Cat6a/Cat5e) is requested for $d > 100\text{ m}$, the engine raises `PhysicalDistanceViolationError` with exact dB attenuation loss estimates.

### Component 3: Layer 3 VLSM Bitwise Subnet Allocator (`netarchitect.engines.vlsm`)
* **Role:** Optimal IPv4 variable-length subnet mask allocation with zero fragmentation and zero address overlap.
* **Mathematical Algorithm:**
  1. Let $R$ be the root network prefix with prefix length $P_{\text{root}}$ and capacity $2^{32 - P_{\text{root}}}$.
  2. Ingest list of host requirements: $H = [h_1, h_2, \dots, h_n]$.
  3. Sort $H$ in descending order: $h_{(1)} \ge h_{(2)} \ge \dots \ge h_{(n)}$.
  4. For each host requirement $h_i$:
     * Calculate required host address count: $C_i = h_i + 2$ (adding Network ID and Broadcast IP; for `/31` point-to-point links per RFC 3021, $C_i = 2$).
     * Compute prefix length:
       $$p_i = 32 - \lceil \log_2(C_i) \rceil$$
     * Subnet mask integer:
       $$M_i = (0\text{xFFFFFFFF} \ll (32 - p_i)) \ \& \ 0\text{xFFFFFFFF}$$
     * Wildcard mask integer:
       $$W_i = M_i \oplus 0\text{xFFFFFFFF}$$
     * Allocate the next available boundary: Align current cursor $A$ to the next multiple of $2^{32 - p_i}$:
       $$A_{\text{aligned}} = (A + 2^{32 - p_i} - 1) \ \& \ (\sim(2^{32 - p_i} - 1))$$
     * Check boundary containment: If $A_{\text{aligned}} + 2^{32 - p_i} > \text{Root Broadcast} + 1$, raise `AddressSpaceExhaustionError`.
     * Usable range:
       $$\text{Gateway} = A_{\text{aligned}} + 1, \quad \text{Host Min} = A_{\text{aligned}} + 2, \quad \text{Host Max} = A_{\text{aligned}} + 2^{32 - p_i} - 2$$
     * Advance cursor: $A \leftarrow A_{\text{aligned}} + 2^{32 - p_i}$.

### Component 4: Explainable Decision Engine (`netarchitect.engines.explainability`)
* **Role:** Produces deterministic, contextual engineering justifications for every architectural decision.
* **Citation Matrix:**

| Architecture Domain | Recommendation | Engineering Justification & Standard Citation |
|---|---|---|
| **Intra-Building Access** | Cat6a (10GBASE-T) | IEEE 802.3an allows 10 Gbps up to 100 meters. Power over Ethernet (802.3bt PoE++) delivers up to 90W to Wi-Fi 6/7 Access Points without dedicated power runs. |
| **Inter-Building Backbone** | OM4 MMF (10GBASE-SR) | $850\text{ nm}$ VCSEL laser optics over $50/125\ \mu\text{m}$ multimode fiber supports up to 400m distance at lower optical transceiver cost than single-mode optics. |
| **Metro Link ($>10\text{ km}$)** | OS2 SMF (10GBASE-ER) | Link distance exceeds the $400\text{ m}$ modal dispersion limit of MMF and the $10\text{ km}$ reach of 10GBASE-LR. $1550\text{ nm}$ single-mode laser guarantees link budget over long-span attenuation. |
| **Spanning Tree** | Rapid PVST+ / RSTP | IEEE 802.1w reduces STP convergence time from 30–50 seconds down to sub-second ($<1\text{ s}$) via direct handshake proposal/agreement on point-to-point links. |
| **Routing Protocol (<50 subnets)** | OSPF Area 0 | RFC 2328 link-state algorithm (Dijkstra SPF) provides loop-free sub-second internal convergence for single autonomous systems. |
| **Routing Protocol (Multi-Site/Cloud)** | Multi-Area OSPF / eBGP | RFC 4271 (BGP-4) provides autonomous system boundary isolation, policy-based path-vector routing, and prevents routing table bloat via prefix summarization. |

### Component 5: Cisco IOS Configuration Synthesis (`netarchitect.exporters.cisco_ios`)
* **Role:** Translates validated architectural objects into syntactic, hardened Cisco IOS configurations.
* **Generates:**
  1. **Core / Distribution Switches:**
     * VTP mode transparent / off.
     * VLAN databases with named segments.
     * Hardened IEEE 802.1Q Trunks (`switchport mode trunk`, `switchport nonegotiate`, quarantined Native VLAN 999).
     * Rapid Spanning Tree (`spanning-tree mode rapid-pvst`, Root Guard, BPDU Guard).
     * Switched Virtual Interfaces (SVIs) with HSRP / VRRP gateway redundancy.
  2. **Edge / Core Routers:**
     * Sub-interfaces with 802.1Q encapsulation for Router-on-a-Stick or routed L3 interfaces.
     * OSPF routing process with mathematically verified inverse wildcard masks.
     * eBGP peering with `neighbor remote-as` and route summarization.
     * IPsec Crypto Maps, Phase 1 ISAKMP profiles, and Phase 2 IPsec transform sets for Global WAN.
  3. **Access Control Lists (ACLs):**
     * Extended IP access lists isolating guest / IoT subnets from internal management and server zones.

---

## 4. Directory & Module Organization

```
NetArchitect/
├── README.md                                    # Comprehensive User & Developer Guide
├── ARCHITECTURE.md                              # This Technical Architecture Document
├── ai_audit_log.md                              # Mandatory AI Defense & Audit Log (20 Pts)
├── PACKET_TRACER_VERIFICATION_GUIDE.md          # Packet Tracer / GNS3 Verification Manual
├── _DEFENSE_GUIDE.md                            # Viva Examination & Defense Q&As
├── pyproject.toml / requirements.txt            # Dependency Management
│
├── src/netarchitect/                            # Core Engine Source Code (src-layout)
│   ├── __init__.py
│   ├── cli.py                                   # Typer & Rich Interactive CLI
│   ├── network_planner.py                       # Main Orchestrator Facade
│   ├── exceptions.py                            # Custom Domain Exceptions
│   ├── models/                                  # Data Contracts & Pydantic Schemas
│   │   ├── __init__.py
│   │   ├── scenario_inputs.py                   # Scenario, Link, and Subnet Input Models
│   │   └── architecture_outputs.py              # Recommendation & Export Data Models
│   ├── engines/                                 # Algorithmic Rule Processors
│   │   ├── __init__.py
│   │   ├── physical_media_engine.py             # Distance Physics & Media Engine
│   │   ├── vlsm_subnet_allocator.py             # Bitwise Subnet Allocator & Optimizer
│   │   ├── routing_protocol_engine.py           # OSPF/BGP Protocol Selection Engine
│   │   └── architectural_rationale_engine.py    # Natural-Language Rationale Generator
│   ├── exporters/                               # Configuration Generators
│   │   ├── __init__.py
│   │   ├── cisco_ios_config_generator.py        # Cisco Catalyst & ISR Config Synthesizer
│   │   ├── plan_json_exporter.py                # Structured JSON Exporter
│   │   └── subnet_csv_exporter.py               # Subnet Allocation CSV Exporter
│   ├── presets/                                 # Preset Enterprise Scenarios
│   │   ├── __init__.py
│   │   ├── profile1_campus_lan.py               # Profile 1: Campus LAN (3 Bldgs, 1600 Nodes)
│   │   ├── profile2_metro_man.py                # Profile 2: Metro MAN (HQ + 2 Remote, 450 Nodes)
│   │   ├── profile3_global_wan.py               # Profile 3: Global WAN (4 Cities + Cloud VPC)
│   │   └── preset_registry.py                   # Preset Scenario Registry
│   └── web/                                     # Web Dashboard (FastAPI + HTML/JS)
│       ├── __init__.py
│       ├── api_server.py                        # Web API & UI Server
│       └── static/                              # Embedded Dashboard Assets
│
├── ai_audit_traces/                             # Raw Regression Failure Logs
│
├── exports/                                     # Verification Configuration Exports
│   ├── profile1_campus_lan.cfg                  # Packet Tracer / GNS3 Profile 1 Config
│   ├── profile2_metro_man.cfg                   # Packet Tracer / GNS3 Profile 2 Config
│   └── profile3_global_wan.cfg                  # Packet Tracer / GNS3 Profile 3 Config
│
└── tests/                                       # Automated Pytest Suite (40 Test Functions)
    ├── __init__.py
    ├── test_physical_media_engine.py            # Distance violations & media selection
    ├── test_vlsm_subnet_allocator.py            # Subnet overlaps, boundaries, exhaustion
    ├── test_routing_protocol_engine.py          # OSPF vs BGP selection logic
    ├── test_cisco_ios_config_generator.py       # Syntactic correctness of generated configs
    ├── test_ai_hallucination_defenses.py        # Regression tests for AI hallucinations
    ├── test_validation_and_api.py               # Input schemas, presets, and API checks
    └── test_cli_and_exporters.py                # CLI, CSV/JSON exporters, and explainability
```

---

## 5. Algorithmic Complexity Analysis

1. **VLSM Subnet Allocation:**
   * Sorting $n$ host requirements: $\mathcal{O}(n \log n)$ via Timsort.
   * Bitwise address cursor allocation: $\mathcal{O}(n)$ bitwise operations.
   * Total Time Complexity: $\mathcal{O}(n \log n)$, requiring $<2\text{ ms}$ for typical enterprise scopes ($n \le 1000$).
   * Space Complexity: $\mathcal{O}(n)$ to store allocated subnet metadata.

2. **L1 Media Selection:**
   * Direct constraint evaluation: $\mathcal{O}(1)$ interval lookups against boundary limits.

3. **Cisco IOS Synthesis:**
   * Linear string templating over allocated interfaces and VLANs: $\mathcal{O}(V + I)$ where $V$ is number of VLANs and $I$ is interface count.

