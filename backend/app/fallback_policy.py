from app.schemas import (
    ActionRecommendation,
    ActionType,
    DynamicContext,
    FixedContext,
    RecommendationOutput,
    SceneObject,
)
from app.explanations import build_template_explanation


MODE_WEIGHTS: dict[str, dict[str, float]] = {
    "protect_plants_and_sensitive_equipment": {
        "seed_tray": 9.5,
        "plant_pot": 9.0,
        "battery_pack": 8.2,
        "electronics_case": 8.0,
        "tarp": 7.4,
        "storage_bin": 7.0,
        "metal_tool": 5.0,
        "gloves": 3.2,
        "water_jug": 2.4,
        "misc_item": 0.4,
    },
    "general_outdoor_protection": {
        "seed_tray": 7.0,
        "plant_pot": 6.8,
        "battery_pack": 7.4,
        "electronics_case": 7.5,
        "tarp": 6.6,
        "storage_bin": 6.2,
        "metal_tool": 5.8,
        "gloves": 3.5,
        "water_jug": 3.0,
        "misc_item": 0.4,
    },
}

PROTECTION_VALUE = {
    "seed_tray": 2.0,
    "plant_pot": 1.8,
    "battery_pack": 1.7,
    "electronics_case": 1.7,
    "metal_tool": 1.1,
    "water_jug": 0.5,
    "gloves": 0.6,
    "misc_item": 0.0,
}

ENABLING_VALUE = {
    "tarp": 2.2,
    "storage_bin": 2.0,
}


def build_fallback_recommendations(
    fixed_context: FixedContext,
    dynamic_context: DynamicContext,
) -> RecommendationOutput:
    actions = [
        _score_object(index, scene_object, fixed_context)
        for index, scene_object in enumerate(dynamic_context.objects)
    ]
    actions.sort(key=lambda action: action.score or 0, reverse=True)

    ranked_actions = [
        action.model_copy(update={"rank": rank})
        for rank, action in enumerate(actions, start=1)
        if (action.score or 0) > 0.5
    ]

    missing_insights = _build_missing_insights(dynamic_context)
    explanation = build_template_explanation(fixed_context, ranked_actions, missing_insights)

    return RecommendationOutput(
        decision_source="fallback_policy",
        actions=ranked_actions,
        explanation=explanation,
        missing_insights=missing_insights,
    )


def _score_object(index: int, scene_object: SceneObject, fixed_context: FixedContext) -> ActionRecommendation:
    object_name = scene_object.name
    mode_weights = MODE_WEIGHTS.get(fixed_context.risk_mode, MODE_WEIGHTS["general_outdoor_protection"])

    vulnerability = mode_weights.get(object_name, 0.5)
    protection_value = PROTECTION_VALUE.get(object_name, 0.0)
    enabling_value = ENABLING_VALUE.get(object_name, 0.0)
    distance_penalty = min(scene_object.distance * 0.55, 2.5)
    unreachable_penalty = 2.5 if not scene_object.reachable else 0.0
    confidence_adjustment = (scene_object.confidence - 0.5) * 0.8

    score = vulnerability + protection_value + enabling_value - distance_penalty - unreachable_penalty + confidence_adjustment
    score = round(max(score, 0.0), 2)

    action = _choose_action(object_name, score)
    reason_tags = _reason_tags(object_name, scene_object, action, fixed_context)
    reason = _human_reason(object_name, action, reason_tags)

    return ActionRecommendation(
        rank=index + 1,
        action=action,
        target=object_name,
        score=score,
        reason_tags=reason_tags,
        reason=reason,
    )


def _choose_action(object_name: str, score: float) -> ActionType:
    if score < 3.0:
        return "low_priority"
    if object_name in {"battery_pack", "electronics_case"}:
        return "move_to_storage"
    if object_name in {"tarp", "storage_bin", "metal_tool"}:
        return "cover_if_time_allows"
    return "protect_first"


def _reason_tags(
    object_name: str,
    scene_object: SceneObject,
    action: ActionType,
    fixed_context: FixedContext,
) -> list[str]:
    tags: list[str] = []

    if object_name in {"seed_tray", "plant_pot"}:
        tags.append("plant_sensitive")
    if object_name in {"battery_pack", "electronics_case"}:
        tags.append("sensitive_equipment")
    if object_name in {"tarp", "storage_bin"}:
        tags.append("protection_enabler")
    if fixed_context.pollution_profile.ozone_risk == "high":
        tags.append("high_ozone_context")
    if scene_object.reachable:
        tags.append("reachable")
    else:
        tags.append("hard_to_reach")
    if scene_object.distance <= 1.5:
        tags.append("nearby")
    if action == "low_priority":
        tags.append("lower_environmental_sensitivity")

    return tags


def _human_reason(object_name: str, action: ActionType, reason_tags: list[str]) -> str:
    if "plant_sensitive" in reason_tags:
        return "Plant-sensitive resource under elevated ozone context."
    if "sensitive_equipment" in reason_tags:
        return "Sensitive equipment is exposed and should be moved out of environmental stress."
    if "protection_enabler" in reason_tags:
        return "Protection-enabling item can reduce exposure for nearby resources."
    if action == "low_priority":
        return "Lower urgency compared with sensitive or protection-enabling items."
    return "Relevant exposed outdoor resource."


def _build_missing_insights(dynamic_context: DynamicContext) -> list[str]:
    object_names = {scene_object.name for scene_object in dynamic_context.objects}
    insights: list[str] = []

    if "tarp" not in object_names:
        insights.append("No tarp detected. Coverage options are limited.")
    if "storage_bin" not in object_names:
        insights.append("No storage bin detected. Move-sensitive recommendations may be harder to act on.")

    return insights

