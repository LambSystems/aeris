import sys
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from app.context.schemas import (  # noqa: E402
    AirQualityContext,
    EnvironmentalFixedContext,
    LocationContext,
    WeatherContext,
)
from app.main import app  # noqa: E402
from app.sustainability.schemas import CASTNETReading, YOLODetection  # noqa: E402


def demo_fixed_context() -> EnvironmentalFixedContext:
    return EnvironmentalFixedContext(
        location=LocationContext(
            latitude=40.9478,
            longitude=-90.3712,
            label="Galesburg, IL",
            source="default_demo_location",
        ),
        castnet=CASTNETReading(
            site_id="BVL130",
            location="Bondville, IL",
            ozone_ppb=39.0,
            sulfate_ug_m3=0.68,
            nitrate_ug_m3=2.08,
            co_ppb=41.72,
            measurement_date="2026-04-15",
        ),
        weather=WeatherContext(temperature_c=18.2, wind_speed_kmh=12.0),
        air_quality=AirQualityContext(pm2_5_ug_m3=8.4, ozone_ug_m3=76.0),
        weather_alerts=[],
        risk_flags=["castnet_elevated_nitrate"],
        summary="Nearest CASTNET context is Bondville, IL.",
        source_status={
            "castnet": "ok",
            "weather": "ok",
            "air_quality": "ok",
            "weather_alerts": "ok",
        },
    )


class ApiContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_health_contract(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True, "service": "aeris-api"})

    def test_fixed_context_contract(self) -> None:
        with patch("app.main.load_fixed_context", return_value=demo_fixed_context()):
            response = self.client.get("/context/fixed?latitude=40.9478&longitude=-90.3712")

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["location"]["label"], "Galesburg, IL")
        self.assertEqual(payload["castnet"]["site_id"], "BVL130")
        self.assertIn("castnet_elevated_nitrate", payload["risk_flags"])
        self.assertEqual(payload["source_status"]["weather"], "ok")

    def test_sustainability_detect_uses_fallback_without_llm_keys(self) -> None:
        request = {
            "latitude": 40.9478,
            "longitude": -90.3712,
            "detection": {
                "object_class": "paper",
                "confidence": 0.91,
                "frame_id": "frame_00042",
                "timestamp": "2026-04-19T06:30:00Z",
            },
        }

        with patch("app.main.load_fixed_context", return_value=demo_fixed_context()), patch.dict(
            "os.environ",
            {"GEMINI_API_KEY": "", "ANTHROPIC_API_KEY": "", "AERIS_LLM_PROVIDER": "gemini"},
            clear=False,
        ):
            response = self.client.post("/sustainability/detect", json=request)

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["object_detected"], "paper")
        self.assertEqual(payload["decision_source"], "deterministic_fallback")
        self.assertEqual(payload["castnet_site"], "Bondville, IL")
        self.assertIn("recycling", payload["action"].lower())

    def test_latest_detection_contract(self) -> None:
        detection = YOLODetection(
            object_class="can",
            confidence=0.88,
            frame_id="frame_00012",
            timestamp="2026-04-19T06:30:00Z",
        )

        with patch("app.main.read_latest_detection", return_value=detection):
            response = self.client.get("/vision/latest-detection")

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["object_class"], "can")
        self.assertEqual(payload["confidence"], 0.88)
        self.assertEqual(payload["frame_id"], "frame_00012")


if __name__ == "__main__":
    unittest.main()
