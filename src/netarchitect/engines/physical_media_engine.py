"""
Layer 1 / Layer 2 Physical Media & Distance Physics Engine.
Enforces IEEE 802.3 Ethernet standards, optical transmission link budgets,
and modal dispersion limits.
"""

from typing import List

from netarchitect.exceptions import PhysicalDistanceViolationError
from netarchitect.models.architecture_outputs import MediaRecommendation
from netarchitect.models.scenario_inputs import LinkRequest, MediumPreference


class L1L2MediaEngine:
    """
    Evaluates physical link requests against electromagnetic and optical physics:
    - IEEE 802.3an: 10GBASE-T over Category 6a Balanced Twisted-Pair Copper (<= 100m)
    - IEEE 802.3ae: 10GBASE-SR over OM4 Multimode Fiber 850nm (<= 400m)
    - IEEE 802.3ae: 10GBASE-LR over OS2 Single-Mode Fiber 1310nm (<= 10,000m)
    - IEEE 802.3ae: 10GBASE-ER over OS2 Single-Mode Fiber 1550nm (<= 40,000m)
    """

    COPPER_MAX_DISTANCE_METERS = 100.0
    OM4_MMF_MAX_DISTANCE_METERS = 400.0
    OS2_LR_MAX_DISTANCE_METERS = 10_000.0
    OS2_ER_MAX_DISTANCE_METERS = 40_000.0

    @classmethod
    def evaluate_link(cls, link: LinkRequest) -> MediaRecommendation:
        dist = link.distance_meters
        if dist <= 0:
            raise ValueError(f"Link distance must be strictly positive (> 0), got {dist}m for link '{link.link_id}'")

        # Boundary Error Check: Explicit copper request exceeding 100m
        if link.medium_preference == MediumPreference.COPPER and dist > cls.COPPER_MAX_DISTANCE_METERS:
            loss_est = (dist / 100.0) * 45.0  # Estimated copper insertion loss at high freq
            raise PhysicalDistanceViolationError(
                message=(
                    f"Physical Distance Violation on link '{link.link_id}': Requested Copper (Cat6a) for {dist}m "
                    f"exceeds the 100m IEEE 802.3an limit. Signal attenuation (~{loss_est:.1f} dB) and Alien Crosstalk "
                    f"(ANEXT) will cause total frame loss and link failure."
                ),
                distance_meters=dist,
                medium="Cat6a UTP/STP",
                max_allowed_meters=cls.COPPER_MAX_DISTANCE_METERS,
            )

        # Automatic or Fiber Media Selection Logic
        if link.medium_preference == MediumPreference.COPPER:
            # Within valid copper range (<= 100m)
            attenuation = (dist / 100.0) * 4.2  # ~4.2 dB at standard channel frequencies
            return MediaRecommendation(
                link_id=link.link_id,
                source=link.source,
                destination=link.destination,
                distance_meters=dist,
                bandwidth_gbps=link.bandwidth_gbps,
                medium_type="Category 6a (Cat6a) F/UTP",
                standard="10GBASE-T",
                wavelength_nm=0,
                max_reach_meters=cls.COPPER_MAX_DISTANCE_METERS,
                attenuation_db_est=round(attenuation, 2),
                rationale=(
                    f"Recommended Cat6a (10GBASE-T) for {dist}m run. Within IEEE 802.3an 100m electrical transmission limit. "
                    f"Supports IEEE 802.3bt Type 4 Power over Ethernet (PoE++ up to 90W) for edge devices and APs without dedicated AC lines."
                ),
            )

        # Distance <= 100m with AUTO or FIBER preference
        if dist <= cls.COPPER_MAX_DISTANCE_METERS:
            if link.medium_preference == MediumPreference.AUTO and link.role.lower() == "access":
                attenuation = (dist / 100.0) * 4.2
                return MediaRecommendation(
                    link_id=link.link_id,
                    source=link.source,
                    destination=link.destination,
                    distance_meters=dist,
                    bandwidth_gbps=link.bandwidth_gbps,
                    medium_type="Category 6a (Cat6a) F/UTP",
                    standard="10GBASE-T",
                    wavelength_nm=0,
                    max_reach_meters=cls.COPPER_MAX_DISTANCE_METERS,
                    attenuation_db_est=round(attenuation, 2),
                    rationale=(
                        f"Selected Cat6a (10GBASE-T) because link distance ({dist}m) is within the 100m horizontal cabling limit (IEEE 802.3an). "
                        f"Enables PoE++ power delivery and cost-effective RJ-45 termination for edge switches."
                    ),
                )
            else:
                # Inter-switch or backbone short-range fiber
                attenuation = (dist / 1000.0) * 3.0 + 0.5  # 3 dB/km for 850nm + connectors
                return MediaRecommendation(
                    link_id=link.link_id,
                    source=link.source,
                    destination=link.destination,
                    distance_meters=dist,
                    bandwidth_gbps=link.bandwidth_gbps,
                    medium_type="OM4 Laser-Optimized Multimode Fiber (50/125 um)",
                    standard="10GBASE-SR",
                    wavelength_nm=850,
                    max_reach_meters=cls.OM4_MMF_MAX_DISTANCE_METERS,
                    attenuation_db_est=round(attenuation, 2),
                    rationale=(
                        f"Selected OM4 MMF (10GBASE-SR) for {dist}m short-span backbone link. Eliminates electrical ground loop potential "
                        f"between chassis while utilizing low-cost 850nm VCSEL transceivers."
                    ),
                )

        # 101m - 400m: OM4 MMF
        elif dist <= cls.OM4_MMF_MAX_DISTANCE_METERS:
            attenuation = (dist / 1000.0) * 3.0 + 0.6  # 3.0 dB/km + patch panels
            return MediaRecommendation(
                link_id=link.link_id,
                source=link.source,
                destination=link.destination,
                distance_meters=dist,
                bandwidth_gbps=link.bandwidth_gbps,
                medium_type="OM4 Laser-Optimized Multimode Fiber (50/125 um)",
                standard="10GBASE-SR",
                wavelength_nm=850,
                max_reach_meters=cls.OM4_MMF_MAX_DISTANCE_METERS,
                attenuation_db_est=round(attenuation, 2),
                rationale=(
                    f"Selected OM4 Multimode Fiber (10GBASE-SR) because link distance ({dist}m) exceeds copper 100m limit but operates within "
                    f"the 400m modal dispersion limit of OM4 850nm VCSEL optics (IEEE 802.3ae). Provides cost-effective campus backbone interconnections."
                ),
            )

        # 401m - 10,000m: OS2 SMF (10GBASE-LR)
        elif dist <= cls.OS2_LR_MAX_DISTANCE_METERS:
            dist_km = dist / 1000.0
            attenuation = (dist_km * 0.4) + 0.8  # 0.4 dB/km @ 1310nm + splice/connectors
            return MediaRecommendation(
                link_id=link.link_id,
                source=link.source,
                destination=link.destination,
                distance_meters=dist,
                bandwidth_gbps=link.bandwidth_gbps,
                medium_type="OS2 Low-Water-Peak Single-Mode Fiber (9/125 um)",
                standard="10GBASE-LR",
                wavelength_nm=1310,
                max_reach_meters=cls.OS2_LR_MAX_DISTANCE_METERS,
                attenuation_db_est=round(attenuation, 2),
                rationale=(
                    f"Selected OS2 Single-Mode Fiber (10GBASE-LR) because link distance ({dist_km:.2f} km) exceeds the 400m modal dispersion limit "
                    f"of OM4 multimode fiber. Uses 1310nm Fabry-Perot/DFB laser with optical budget capable of spans up to 10 km."
                ),
            )

        # 10,001m - 40,000m: OS2 SMF (10GBASE-ER)
        elif dist <= cls.OS2_ER_MAX_DISTANCE_METERS:
            dist_km = dist / 1000.0
            attenuation = (dist_km * 0.25) + 1.2  # 0.25 dB/km @ 1550nm silica minimum loss window
            return MediaRecommendation(
                link_id=link.link_id,
                source=link.source,
                destination=link.destination,
                distance_meters=dist,
                bandwidth_gbps=link.bandwidth_gbps,
                medium_type="OS2 Low-Water-Peak Single-Mode Fiber (9/125 um)",
                standard="10GBASE-ER",
                wavelength_nm=1550,
                max_reach_meters=cls.OS2_ER_MAX_DISTANCE_METERS,
                attenuation_db_est=round(attenuation, 2),
                rationale=(
                    f"Selected OS2 Single-Mode Fiber (10GBASE-ER) because link distance ({dist_km:.2f} km) exceeds the 10 km reach of 10GBASE-LR. "
                    f"Utilizes 1550nm cooled EML laser operating in the minimum silica attenuation window (0.25 dB/km) with an optical power budget "
                    f"supporting up to 40 km metro MAN interconnects without mid-span amplification."
                ),
            )

        # > 40,000m: DWDM / Optical Amplification required
        else:
            dist_km = dist / 1000.0
            attenuation = (dist_km * 0.22) + 2.0
            return MediaRecommendation(
                link_id=link.link_id,
                source=link.source,
                destination=link.destination,
                distance_meters=dist,
                bandwidth_gbps=link.bandwidth_gbps,
                medium_type="OS2 Single-Mode Fiber with DWDM / EDFA",
                standard="10GBASE-ZR / DWDM",
                wavelength_nm=1550,
                max_reach_meters=80_000.0,
                attenuation_db_est=round(attenuation, 2),
                rationale=(
                    f"Ultra-long-haul link ({dist_km:.2f} km) exceeds 10GBASE-ER 40 km unamplified optical budget. "
                    f"Requires 1550nm DWDM transponders with Erbium-Doped Fiber Amplifiers (EDFA) and dispersion compensation modules."
                ),
            )

    @classmethod
    def evaluate_all(cls, links: List[LinkRequest]) -> List[MediaRecommendation]:
        return [cls.evaluate_link(link) for link in links]

