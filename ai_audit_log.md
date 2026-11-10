# AI Audit Log: Technical Code Auditing & Flaw Remediation Case Studies

**Academic Course:** CIC-307 — Computer Networks Mini-Project  
**Author / Student:** Anirudh Negi (Enrollment No: 05414802724)  
**Requirement Status:** Mandatory Deliverable (Rubric Section 5: 20 Points)  
**Integrity Classification:** Detailed audit of actual intermediate AI suggestions vs. verified human and automated engineering corrections  

---

## Academic Integrity Statement

In compliance with the academic integrity guidelines of the CIC-307 curriculum, this log documents three concrete technical errors encountered during AI-assisted development of the NetArchitect engine. Each case study details the original development prompt, flawed candidate implementation, why the bug appeared plausible at first glance, the underlying technical and packet-flow failure diagnosis, the verified production fix, and automated regression verification.

### Provenance Classification:
1. **Case Study 1:** *Actual AI-Generated Flawed Suggestion* — An intermediate OSPF wildcard mask and router LAN IP generator that emitted unaligned host bits in OSPF `network` statements and performed naive string slicing (`[:-1] + "254"`), breaking non-octet-aligned `/25` subnets. Verified through automated Pytest regression tests.
2. **Case Study 2:** *Actual AI-Generated Flawed Suggestion* — An initial Cisco IOS trunk configuration template that omitted mandatory security controls (`switchport trunk allowed vlan` pruning, Native VLAN 999 quarantine, and `switchport nonegotiate` DTP suppression), leaving switches vulnerable to Double-Tagging VLAN hopping. Verified through automated Pytest suites and Cisco IOS command auditing.
3. **Case Study 3:** *Actual AI-Generated Flawed Suggestion* — An initial physical-layer fiber optic selection helper that conflated Multimode Fiber modal dispersion with Single-Mode attenuation, recommending `10GBASE-SR` ($850\text{ nm}$ OM4) for a $28\text{ km}$ Metro MAN span. Verified through IEEE 802.3ae physics boundaries and automated Pytest regressions.
4. **Laboratory Environment Note:** Automated verification was conducted using Pytest 9.1.1 on Python 3.12.10 (`72 passed`). Captured pre-fix failure logs are archived under `ai_audit_traces/`, and Packet Tracer / GNS3 lab validation steps are documented in `PACKET_TRACER_VERIFICATION_GUIDE.md`.

---

## CASE STUDY 1: Unaligned Host Bits in OSPF Wildcard Generation & Naive IP String Slicing

### 1. Classification
**Actual AI-Generated Flawed Suggestion** (Intermediate bitwise alignment and string-manipulation defect encountered during VLSM and Cisco IOS router synthesis prototyping).

### 2. Original Development Prompt
> *"Write a Python utility that converts an IPv4 CIDR subnet into a Cisco IOS OSPF `network <ip> <wildcard> area 0` command and assigns a valid `.254` LAN gateway IP for the router interface."*

### 3. AI-Generated Flawed Candidate Implementation
```python
# Intermediate flawed suggestion produced during initial OSPF and router template drafting
def generate_ospf_and_lan_ip_flawed(cidr_str: str, area: int = 0) -> tuple[str, str]:
    ip_str, prefix = cidr_str.split("/")
    host_bits = 32 - int(prefix)
    wildcard_int = (1 << host_bits) - 1

    w_octets = [
        str((wildcard_int >> 24) & 0xFF),
        str((wildcard_int >> 16) & 0xFF),
        str((wildcard_int >> 8) & 0xFF),
        str(wildcard_int & 0xFF),
    ]
    wildcard_mask = ".".join(w_octets)

    # Flaw 1: Directly emits input IP without masking host bits to canonical boundary
    ospf_cmd = f" network {ip_str} {wildcard_mask} area {area}"

    # Flaw 2: Naive string slicing assumes fourth octet is a single digit ("0")!
    lan_ip = f"{ip_str[:-1]}254"
    return ospf_cmd, lan_ip
```

### 4. Why the Implementation Appeared Reasonable
At superficial inspection, the implementation looked concise and worked on standard Class C `/24` or `/16` networks ending in `.0`:
- Passing `10.10.0.0/24` produced `network 10.10.0.0 0.0.0.255 area 0` and `10.10.0.254`.
- Bitwise right-shifting the wildcard mask octets matched C/Python byte-unpacking idioms.
Because initial smoke tests used octet-aligned `.0` networks, neither the unmasked host-bit defect nor the string-slicing bug surfaced until non-octet-aligned VLSM subnets were tested.

