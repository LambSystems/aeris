from app.sustainability.schemas import CASTNETReading


def load_mock_castnet() -> CASTNETReading:
    """Simulates a CASTNET reading for a northeastern US monitoring site."""
    return CASTNETReading(
        site_id="NE11",
        location="Boston, MA (urban periphery)",
        ozone_ppb=54.2,
        sulfate_ug_m3=2.8,
        nitrate_ug_m3=1.6,
        co_ppb=210.0,
        measurement_date="2026-04-18",
    )
