from app.schemas import ActionRecommendation, FixedContext


MODE_LABELS = {
    "protect_plants_and_sensitive_equipment": "protect plants and sensitive equipment",
    "general_outdoor_protection": "general outdoor protection",
}

ACTION_LABELS = {
    "protect_first": "protect",
    "move_to_storage": "move to storage",
    "cover_if_time_allows": "cover if time allows",
    "low_priority": "deprioritize",
}


def build_template_explanation(
    fixed_context: FixedContext,
    actions: list[ActionRecommendation],
    missing_insights: list[str],
) -> str:
    mode_label = MODE_LABELS.get(fixed_context.risk_mode, fixed_context.risk_mode.replace("_", " "))

    if not actions:
        return (
            f"CASTNET-derived context indicates {mode_label}, but no actionable scene objects were detected. "
            "Use the backup demo frame or rescan the scene."
        )

    top = actions[0]
    explanation = (
        f"CASTNET-derived context indicates {mode_label}. "
        f"Aeris ranks {format_target(top.target)} first because {top.reason.lower()}"
    )

    if len(actions) > 1:
        second = actions[1]
        explanation += (
            f" Next, {format_target(second.target)} should be "
            f"{ACTION_LABELS[second.action]} because {second.reason.lower()}"
        )

    if len(actions) > 2:
        third = actions[2]
        explanation += (
            f" {format_target(third.target).capitalize()} is also relevant as a "
            f"{ACTION_LABELS[third.action]} action."
        )

    if missing_insights:
        explanation += f" Note: {missing_insights[0]}"

    return explanation


def format_target(target: str) -> str:
    return target.replace("_", " ")