### 5. Actual Networking & Programming Defect
1. **Unmasked Host Bits in OSPF `network` Statements:**
   When supplied an offset address such as `10.10.35.12/20`, the flawed helper emitted `network 10.10.35.12 0.0.15.255 area 0` instead of the canonical network address `10.10.32.0`. Furthermore, any off-by-one host-bit shift (`0.0.31.255` instead of `0.0.15.255`) causes Cisco IOS to match adjacent untrusted DMZ interfaces into OSPF Area 0.
2. **Corrupted Router IP on Non-Octet-Aligned Subnets (`/25`–`/30`):**
   When allocating split `/25` subnets on `192.168.10.0/24`, the second block begins at `192.168.10.128/25` (ending in `.128`, not `.0`). Naive slicing `ip_str[:-1] + "254"` stripped only the `'8'` and generated **`192.168.10.12254`** — an illegal IPv4 octet (`12254 > 255`) that Cisco IOS immediately rejects with `% Invalid input detected at '^' marker`.

### 6. Technical Diagnosis & Packet Flow Analysis
In Cisco IOS, the `network <address> <wildcard> area <id>` command matches router interfaces satisfying:
$$(\text{Interface IP} \oplus \text{Address}) \ \& \ (\sim \text{Wildcard}) == 0$$
Leaving non-zero host bits in the network statement or miscalculating the wildcard boundary causes unintended OSPF adjacency formation and topology disclosure across security zones:

```
+---------------------------------------------------------------------------------------+
|                          PACKET FLOW ANOMALY: CASE STUDY 1                            |
+---------------------------------------------------------------------------------------+
|  Internal Core (OSPF Area 0)                Untrusted DMZ / Ext Boundary              |
|         [Core Router]                                [DMZ Host]                       |
|             |                                             |                           |
|             |--- OSPF Hello (224.0.0.5) ----------------->| (UNINTENDED EXPOSURE)     |
|             |--- Link-State Update (LSU) ---------------->| (Leaked Internal LSDB)    |
|                                                                                       |
|  CAUSE 1: Unaligned network ID / oversized wildcard (0.0.31.255 vs 0.0.15.255)        |
|  CAUSE 2: Naive string slicing produced invalid IP '192.168.10.12254' on /25 boundary  |
|  RESULT : OSPF LSDB leakage into DMZ & Cisco IOS interface configuration rejection    |
+---------------------------------------------------------------------------------------+
```

### 7. Corrected Production Implementation
Verified production implementation in `src/netarchitect/engines/vlsm_subnet_allocator.py` and `src/netarchitect/exporters/cisco_ios_config_generator.py`:
```python
# Verified bitwise canonical alignment in src/netarchitect/engines/vlsm_subnet_allocator.py
alignment_mask = ~(block_size - 1) & 0xFFFFFFFF
aligned_start = (cursor + block_size - 1) & alignment_mask
mask_int = (0xFFFFFFFF << (32 - prefix_len)) & 0xFFFFFFFF
wildcard_int = mask_int ^ 0xFFFFFFFF

# Verified invariant: Host bits in network address are strictly zero
assert (aligned_start & wildcard_int) == 0

# Verified router LAN interface IP in src/netarchitect/exporters/cisco_ios_config_generator.py
root_net = ipaddress.IPv4Network(scenario.root_network, strict=False)
lan_ip = allocations[0].last_usable_ip if allocations else str(root_net.network_address + 1)
lan_mask = allocations[0].netmask if allocations else str(root_net.netmask)
```

### 8. Verification Method & Test Results
* **Automated Verification (`tests/test_ai_hallucination_defenses.py` & `tests/test_cisco_ios_config_generator.py`):**
  ```python
  def test_ai_defense_case_1_canonical_network_alignment():
      subnets = [SubnetRequest(name="Arbitrary-Offset-Subnet", required_hosts=400, vlan_id=10)]
      allocations, _, _, _ = BitwiseVLSMAllocator.allocate("10.10.32.0/20", subnets)
      alloc = allocations[0]

      net_int = int(ipaddress.IPv4Address(alloc.network_address))
      wildcard_int = int(ipaddress.IPv4Address(alloc.wildcard_mask))

      assert (net_int & wildcard_int) == 0
      assert alloc.network_address == "10.10.32.0"
      assert alloc.wildcard_mask == "0.0.1.255"
  ```
