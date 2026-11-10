# NetArchitect: Viva Defense & Technical Examination Guide (`_DEFENSE_GUIDE.md`)

**Course Code:** CIC-307 • Computer Networks Mini-Project  
**Evaluation Weight:** 100 Points + Oral Examination  
**Topic:** Algorithmic Network Planning & Self-Explaining Architecture Engine  
**Lead Architect & Validator:** Anirudh Negi (05414802724)  

---

## 1. Physical Layer (L1) & Transmission Media Physics

### Q1: Why is OM4 multimode fiber strictly limited to 400 meters for 10GBASE-SR?
**Answer:** At the $850\text{ nm}$ operating wavelength, Multimode Fiber (MMF with a $50/125\ \mu\text{m}$ core) experiences severe **modal dispersion**. Because multiple spatial modes of light propagate along different paths down the core, light pulses spread out over time, causing **Inter-Symbol Interference (ISI)**. OM4 fiber has an Effective Modal Bandwidth (EMB) of $4700\text{ MHz}\cdot\text{km}$. Per **IEEE 802.3ae**, this modal bandwidth limit caps $10\text{ Gbps}$ transmission at exactly **$400\text{ meters}$** before the Bit Error Rate (BER) exceeds $10^{-12}$. For distances $> 400\text{ m}$, single-mode fiber (OS2) is mandatory.

### Q2: Why does Cat6a copper have an absolute limit of 100 meters under IEEE 802.3an?
**Answer:** Copper transmission at $10\text{ Gbps}$ requires high-frequency signaling up to $500\text{ MHz}$. At these frequencies, Cat6a balanced twisted-pair cable suffers from:
1. **Skin effect and dielectric loss**, causing insertion loss to scale exponentially with distance.
2. **Alien Crosstalk (ANEXT)**: High-frequency electromagnetic coupling between adjacent cable jackets in a bundle.
Per **IEEE 802.3an** and **ANSI/TIA-568-C.2**, the insertion loss budget ($< 45\text{ dB}$) and Power Sum Alien Near-End Crosstalk (PS-ANEXT) margins limit horizontal structured cabling to a **$90\text{ m}$ solid-conductor link plus $10\text{ m}$ total patch cord length ($100\text{ m}$ total channel)**. Attempting to run copper beyond 100m causes total packet extinction.

### Q3: What is the optical power budget equation for single-mode fiber (OS2)?
**Answer:** The link loss budget is calculated as:
$$\text{Loss}_{\text{total}} = (\text{Distance}_{\text{km}} \times \alpha) + (N_{\text{connectors}} \times \text{Loss}_{\text{conn}}) + (N_{\text{splices}} \times \text{Loss}_{\text{splice}}) + \text{Margin}_{\text{safety}}$$
Where:
* $\alpha = 0.4\text{ dB/km}$ at $1310\text{ nm}$ (10GBASE-LR) or $0.25\text{ dB/km}$ at $1550\text{ nm}$ (10GBASE-ER).
* Connector loss is typically $0.5\text{ dB}$ per mated pair.
* Safety margin is typically $2.0\text{–}3.0\text{ dB}$.
For 10GBASE-LR, the transceiver power budget is $6.0\text{ dB}$ ($10\text{ km}$ reach). For 10GBASE-ER, the budget is $15.0\text{ dB}$ ($40\text{ km}$ reach).

---

## 2. Layer 2 Switching, Spanning Tree & VLAN Security

### Q4: How does IEEE 802.1w Rapid Spanning Tree Protocol (RSTP) achieve sub-second convergence compared to legacy IEEE 802.1D?
**Answer:** Legacy 802.1D relies on passive timers (Listening = 15s, Learning = 15s, Max Age = 20s), resulting in **30 to 50 seconds** of service interruption during topology changes. IEEE 802.1w (Rapid-PVST+) achieves sub-second convergence ($< 1\text{ s}$) by:
1. Converting point-to-point inter-switch links to an active **Proposal/Agreement handshake**, immediately promoting an Alternate/Root port to Forwarding without timers.
2. Designating host-facing edge ports with **PortFast**, transitioning them to Forwarding in zero seconds while suppressing Topology Change Notifications (TCNs).

### Q5: What is the security threat of Dynamic Trunking Protocol (DTP) and how does NetArchitect mitigate it?
**Answer:** By default, Cisco Catalyst switchports run DTP (Dynamic Auto or Desirable). An attacker connected to an access port can transmit spoofed DTP negotiation frames to trick the switch into forming a trunk link. Once trunked, the attacker receives broadcast and unknown unicast frames for all VLANs. NetArchitect explicitly hardens every trunk port by emitting:
```cisco
switchport mode trunk
switchport nonegotiate
```
Disabling DTP completely prevents unauthorized trunk formation.

