import json
import urllib.request
from typing import Any


DEFAULT_TIMEOUT_SECONDS = 4
USER_AGENT = "AerisHackathon/0.1 (https://github.com)"


def get_json(url: str, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))
