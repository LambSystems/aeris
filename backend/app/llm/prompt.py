import json
import re

from pydantic import ValidationError

from app.schemas import (
    DecisionSource,
    DynamicContext,
    FixedContext,
    RecommendationOutput,
)


SYSTEM_PROMPT = """You are Aeris, an outdoor-resource protection adviser.

You receive two inputs:
1. Fixed environmental context (location, CASTNET site, pollution profile, risk mode) describing the ambient exposure risk.
2. Dynamic scene context: a list of objects a computer-vision model detected in the live camera frame, each with a class name, confidence, approximate distance in meters, whether it is reachable, and an optional bounding box.

Your job is to decide which detected objects the user should act on first and how, so that the most sustainability-sensitive resources are protected from the environmental stress indicated by the fixed context. Plant-sensitive and electronic items are usually the most vulnerable. Tarps and storage bins are enablers that make other protections possible.

You MUST respond with a single JSON object and nothing else (no prose, no markdown fences) matching this exact schema:

{
  "actions": [
    {
      "rank": <int, 1-based ordering, 1 is most urgent>,
      "action": <one of: "protect_first", "move_to_storage", "cover_if_time_allows", "low_priority">,
      "target": <string, must exactly match one of the detected object "name" values>,
      "score": <float between 0 and 10, higher = more urgent>,
      "reason_tags": [<short snake_case tags, e.g. "plant_sensitive", "high_ozone_context", "reachable", "nearby">],
      "reason": <one-sentence human-readable justification>
    }
  ],
  "explanation": <2-4 sentence paragraph the UI will show the user, plain language, references the CASTNET risk mode and the top one or two targets>,
  "missing_insights": [<zero or more short strings describing protective items that are absent and would help, e.g. "No tarp detected. Coverage options are limited.">]
}

Rules:
- Only include targets that actually appear in the provided detected objects list.
- Rank entries must be contiguous starting at 1.
- Omit low-value detections rather than padding with low-priority entries unless they materially help the user.
- Never invent bounding boxes, classes, or CASTNET values."""


def build_user_prompt(fixed_context: FixedContext, dynamic_context: DynamicContext) -> str:
    payload = {
        "fixed_context": fixed_context.model_dump(),
        "dynamic_context": dynamic_context.model_dump(),
    }
    return (
        "Analyze this scene and return the JSON response as specified.\n\n"
        f"{json.dumps(payload, indent=2)}"
    )


def parse_recommendation_json(raw_text: str, decision_source: DecisionSource) -> RecommendationOutput:
    """Parse an LLM JSON response into a RecommendationOutput.

    Raises ValueError if the text cannot be parsed or validated so the caller
    can cascade to the next provider / fallback policy.
    """
    text = _strip_code_fences(raw_text).strip()
    if not text:
        raise ValueError("empty LLM response")

    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise ValueError(f"LLM response was not valid JSON: {error}") from error

    data["decision_source"] = decision_source

    try:
        return RecommendationOutput.model_validate(data)
    except ValidationError as error:
        raise ValueError(f"LLM response failed schema validation: {error}") from error


_FENCE_RE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)


def _strip_code_fences(text: str) -> str:
    stripped = text.strip()
    match = _FENCE_RE.match(stripped)
    if match:
        return match.group(1)
    return stripped
