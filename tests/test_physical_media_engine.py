"""
Unit tests for Layer 1 / Layer 2 Physical Media & Distance Physics Engine.
Verifies IEEE 802.3an/ae standards, exact boundary thresholds, and PhysicalDistanceViolationError triggers.
"""

import pytest
from pydantic import ValidationError
from netarchitect.models.scenario_inputs import LinkRequest, MediumPreference
from netarchitect.engines.physical_media_engine import L1L2MediaEngine
from netarchitect.exceptions import PhysicalDistanceViolationError


def test_copper_cat6a_valid_within_100m():
    link = LinkRequest(
        link_id="LINK-ACCESS-50M",
        source="IDF-1",
        destination="Endpoint",
        distance_meters=50.0,
        medium_preference=MediumPreference.COPPER,
        role="Access",
    )
    rec = L1L2MediaEngine.evaluate_link(link)
    assert "Cat6a" in rec.medium_type
    assert rec.standard == "10GBASE-T"
    assert rec.wavelength_nm == 0
    assert "802.3an" in rec.rationale


def test_copper_cat6a_exact_100m_boundary_succeeds():
    link = LinkRequest(
        link_id="LINK-ACCESS-100M",
        source="IDF-1",
        destination="Endpoint",
        distance_meters=100.0,
        medium_preference=MediumPreference.COPPER,
        role="Access",
    )
    rec = L1L2MediaEngine.evaluate_link(link)
    assert rec.standard == "10GBASE-T"
    assert rec.max_reach_meters == 100.0


@pytest.mark.parametrize("bad_distance", [100.01, 101.0, 145.0, 400.0, 5000.0])
def test_copper_over_100m_raises_physical_distance_violation(bad_distance):
    link = LinkRequest(
        link_id="LINK-ILLEGAL-COPPER",
        source="IDF",
        destination="Remote-Building",
        distance_meters=bad_distance,
        medium_preference=MediumPreference.COPPER,
        role="Access",
    )
    with pytest.raises(PhysicalDistanceViolationError) as exc_info:
        L1L2MediaEngine.evaluate_link(link)

    err = exc_info.value
    assert err.distance_meters == bad_distance
    assert err.max_allowed_meters == 100.0
    assert "Cat6a" in err.medium
    assert "100m IEEE 802.3an limit" in str(err)


@pytest.mark.parametrize("distance_m", [100.01, 250.0, 400.0])
def test_om4_multimode_selected_for_101m_to_400m_backbone(distance_m):
    link = LinkRequest(
        link_id="LINK-BACKBONE-OM4",
        source="Core",
        destination="Building-B",
        distance_meters=distance_m,
        medium_preference=MediumPreference.AUTO,
        role="Backbone",
    )
    rec = L1L2MediaEngine.evaluate_link(link)
    assert "OM4" in rec.medium_type
    assert rec.standard == "10GBASE-SR"
    assert rec.wavelength_nm == 850
    assert "modal dispersion" in rec.rationale.lower()


@pytest.mark.parametrize("distance_m", [400.01, 5_000.0, 10_000.0])
def test_os2_singlemode_10gbase_lr_selected_for_401m_to_10km(distance_m):
    link = LinkRequest(
        link_id="LINK-METRO-LR",
        source="HQ",
        destination="Branch-A",
        distance_meters=distance_m,
        medium_preference=MediumPreference.AUTO,
        role="Metro",
    )
    rec = L1L2MediaEngine.evaluate_link(link)
    assert "OS2" in rec.medium_type
    assert rec.standard == "10GBASE-LR"
    assert rec.wavelength_nm == 1310


@pytest.mark.parametrize("distance_m", [10_000.01, 22_000.0, 40_000.0])
def test_os2_singlemode_10gbase_er_selected_for_10km_to_40km(distance_m):
    link = LinkRequest(
        link_id="LINK-METRO-ER",
        source="HQ",
        destination="Colo-Remote",
        distance_meters=distance_m,
        medium_preference=MediumPreference.AUTO,
        role="Metro",
    )
    rec = L1L2MediaEngine.evaluate_link(link)
    assert "OS2" in rec.medium_type
    assert rec.standard == "10GBASE-ER"
    assert rec.wavelength_nm == 1550


def test_dwdm_amplified_selected_beyond_40km():
    link = LinkRequest(
        link_id="LINK-LONG-HAUL",
        source="NYC",
        destination="London",
        distance_meters=40_000.01,
        medium_preference=MediumPreference.FIBER,
        role="WAN",
    )
    rec = L1L2MediaEngine.evaluate_link(link)
    assert "DWDM" in rec.medium_type
    assert rec.standard == "10GBASE-ZR / DWDM"


def test_negative_and_zero_distance_rejected():
    with pytest.raises(ValidationError):
        LinkRequest(link_id="NEG", source="A", destination="B", distance_meters=-10.0)

    with pytest.raises(ValidationError):
        LinkRequest(link_id="ZERO", source="A", destination="B", distance_meters=0.0)

    bypassed = LinkRequest.model_construct(
        link_id="BYPASS",
        source="A",
        destination="B",
        distance_meters=0.0,
        bandwidth_gbps=10.0,
        medium_preference=MediumPreference.AUTO,
        role="Access",
    )
    with pytest.raises(ValueError, match="strictly positive"):
        L1L2MediaEngine.evaluate_link(bypassed)
