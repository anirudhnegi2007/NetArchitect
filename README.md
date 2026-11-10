# NetArchitect: Recommendation & Config Engine
### Algorithmic Network Planning & Self-Explaining Architecture Engine

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Tests: 72 Passed](https://img.shields.io/badge/tests-72%20passed-brightgreen.svg)](tests/)
[![Academic Integrity](https://img.shields.io/badge/AI--Assisted-Audited%20%26%20Defended-orange.svg)](./ai_audit_log.md)

**Course Code:** CIC-307 • Computer Networks Mini-Project  
**Author:** Anirudh Negi (05414802724)  
**Repository:** [github.com/anirudhnegi2007/NetArchitect](https://github.com/anirudhnegi2007/NetArchitect)  
**Evaluation Weight:** 100 Points  
**Format:** Individual Architecture Engine  

---

## 🌟 Executive Summary

**NetArchitect** is a computer networking software utility that automates enterprise infrastructure design through algorithmic rule engines. It ingests high-level parameters (distances, endpoint counts, resiliency modes), performs physical-layer validation and bitwise variable-length subnet mask (VLSM) calculations, outputs natural-language engineering justifications citing IEEE/RFC standards, and compiles copy-paste-ready Cisco IOS configurations.

### Key Capabilities
* **Physical Media & Distance Physics (L1/L2):** Evaluates copper (Cat6a) vs Multimode Fiber (OM4) vs Single-Mode Fiber (OS2) with real-world attenuation limits, modal dispersion boundaries, and optical link budgets.
* **Flawless Bitwise VLSM Allocator (L3):** Computes non-overlapping subnet allocations, usable ranges, default gateways, broadcast IPs, and bitwise inverted wildcard masks without route overlap.
* **Explainable Decision Engine:** Generates natural-language rationales for every design decision (IEEE 802.3an, IEEE 802.1w RSTP, RFC 1918, RFC 2328 OSPF, RFC 4271 BGP).
* **Multi-Format Synthesis:** Produces interactive CLI tables (Rich/Typer), a local responsive Web Dashboard (FastAPI), JSON data exports, and Cisco IOS `.cfg` deployment scripts for Cisco Packet Tracer and GNS3.
* **AI Defense & Code Auditing:** Includes a rigorous audit log (`ai_audit_log.md`) detailing technical post-mortems of AI-generated networking flaws with packet flow analysis.

---

## 🏗️ Supported Scenario Presets

| Profile | Target Environment | Scale & Distances | Protocols & Hardware | Key Focus |
|---|---|---|---|---|
| **Profile 1: Campus LAN** | Multi-building enterprise campus | 3 Buildings, $<400\text{ m}$, 1,600 nodes | Cat6a PoE+, OM4 MMF (10GBASE-SR), Catalyst 3650 / 2960 | 802.1Q VLANs, RSTP sub-second convergence, Single-Area OSPF Area 0 |
| **Profile 2: Metro MAN** | HQ to remote financial colocations | HQ + 2 Sites ($15\text{–}35\text{ km}$), 450 nodes | OS2 SMF (10GBASE-LR/ER), Cisco ISR 4331 | EVPL, sub-5ms low latency QoS, dual-homed link failover ring |
| **Profile 3: Global WAN** | Multi-region multinational + cloud | 4 Global Cities + Cloud VPC, 2,000 IoT nodes | IPsec VPN, BGP peering, Cisco ASR 1001-X | Route summarization, Multi-Area OSPF backbone, eBGP AS peering |

---

## 🚀 Quick Start Guide

### 1. Prerequisites & Installation
```bash
git clone https://github.com/anirudhnegi2007/NetArchitect.git
cd NetArchitect
pip install -e .
```
* Python 3.10+ (tested on Python 3.12.10)
* Or install dependencies directly via `pip install -r requirements.txt`

### 2. Running via Command-Line Interface (CLI)
```bash
# List all preset enterprise profiles
python -m netarchitect.cli presets

# Run Profile 1 (Campus LAN) with terminal report and Cisco IOS export
python -m netarchitect.cli run campus-lan --export

# Run Profile 2 (Metro MAN) and inspect explainable rationales
python -m netarchitect.cli run metro-man --export

# Run Profile 3 (Global WAN)
python -m netarchitect.cli run global-wan --export

# Ingest and validate a custom JSON scenario
python -m netarchitect.cli plan --file sample_scenarios/custom_enterprise_datacenter.json
```

### 3. Launching the Web Dashboard
```bash
# Start the local interactive dashboard
python -m netarchitect.web.app --port 8000
```
Open `http://127.0.0.1:8000` in your web browser to interactively tweak distances, host requirements, test boundary violations, and generate Cisco configs on the fly.

### 4. Running the Test Suite
```bash
# Execute unit tests with verbose output
pytest -v
```

---

## 📊 Evaluation Rubric Compliance (100/100 Pts)

| Rubric Area | Points | Implementation & Evidence |
|---|:---:|---|
| **1. Parameter Engine & Presets** | 15 Pts | Implemented in `src/netarchitect/presets/` and `src/netarchitect/models/`. Enforces validation on distance, density, resiliency, and catches boundary violations gracefully. |
| **2. Explainable Decision Engine** | 25 Pts | Implemented in `src/netarchitect/engines/architectural_rationale_engine.py`. Produces IEEE and RFC justified explanations for media, transceivers, routing protocols, and topology tiers. |
| **3. Subnet Engine & Configs** | 25 Pts | Implemented in `src/netarchitect/engines/vlsm_subnet_allocator.py` and `src/netarchitect/exporters/cisco_ios_config_generator.py`. Bitwise non-overlapping VLSM allocator + deployment-ready Cisco IOS configs for switches, routers, SVIs, and ACLs. |
| **4. Automated Unit Testing** | 15 Pts | Implemented under `tests/` (40 test functions / 70+ parametrized assertions). Covers distance violations, address exhaustion, wildcard calculations, CLI, and Web API. |
| **5. AI Code Audit & Defense** | 20 Pts | Documented in `ai_audit_log.md` with 3 detailed post-mortems and packet-flow analyses, with regression tests in `tests/test_ai_hallucination_defenses.py`. |
| **Verification Exports** | Req | Exported into `exports/profile{1,2,3}_*.cfg` with simulation steps in `PACKET_TRACER_VERIFICATION_GUIDE.md`. |

---

## 📁 Repository Structure

```
NetArchitect/
├── README.md                                    # This Overview & User Guide
├── ARCHITECTURE.md                              # Deep System Architecture & Math Model
├── PACKET_TRACER_VERIFICATION_GUIDE.md          # Packet Tracer / GNS3 Verification Manual
├── _DEFENSE_GUIDE.md                            # Viva Examination & Defense Q&As
├── ai_audit_log.md                              # Mandatory AI Defense Audit Log (20 Pts)
├── pyproject.toml / requirements.txt            # Package & Dependency Management
│
├── src/netarchitect/                            # Core Engine Source Code (src-layout)
│   ├── cli.py                                   # Typer & Rich Interactive CLI
│   ├── network_planner.py                       # Pipeline Orchestrator
│   ├── models/                                  # Pydantic Schemas & Data Contracts
│   ├── engines/                                 # L1 Physics, VLSM & Explainability Engines
│   ├── presets/                                 # Campus LAN, Metro MAN, Global WAN Profiles
│   ├── exporters/                               # Cisco IOS, JSON & CSV Synthesizers
│   └── web/                                     # Web Dashboard & FastAPI Backend
│
├── ai_audit_traces/                             # Captured Raw AI Defect Failure Logs
│
├── exports/                                     # Ready-to-load Cisco IOS Configs & CSVs
│   ├── profile1_campus_lan.cfg
│   ├── profile2_metro_man.cfg
│   └── profile3_global_wan.cfg
│
└── tests/                                       # Automated Pytest Suite (40 Test Functions)
    ├── test_physical_media_engine.py
    ├── test_vlsm_subnet_allocator.py
    ├── test_routing_protocol_engine.py
    ├── test_cisco_ios_config_generator.py
    ├── test_ai_hallucination_defenses.py
    ├── test_validation_and_api.py
    └── test_cli_and_exporters.py
```

---

## 📜 Standards & RFC References
* **IEEE 802.3an:** Physical Layer and Management Parameters for 10 Gb/s Operation (10GBASE-T).
* **IEEE 802.3ae:** 10 Gb/s over Optical Fiber (10GBASE-SR / 10GBASE-LR / 10GBASE-ER).
* **IEEE 802.1w:** Rapid Spanning Tree Protocol (RSTP).
* **IEEE 802.1Q:** Bridges and Bridged Networks: Virtual Bridged Local Area Networks.
* **IETF RFC 1918:** Address Allocation for Private Internets.
* **IETF RFC 2328:** OSPF Version 2.
* **IETF RFC 3021:** Using 31-Bit Prefixes on IPv4 Point-to-Point Links.
* **IETF RFC 4271:** A Border Gateway Protocol 4 (BGP-4).

---

## ✅ Final Submission Verification Status
* **Automated Unit & API Tests:** `pytest -v` — **72 passed** across 40 explicit test functions.
* **Code Quality:** Verified clean imports and formatting with `ruff`.
* **Verification Exports:** `exports/profile1_campus_lan.cfg`, `exports/profile2_metro_man.cfg`, `exports/profile3_global_wan.cfg`.
* **Mandatory Audit Log:** Complete 3-case technical post-mortem in `ai_audit_log.md`.