### Q6: Explain the Double-Tagging VLAN Hopping attack and why NetArchitect isolates the Native VLAN to VLAN 999.
**Answer:** In 802.1Q trunking, frames matching the Native VLAN are transmitted **untagged**. If Native VLAN 1 is active:
1. An attacker on VLAN 1 crafts a frame with two 802.1Q tags: Outer = VLAN 1, Inner = Target VLAN 30.
2. The first switch strips the outer VLAN 1 tag (because it matches the native VLAN) and forwards the frame untagged across the trunk with the inner tag intact.
3. The receiving switch inspects the remaining inner tag (VLAN 30) and forwards the packet into VLAN 30.
NetArchitect prevents this by setting a dedicated, unused, non-routable Native VLAN (`switchport trunk native vlan 999`) and ensuring VLAN 999 is never assigned to any access port.

---

## 3. Layer 3 Bitwise VLSM Subnetting Mathematics

### Q7: Why must the VLSM host calculation always add $+2$ to the requested host capacity?
**Answer:** In standard IPv4 classless subnetting (RFC 791 / RFC 4632):
* An address with all host bits set to `0` is mathematically reserved as the **Network Identifier** (base address).
* An address with all host bits set to `1` is mathematically reserved as the **Directed Broadcast Address**.
Therefore, for $H$ required usable host machines, the subnet block size must be:
$$N_{\text{addresses}} \ge H + 2 \implies \text{Prefix Length } p = 32 - \lceil \log_2(H + 2) \rceil$$
*(Exception: Point-to-point router links per RFC 3021 use prefix `/31` where Network and Broadcast are not required).*

### Q8: Why must subnets be sorted in descending order of host requirements before allocation?
**Answer:** Bitwise boundary alignment requires that a subnet block of size $2^k$ start at an address that is an exact multiple of $2^k$ ($A \pmod{2^k} == 0$). 
If smaller subnets are allocated first, they fragment the address space, leaving gaps where large blocks cannot fit without violating boundary alignment or causing massive address wastage. Sorting descending guarantees optimal prefix packing with zero internal fragmentation.

### Q9: How is the Wildcard Mask computed and why is it used in Cisco OSPF statements instead of the subnet mask?
**Answer:** The wildcard mask is computed as the 32-bit unsigned bitwise NOT of the subnet mask:
$$\text{Wildcard} = \text{SubnetMask} \oplus \text{0xFFFFFFFF}$$
In Cisco IOS, `network <address> <wildcard> area <area>` is an interface-matching filter:
$$(\text{Interface IP} \oplus \text{Address}) \ \& \ (\sim \text{Wildcard}) == 0$$
Where `0` bits in the wildcard mean *must match exactly* and `1` bits mean *ignore*. NetArchitect enforces canonical bitwise alignment so host bits are never set in the base network address.

---

## 4. Layer 3 Routing & Autonomous System Boundaries

### Q10: When should an enterprise use OSPF Area 0 vs Multi-Area OSPF vs eBGP?
**Answer:**
1. **OSPF Single-Area (Area 0)**: Best for networks with $< 50$ subnets within a single autonomous system. Minimizes configuration complexity and runs Dijkstra's Shortest Path First (SPF) algorithm in $< 200\text{ ms}$.
2. **Multi-Area OSPF**: Recommended when subnet count exceeds 50 or spans multiple physical campuses. Area Border Routers (ABRs) summarize routes into Area 0, preventing link flaps in one area from triggering SPF recalculations across the rest of the enterprise.
3. **eBGP (RFC 4271)**: Mandatory at autonomous system boundaries (e.g., connecting to AWS Cloud Transit Gateway or ISP). BGP provides path-vector policy routing, AS-Path loop prevention, and administrative domain isolation.

---

## 5. AI Defense & Academic Integrity Post-Mortem

### Q11: Describe a real AI hallucination caught during development and how NetArchitect defends against it.
**Answer:** Generative AI suggested generating OSPF network statements by taking raw interface strings (e.g. `10.10.35.12/20`) and naively inverting the prefix length without zeroing the host bits. This produced `network 10.10.35.12 0.0.15.255 area 0`. In Cisco IOS, this causes parser rejections or unintentional interface matching across adjacent subnets. 
NetArchitect defends against this by performing pure 32-bit unsigned masking:
```python
net_int = int(net.network_address)
mask_int = int(net.netmask)
wildcard_int = mask_int ^ 0xFFFFFFFF
assert (net_int & wildcard_int) == 0  # Guarantees host bits are strictly zero
```
All defenses are verified via `pytest tests/test_ai_hallucination_defenses.py`.

