import json
import os

import anthropic

from app.context.schemas import EnvironmentalFixedContext
from app.sustainability.fallback_advice import build_fallback_advice
from app.sustainability.schemas import CASTNETReading, SustainabilityAdvice, YOLODetection

_SYSTEM_PROMPT = """You are Aeris, an environmental sustainability adviser.

You receive a YOLO object detection and a CASTNET air quality reading.

Respond with a single JSON object and nothing else (no prose, no markdown fences):

{
  "context": <one sentence: name the object, what it's made of, and why it's an environmental concern given the current air quality>,
  "action": <one sentence: exactly what the person should do right now — be specific, e.g. name the bin type or facility that handles it>
}

Example for a soda can:
{
  "context": "A soda can was detected — aluminum takes over 80 years to decompose and the elevated ozone levels here accelerate surface oxidation.",
  "action": "Place it in the nearest blue recycling bin; aluminum cans are accepted at all municipal recycling facilities."
}"""


def _build_prompt(
    detection: YOLODetection,
    castnet: CASTNETReading,
    fixed_context: EnvironmentalFixedContext | None = None,
) -> str:
    payload = {
        "yolo_detection": detection.model_dump(),
        "castnet_reading": castnet.model_dump(),
    }
    if fixed_context is not None:
        payload["fixed_context"] = fixed_context.model_dump()
    return (
        "Analyze this detection, air quality data, and optional fixed context, then return the JSON response as specified.\n\n"
        f"{json.dumps(payload, indent=2)}"
    )


def _parse_response(raw: str, detection: YOLODetection) -> SustainabilityAdvice:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    data = json.loads(text)
    return SustainabilityAdvice(
        object_detected=detection.object_class,
        confidence=detection.confidence,
        context=data["context"],
        action=data["action"],
    )


def get_sustainability_advice(
    detection: YOLODetection,
    castnet: CASTNETReading,
    fixed_context: EnvironmentalFixedContext | None = None,
) -> SustainabilityAdvice:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return build_fallback_advice(detection, castnet, fixed_context)

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
            max_tokens=1024,
            temperature=0.4,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": _build_prompt(detection, castnet, fixed_context)}],
        )

        raw = "".join(
            block.text for block in message.content if getattr(block, "type", None) == "text"
        )
        advice = _parse_response(raw, detection)
        return advice.model_copy(
            update={
                "environment_summary": fixed_context.summary if fixed_context else None,
                "risk_flags": fixed_context.risk_flags if fixed_context else [],
                "castnet_site": castnet.location,
            }
        )
    except Exception:
        return build_fallback_advice(detection, castnet, fixed_context)
