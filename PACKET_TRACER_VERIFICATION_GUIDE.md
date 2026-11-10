# NetArchitect: Cisco Packet Tracer & GNS3 Verification Manual

**Course Code:** CIC-307 • Computer Networks Mini-Project  
**Author:** Anirudh Negi (05414802724)  
**Deliverable:** Verification Exports & Simulation Guide (Section 6)  

---

## 1. Overview

NetArchitect exports production-grade Cisco IOS configurations specifically tuned and tested for:
1. **Cisco Packet Tracer** (v7.3, v8.x, v8.2+)
2. **GNS3 / EVE-NG** (Cisco c3725, c7200, IOSv-L2, IOSv-L3, and Catalyst 9000v)

This manual provides the step-by-step procedures for importing and verifying the three preset scenario configurations exported by NetArchitect:
* `exports/profile1_campus_lan.cfg`
* `exports/profile2_metro_man.cfg`
* `exports/profile3_global_wan.cfg`

---

## 2. Profile 1: Campus LAN Verification (Packet Tracer)

### Topology Setup
* **Core/Distribution Switch:** Cisco Catalyst 3650-24PS or 3560-24PS (Multilayer Switch).
* **Access Switches:** 2x Cisco Catalyst 2960-24TT (Building B Academic, Building C Dormitory).
* **Endpoints:** 4x PCs / Laptops placed in respective VLANs (VLAN 10: Faculty, VLAN 20: Students, VLAN 30: VoIP, VLAN 40: IoT/Lab).

```
                 [Core-Switch-3650] (L3 Distribution / SVI Gateway)
                        /                  \
   (OM4 MMF / 10G Trunk)                    (OM4 MMF / 10G Trunk)
                      /                      \
        [Access-BldgB-2960]               [Access-BldgC-2960]
             /        \                        /        \
        [Faculty]   [Student]               [VoIP]     [IoT AP]
        (VLAN 10)   (VLAN 20)              (VLAN 30)   (VLAN 40)
```

### Loading the Configuration
1. Open Cisco Packet Tracer and drop the devices according to the diagram above.
2. Interconnect the switches:
   * Core `Gig0/1` $\leftrightarrow$ BldgB `Gig0/1`
   * Core `Gig0/2` $\leftrightarrow$ BldgC `Gig0/1`
3. Click on **Core-Switch-3650** $\rightarrow$ **CLI** tab.
4. Open `exports/profile1_campus_lan.cfg` in a text editor, copy the entire configuration block, and paste directly into the CLI prompt.
5. Hit `Enter` to ensure the final `end` and `write memory` commands execute.

### Validation Commands & Expected Output

#### 1. Verify VLAN Database & SVIs
```cisco
Core-Switch# show ip interface brief | include Vlan
Vlan1                  unassigned      YES manual administratively down down    
Vlan10                 10.10.0.1       YES manual up                    up      
Vlan20                 10.10.4.1       YES manual up                    up      
Vlan30                 10.10.6.1       YES manual up                    up      
Vlan40                 10.10.7.1       YES manual up                    up      
Vlan999                unassigned      YES manual up                    up      
```
* **Success Criteria:** All configured SVIs are in the `up/up` operational state with the calculated VLSM gateway IP addresses.

#### 2. Verify Spanning Tree Protocol (Rapid PVST+)
```cisco
Core-Switch# show spanning-tree summary
Switch is in rapid-pvst mode
Root bridge for: VLAN0010, VLAN0020, VLAN0030, VLAN0040
```
* **Success Criteria:** Rapid-PVST is active; Core Switch is recognized as the root bridge.

#### 3. Verify Trunking & Native VLAN Quarantine
```cisco
Core-Switch# show interfaces trunk
Port        Mode             Encapsulation  Status        Native vlan
Gi0/1       on               802.1q         trunking      999
Gi0/2       on               802.1q         trunking      999

Port        Vlans allowed on trunk
Gi0/1       10,20,30,40
Gi0/2       10,20,30,40
```
* **Success Criteria:** Native VLAN is set to quarantine VLAN 999 (not VLAN 1), and trunk pruning is active.

#### 4. End-to-End Ping Test
* From PC in VLAN 10 (`10.10.0.15`), execute:
  ```shell
  ping 10.10.4.1   # Default Gateway of VLAN 20
  ping 10.10.4.50  # Host in VLAN 20
  ```
* **Success Criteria:** 100% ICMP echo reply success, proving inter-VLAN routing across SVIs.

---

## 3. Profile 2: Metro MAN Verification (Packet Tracer / GNS3)

### Topology Setup
* **HQ Core Router:** Cisco ISR 4331 or 2911.
* **Remote Colo A Router (18 km):** Cisco ISR 4331 or 2911.
* **Remote Colo B Router (32 km):** Cisco ISR 4331 or 2911.
* **Connections:** Dual-homed fiber links simulating EVPL metro links.

```
                  [HQ-Core-Router] (OS2 10GBASE-LR/ER)
                     /         \
          (18 km Link)         (32 km Link)
                   /             \
        [Colo-A-Router] <=======> [Colo-B-Router]
                        (Failover Ring)
```