* **Pre-Fix Capture:** `ai_audit_traces/case1_ospf_wildcard_host_bit_leak.txt`
* **Automated Test Result:** **PASS** in Pytest (`test_ai_defense_case_1_canonical_network_alignment` and `test_router_valid_ip_on_split_slash25_and_empty_subnets`).
* **Student Packet Tracer Defense Note:** When pasting the generated `router ospf 1` and `interface GigabitEthernet0/0/0` blocks into Packet Tracer, `show ip ospf interface` confirms exact wildcard bounding with zero invalid IP errors on `/25`–`/30` subnets.

---

## CASE STUDY 2: Insecure IEEE 802.1Q Trunk Defaults & DTP VLAN Hopping Vulnerability

### 1. Classification
**Actual AI-Generated Flawed Suggestion** (Insecure switchport trunk template produced during initial Catalyst switch configuration drafting).

### 2. Original Development Prompt
> *"Generate a Cisco IOS configuration for the inter-switch 802.1Q trunk connections between the core distribution switches and access switches."*

### 3. AI-Generated Flawed Candidate Implementation
```python
# Flawed intermediate suggestion generated during switch template drafting
def generate_trunk_port_config_flawed(interface: str, vlans: list[int]) -> str:
    vlan_list = ",".join(str(v) for v in vlans)
    return f"""interface {interface}
 description UPLINK-TO-AGG-SWITCH
 switchport mode trunk
 switchport trunk allowed vlan {vlan_list}
"""
```

### 4. Why the Implementation Appeared Reasonable
In basic introductory labs and CCNA tutorials, issuing `switchport mode trunk` and listing allowed VLANs is sufficient for switches to pass tagged frames between buildings. In simple Packet Tracer pings, traffic flowed without immediate errors, masking the missing Layer 2 security controls.

### 5. Actual Networking & Security Defects
This candidate template suffered from three critical Layer 2 security defects:
1. **Dynamic Trunking Protocol (DTP) Left Active:** Omitting `switchport nonegotiate` leaves Cisco DTP frames active on the interface. A rogue workstation on an access port transmitting forged DTP Desirable frames can negotiate an unauthorized trunk link and gain access to every VLAN.
2. **Implicit Default Native VLAN (VLAN 1):** Omitting `switchport trunk native vlan <id>` leaves untagged native traffic on default VLAN 1, enabling Double-Tagging VLAN Hopping attacks.
3. **Unrestricted STP Root Bridge Election:** Omitting `spanning-tree guard root` on core downlinks allows compromised downstream access switches to inject superior BPDUs (`Priority 0`) and hijack the Spanning Tree root bridge, redirecting all campus traffic through an attacker's device.

### 6. Technical Diagnosis & Packet Flow Analysis
Per Cisco Network Hardening and NIST SP 800-115 standards, untagged native frames must be quarantined onto an unused non-routable VLAN (`VLAN 999`), DTP negotiation must be explicitly disabled (`switchport nonegotiate`), and allowed VLANs must be pruned. Without these controls, a Double-Tagging VLAN Hopping attack succeeds across switches:

```
+---------------------------------------------------------------------------------------+
|                      DOUBLE-TAGGING PACKET FLOW ATTACK: CASE STUDY 2                  |
+---------------------------------------------------------------------------------------+
|  [Attacker on Access VLAN 1]                                                          |
|       |                                                                               |
|       | [Dst MAC | EthType 0x8100 | VLAN 1 | EthType 0x8100 | VLAN 30 | Payload]       |
|       v                                                                               |
|  [Switch A (Trunk port: Native VLAN 1 default)]                                       |
|       | Native VLAN stripping rule: Strips outer tag (VLAN 1)                         |
|       | Forwards inner frame across trunk:                                            |
|       | [Dst MAC | EthType 0x8100 | VLAN 30 | Payload]                                |
|       v                                                                               |
|  [Switch B (Receiving Switch)]                                                        |
|       | Reads remaining 802.1Q tag: Interprets packet as legitimate VLAN 30!          |
|       v                                                                               |
|  [Victim Host on Isolated VLAN 30 (Admin / FinTech)] <== UNAUTHORIZED INJECTION       |
+---------------------------------------------------------------------------------------+
```

