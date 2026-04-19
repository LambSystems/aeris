from dataclasses import dataclass
from typing import Literal

from app.schemas import DynamicContext, FixedContext


EnvironmentMode = Literal["indoor", "outdoor"]

DEFAULT_COOLDOWN_SECONDS = 20.0


@dataclass(frozen=True)
class EventState:
    """Small snapshot of the previous scene used to prevent repeated LLM calls."""

    object_names: tuple[str, ...] = ()
    environment_mode: EnvironmentMode = "outdoor"
    risk_key: str = "ozone:low|deposition:low"
    advice_key: str | None = None
    last_triggered_at: float = 0.0


@dataclass(frozen=True)
class EventDecision:
    should_analyze: bool
    reason: str
    advice_key: str
    cooldown_remaining: float = 0.0


def evaluate_event_policy(
    fixed_context: FixedContext,
    dynamic_context: DynamicContext,
    previous_state: EventState | None = None,
    environment_mode: EnvironmentMode = "outdoor",
    now_seconds: float = 0.0,
    cooldown_seconds: float = DEFAULT_COOLDOWN_SECONDS,
) -> EventDecision:
    """Decide whether this scene snapshot is worth an async agent call.

    The policy keeps the live vision path cheap: detections can update every
    sampled frame, while the LLM is only called on meaningful scene/context
    changes or after a cooldown.
    """
    object_names = normalized_object_names(dynamic_context)
    risk_key = build_risk_key(fixed_context)
    advice_key = build_advice_key(fixed_context, dynamic_context, environment_mode)

    if not object_names and not _has_environment_risk(fixed_context, environment_mode):
        return EventDecision(False, "no_actionable_context", advice_key)

    if previous_state is None:
        return EventDecision(True, "initial_scene", advice_key)

    strong_change = _strong_change_reason(
        object_names=object_names,
        environment_mode=environment_mode,
        risk_key=risk_key,
        previous_state=previous_state,
    )
    if strong_change is not None:
        return EventDecision(True, strong_change, advice_key)

    elapsed = max(now_seconds - previous_state.last_triggered_at, 0.0)
    if previous_state.advice_key == advice_key and elapsed < cooldown_seconds:
        return EventDecision(
            False,
            "cooldown_active",
            advice_key,
            cooldown_remaining=round(cooldown_seconds - elapsed, 2),
        )

    if _has_environment_risk(fixed_context, environment_mode):
        return EventDecision(True, "environment_risk_refresh", advice_key)

    if object_names:
        return EventDecision(True, "cooldown_expired", advice_key)

    return EventDecision(False, "no_meaningful_change", advice_key)


def next_event_state(
    fixed_context: FixedContext,
    dynamic_context: DynamicContext,
    decision: EventDecision,
    previous_state: EventState | None = None,
    environment_mode: EnvironmentMode = "outdoor",
    now_seconds: float = 0.0,
) -> EventState:
    """Build the state to store after evaluating a snapshot."""
    previous_triggered_at = previous_state.last_triggered_at if previous_state else 0.0
    triggered_at = now_seconds if decision.should_analyze else previous_triggered_at
    previous_advice_key = previous_state.advice_key if previous_state else None
    return EventState(
        object_names=normalized_object_names(dynamic_context),
        environment_mode=environment_mode,
        risk_key=build_risk_key(fixed_context),
        advice_key=decision.advice_key if decision.should_analyze else previous_advice_key,
        last_triggered_at=triggered_at,
    )


def normalized_object_names(dynamic_context: DynamicContext) -> tuple[str, ...]:
    return tuple(sorted({scene_object.name for scene_object in dynamic_context.objects}))


def build_risk_key(fixed_context: FixedContext) -> str:
    profile = fixed_context.pollution_profile
    return f"ozone:{profile.ozone_risk}|deposition:{profile.deposition_risk}"


def build_advice_key(
    fixed_context: FixedContext,
    dynamic_context: DynamicContext,
    environment_mode: EnvironmentMode,
) -> str:
    objects = ",".join(normalized_object_names(dynamic_context)) or "no_objects"
    return f"{environment_mode}|{build_risk_key(fixed_context)}|{objects}"


def _strong_change_reason(
    object_names: tuple[str, ...],
    environment_mode: EnvironmentMode,
    risk_key: str,
    previous_state: EventState,
) -> str | None:
    if previous_state.environment_mode != environment_mode:
        return "environment_mode_changed"
    if previous_state.risk_key != risk_key:
        return "environment_risk_changed"
    if previous_state.object_names != object_names:
        return "object_set_changed"
    return None


def _has_environment_risk(fixed_context: FixedContext, environment_mode: EnvironmentMode) -> bool:
    if environment_mode != "outdoor":
        return False

    profile = fixed_context.pollution_profile
    return profile.ozone_risk == "high" or profile.deposition_risk == "high"