### Loading the Configuration
1. Open `exports/profile2_metro_man.cfg`.
2. Apply the respective blocks to HQ Router, Colo A Router, and Colo B Router.

### Validation Commands & Expected Output

#### 1. Verify OSPF Neighbor Adjacency
```cisco
HQ-Router# show ip ospf neighbor
Neighbor ID     Pri   State           Dead Time   Address         Interface
172.16.1.2        1   FULL/BDR        00:00:36    172.16.0.2      GigabitEthernet0/0/1
172.16.2.2        1   FULL/DR         00:00:34    172.16.0.6      GigabitEthernet0/0/2
```
* **Success Criteria:** Neighbor states reach `FULL/DR` or `FULL/BDR` in sub-second to low single-digit seconds, establishing link-state database synchronization.

#### 2. Verify IP Route Table & Subnet Mask Correctness
```cisco
HQ-Router# show ip route ospf
     172.16.0.0/12 is variably subnetted, 8 subnets, 4 masks
O       172.16.8.0/21 [110/2] via 172.16.0.2, 00:04:12, GigabitEthernet0/0/1
O       172.16.16.0/22 [110/2] via 172.16.0.6, 00:03:55, GigabitEthernet0/0/2
```
* **Success Criteria:** Zero overlapping routes; non-contiguous prefixes resolved via canonical bitwise wildcard masks.

#### 3. Test Failover Convergence
* Administratively shut down `GigabitEthernet0/0/1` on HQ:
  ```cisco
  HQ-Router(config)# interface Gi0/0/1
  HQ-Router(config-if)# shutdown
  ```
* Observe routing table immediately reconverging via Colo B failover link:
  ```cisco
  HQ-Router# show ip route 172.16.8.0
  Routing entry for 172.16.8.0/21
    Known via "ospf 1", distance 110, metric 3
    Routing Descriptor Blocks:
    * via 172.16.0.6, GigabitEthernet0/0/2
  ```

---

## 4. Profile 3: Global WAN Verification (GNS3 / Cisco Packet Tracer)

### Topology Setup
* **4 Edge Routers:** NYC-HQ, LON-Branch, TKO-Branch, FRA-Branch.
* **1 Cloud Border Gateway:** AWS-VPC-GW.
* **WAN Protocol:** Multi-Area OSPF with BGP peering to Autonomous System 65000 (Cloud VPC).

```
                      +-------------------+
                      |   AWS-VPC-GW      |
                      |   (AS 65000)      |
                      +-------------------+
                                ^
                                | (eBGP Peering)
                                v
+-------------+      +-------------------+      +-------------+
| LON-Branch  |<---->|   NYC-HQ-Core     |<---->| TKO-Branch  |
| (Area 10)   |      |  (OSPF Area 0)    |      | (Area 20)   |
+-------------+      +-------------------+      +-------------+
                                ^
                                |
                                v
                     +-------------------+
                     |   FRA-Branch      |
                     |   (Area 30)       |
                     +-------------------+
```

### Validation Commands & Expected Output

#### 1. Verify eBGP Peering with Cloud VPC
```cisco
NYC-HQ-Router# show ip bgp summary
BGP router identifier 10.200.0.1, local AS number 65001
BGP table version is 5, main routing table version 5
4 network entries using 992 bytes of memory

Neighbor        V           AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd
198.51.100.2    4        65000     142     145        5    0    0 01:14:22        2
```
* **Success Criteria:** BGP session state is established (`State/PfxRcd` shows numeric count $\ge 1$, not `Active` or `Idle`).

#### 2. Verify Multi-Area Route Summarization
```cisco
NYC-HQ-Router# show ip route ospf | include IA
O IA    10.200.16.0/20 [110/20] via 10.200.1.2, GigabitEthernet0/0/1
O IA    10.200.32.0/20 [110/20] via 10.200.2.2, GigabitEthernet0/0/2
```
* **Success Criteria:** Routes from Area 10 and Area 20 appear as Inter-Area (`O IA`) summaries, keeping the Area 0 link-state database minimal and isolated from remote edge flapping.

---

## 5. Troubleshooting Matrix

| Symptom | Root Cause | Remediation in NetArchitect |
|---|---|---|
| **OSPF stuck in `INIT` or `EXSTART`** | MTU mismatch or unaligned wildcard mask in `network` statement | Ensure interface MTU matches across link; use NetArchitect canonical bitwise wildcard generator. |
| **VLAN frames dropped on trunk** | Trunk port native VLAN mismatch or pruned VLAN | Ensure `switchport trunk native vlan 999` and `switchport trunk allowed vlan` contain all active VLANs. |
| **Packet Tracer CLI error on `nonegotiate`** | Some older PT switch models default to auto-trunk | Issue `switchport mode trunk` prior to `switchport nonegotiate`. |
| **Optical link down in GNS3 / PT** | Simulated fiber cable mismatch (Single-mode vs Multimode) | Use Yellow patch cables for SMF (10GBASE-LR/ER) and Orange patch cables for MMF (10GBASE-SR). |

