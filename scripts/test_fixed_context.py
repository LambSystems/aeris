import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from app.context.fixed_context_service import load_fixed_context  # noqa: E402
from app.main import app  # noqa: E402


def test_fixed_context_loads_castnet() -> None:
    context = load_fixed_context()
    assert context.castnet.site_id == "BVL130"
    assert context.castnet.location == "Bondville, IL"
    assert "castnet" in context.source_status
    assert context.summary


def test_fixed_context_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/context/fixed?latitude=40.9478&longitude=-90.3712")
    assert response.status_code == 200
    data = response.json()
    assert data["castnet"]["site_id"] == "BVL130"
    assert "risk_flags" in data
    assert "source_status" in data


def test_detect_response_includes_environment_context() -> None:
    client = TestClient(app)
    response = client.post(
        "/sustainability/detect",
        json={
            "latitude": 40.9478,
            "longitude": -90.3712,
            "detection": {
                "object_class": "plastic_bottle",
                "confidence": 0.95,
                "frame_id": "frame_1",
                "timestamp": "2026-04-19T10:30:00Z",
            },
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["object_detected"] == "plastic_bottle"
    assert data["environment_summary"]
    assert data["castnet_site"] == "Bondville, IL"


def run_tests() -> None:
    tests = [
        test_fixed_context_loads_castnet,
        test_fixed_context_endpoint,
        test_detect_response_includes_environment_context,
    ]
    for test in tests:
        test()
        print(f"pass: {test.__name__}")


if __name__ == "__main__":
    run_tests()