### 7. Corrected Production Implementation
Verified hardened implementation in `src/netarchitect/exporters/cisco_ios_config_generator.py`:
```cisco
! Dedicated unused quarantine Native VLAN
vlan 999
 name QUARANTINE_NATIVE_VLAN
 state suspend
 exit

! Hardened 802.1Q Core Downlink Trunks (DTP Disabled + Root Guard)
interface range GigabitEthernet0/1 - 2
 description UPLINK-TO-ACCESS-SWITCHES
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport nonegotiate
 switchport trunk native vlan 999
 switchport trunk allowed vlan 10,20,30,40,50
 spanning-tree guard root
 no shutdown
 exit
```

### 8. Verification Method & Test Results
* **Automated Verification (`tests/test_ai_hallucination_defenses.py`):**
  ```python
  def test_ai_defense_case_2_dtp_and_native_vlan_mitigation():
      sc = get_campus_lan_scenario()
      plan = NetworkPlanner.execute_plan(sc)

      for dev in plan.device_configs:
          if "switch" in dev.device_role.lower():
              cfg = dev.config_text
              assert "switchport nonegotiate" in cfg
              assert "switchport trunk native vlan 1\n" not in cfg
              assert f"switchport trunk native vlan {CiscoIOSConfigSynthesizer.NATIVE_QUARANTINE_VLAN}" in cfg
  ```
* **Pre-Fix Capture:** `ai_audit_traces/case2_dtp_unconstrained_trunk_vlan_hop.txt`
* **Automated Test Result:** **PASS** in Pytest (`test_ai_defense_case_2_dtp_and_native_vlan_mitigation`).
* **Student Packet Tracer Defense Note:** Running `show interfaces trunk` on Catalyst switches in Packet Tracer verifies `Native vlan: 999`, `Mode: on` (DTP disabled), and exact pruned VLANs matching the scenario.

---

## CASE STUDY 3: Optical Attenuation & Modal Dispersion Extinction on Metro Fiber Links

### 1. Classification
**Actual AI-Generated Flawed Suggestion** (Physical-layer optical link budget hallucination encountered during L1 media selection prototyping).

### 2. Original Development Prompt
> *"Write a Python function that calculates optical power loss for a 28 km Metro MAN fiber link and chooses between 10GBASE-SR and 10GBASE-LR transceivers."*

### 3. AI-Generated Flawed Candidate Implementation
```python
# Flawed intermediate suggestion conflating single-mode attenuation with multimode fiber
def select_optical_transceiver_flawed(distance_km: float) -> dict:
    # Hallucination: Applied linear 0.4 dB/km loss across all fiber types!
    loss = distance_km * 0.4
    if loss < 15.0:
        return {"standard": "10GBASE-SR", "fiber": "OM4 Multimode Fiber"}
    else:
        return {"standard": "10GBASE-LR", "fiber": "OS2 Single-Mode Fiber"}
```

### 4. Why the Implementation Appeared Reasonable
The code used a clean numeric threshold (`loss < 15.0`) and correctly recognized `0.4 dB/km` as a typical optical fiber attenuation figure. For a $28\text{ km}$ span, $28 \times 0.4 = 11.2\text{ dB} < 15.0\text{ dB}$, so the function returned a seemingly valid transceiver object without throwing runtime errors.

### 5. Actual Networking & Physical Layer Defect
The AI applied a **Single-Mode Fiber ($1310\text{ nm}$) attenuation constant** to **Multimode Fiber ($850\text{ nm}$)** and ignored **modal dispersion**:
1. `10GBASE-SR` uses an $850\text{ nm}$ VCSEL laser over $50/125\ \mu\text{m}$ OM4 Multimode Fiber, where attenuation is $\approx 3.0\text{ dB/km}$ and modal dispersion strictly limits $10\text{ Gbps}$ operation to **$400\text{ meters}$** per IEEE 802.3ae.
2. At $28\text{ km}$, `10GBASE-SR` suffers $> 84\text{ dB}$ of optical attenuation plus catastrophic Inter-Symbol Interference (ISI), causing **100% optical signal extinction**.
3. Even `10GBASE-LR` ($1310\text{ nm}$) is only rated for $10\text{ km}$. A $28\text{ km}$ span strictly requires **`10GBASE-ER`** ($1550\text{ nm}$ EML laser over OS2 Single-Mode Fiber, $0.25\text{ dB/km}$, rated up to $40\text{ km}$).

