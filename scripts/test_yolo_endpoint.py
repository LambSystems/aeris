import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def test_scan_frame_fixture_fallback() -> None:
    client = TestClient(app)
    response = client.post("/scan-frame")
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "yolo_fixture"
    assert len(data["objects"]) > 0


def test_scan_frame_upload_does_not_crash_without_yolo() -> None:
    client = TestClient(app)
    response = client.post(
        "/scan-frame",
        files={"file": ("bad.jpg", b"not an image", "image/jpeg")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["source"] in {"yolo_live", "yolo_unavailable_fallback"}
    assert "objects" in data


def run_tests() -> None:
    tests = [
        test_scan_frame_fixture_fallback,
        test_scan_frame_upload_does_not_crash_without_yolo,
    ]
    for test in tests:
        test()
        print(f"pass: {test.__name__}")


if __name__ == "__main__":
    run_tests()
