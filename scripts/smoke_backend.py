import json
import os
import time
import urllib.error
import urllib.request


BASE_URL = os.getenv("AERIS_API_URL", "http://localhost:8000").rstrip("/")


def request_json(path: str, method: str = "GET", payload: dict | None = None) -> dict:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8")
        raise RuntimeError(f"{method} {path} failed: {error.code} {body}") from error


def main() -> None:
    health = request_json("/health")
    print(f"health: {health['ok']}")

    print(f"base_url: {BASE_URL}")

    context = request_json("/context/demo")
    print(f"context: {context['location']} / {context['risk_mode']}")

    scene = request_json("/scan-frame", method="POST")
    print(f"scan-frame: {scene['source']} / {len(scene['objects'])} objects")

    job = request_json(
        "/analyze-scene",
        method="POST",
        payload={
            "fixed_context": context,
            "dynamic_context": scene,
            "provider": "gemini",
        },
    )
    print(f"analysis job: {job['job_id']} / {job['status']}")

    final_job = job
    for _ in range(20):
        final_job = request_json(f"/analysis/{job['job_id']}")
        if final_job["status"] != "pending":
            break
        time.sleep(0.5)

    if final_job["status"] != "complete":
        raise RuntimeError(f"analysis did not complete: {final_job}")

    recommendations = final_job["recommendations"]
    top_action = recommendations["actions"][0]
    print(
        "recommendation: "
        f"{recommendations['decision_source']} -> "
        f"{top_action['action']} {top_action['target']}"
    )

    latest = request_json("/analysis/latest")
    print(f"latest: {latest['has_result']}")


if __name__ == "__main__":
    main()