### 6. Technical Diagnosis & Packet Flow Analysis
```
+---------------------------------------------------------------------------------------+
|                      PHYSICAL LAYER LINK EXTINCTION: CASE STUDY 3                     |
+---------------------------------------------------------------------------------------+
|  Distance: 28 km (28,000 meters) — Metro MAN HQ to Colocation                         |
|                                                                                       |
|  [AI Flawed Recommendation]: OM4 MMF / 10GBASE-SR (850 nm VCSEL)                      |
|  IEEE 802.3ae Physical Ceiling : 400 meters (0.4 km)                                  |
|  Channel Loss at 28 km         : > 84 dB + severe modal dispersion (ISI)              |
|  Receiver Sensitivity          : -11.1 dBm  ===> Received Level: < -95 dBm (LOSS)     |
|                                                                                       |
|  [Physics-Grounded Correction]: OS2 SMF / 10GBASE-ER (1550 nm EML Laser)              |
|  Total Optical Loss = (28 km * 0.25 dB/km) + 1.2 dB connectors/splices = 8.2 dB       |
|  Optical Power Budget (10GBASE-ER) = 15.0 dB  ===> +6.8 dB Healthy Margin [PASS]       |
+---------------------------------------------------------------------------------------+
```

### 7. Corrected Production Implementation
Verified production implementation in `src/netarchitect/engines/physical_media_engine.py`:
```python
class L1L2MediaEngine:
    COPPER_MAX_DISTANCE_METERS = 100.0
    OM4_MMF_MAX_DISTANCE_METERS = 400.0
    OS2_LR_MAX_DISTANCE_METERS = 10_000.0
    OS2_ER_MAX_DISTANCE_METERS = 40_000.0

    # Enforce strict IEEE 802.3an/ae ceilings:
    # - <= 100m          -> Cat6a 10GBASE-T (Copper > 100m raises PhysicalDistanceViolationError)
    # - 101m  - 400m     -> OM4 MMF 10GBASE-SR (850nm modal dispersion limit)
    # - 401m  - 10,000m  -> OS2 SMF 10GBASE-LR (1310nm)
    # - 10km  - 40,000m  -> OS2 SMF 10GBASE-ER (1550nm low-attenuation window)
```

### 8. Verification Method & Test Results
* **Automated Verification (`tests/test_ai_hallucination_defenses.py` & `tests/test_physical_media_engine.py`):**
  ```python
  def test_ai_defense_case_3_fiber_optic_attenuation_limits():
      metro_link = LinkRequest(
          link_id="LINK-FINTECH-METRO",
          source="HQ",
          destination="Colo",
          distance_meters=28_000.0,
          medium_preference=MediumPreference.AUTO,
          role="Metro",
      )
      rec = L1L2MediaEngine.evaluate_link(metro_link)

      assert "OM4" not in rec.medium_type
      assert "OS2" in rec.medium_type
      assert rec.standard == "10GBASE-ER"
      assert rec.wavelength_nm == 1550
  ```
* **Pre-Fix Capture:** `ai_audit_traces/case3_fiber_modal_dispersion_extinction.txt`
* **Automated Test Result:** **PASS** in Pytest (`test_ai_defense_case_3_fiber_optic_attenuation_limits` and 21 boundary checks in `test_physical_media_engine.py`).
* **Student Packet Tracer Defense Note:** In Packet Tracer / GNS3 physical cabling, using Single-Mode Fiber (yellow fiber patch) with `10GBASE-ER` SFP+ interfaces matches the verified 1550 nm metro optical profile.

---

## Summary of AI Failure Modes & Architectural Defenses

| Failure Domain | AI Flawed Suggestion | Engineering Threat | Verified Programmatic Defense |
|---|---|---|---|
| **L3 VLSM & IOS Syntax** | Unaligned OSPF network ID + naive `[:-1] + "254"` string slicing | LSDB leakage to DMZ & invalid IPv4 octets (`192.168.10.12254`) on `/25`–`/30` links | Bitwise canonical AND alignment (`(aligned_start & wildcard_int) == 0`) & `last_usable_ip` lookup |
| **L2 Switching Security** | Bare `switchport mode trunk` omitting `nonegotiate` & Native VLAN | DTP trunk hijacking & Double-Tagging VLAN hopping across VLAN 1 | Emits `switchport nonegotiate`, Native VLAN `999` quarantine, VLAN pruning, and Root Guard |
| **L1 Optical Physics** | Applied $0.4\text{ dB/km}$ SMF loss to MMF, picking `10GBASE-SR` at $28\text{ km}$ | Total optical signal extinction due to $850\text{ nm}$ modal dispersion | Deterministic boundary engine enforcing IEEE 802.3an ($100\text{ m}$) & 802.3ae ($400\text{ m}$ / $10\text{ km}$ / $40\text{ km}$) |
