import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.data import load_demo_context, load_scene  # noqa: E402
from app.event_policy import evaluate_event_policy, next_event_state  # noqa: E402
from app.fallback_policy import build_fallback_recommendations  # noqa: E402
from app.schemas import DynamicContext  # noqa: E402


def test_initial_scene_triggers_analysis() -> None:
    fixed_context = load_demo_context()
    dynamic_context = load_scene("demo")

    decision = evaluate_event_policy(
        fixed_context=fixed_context,
        dynamic_context=dynamic_context,
        previous_state=None,
        environment_mode="outdoor",
        now_seconds=100.0,
    )

    assert decision.should_analyze is True
    assert decision.reason == "initial_scene"
    assert "seed_tray" in decision.advice_key


def test_same_scene_respects_cooldown() -> None:
    fixed_context = load_demo_context()
    dynamic_context = load_scene("demo")
    first_decision = evaluate_event_policy(
        fixed_context=fixed_context,
        dynamic_context=dynamic_context,
        previous_state=None,
        environment_mode="outdoor",
        now_seconds=100.0,
    )
    state = next_event_state(
        fixed_context=fixed_context,
        dynamic_context=dynamic_context,
        decision=first_decision,
        environment_mode="outdoor",
        now_seconds=100.0,
    )

    second_decision = evaluate_event_policy(
        fixed_context=fixed_context,
        dynamic_context=dynamic_context,
        previous_state=state,
        environment_mode="outdoor",
        now_seconds=105.0,
    )

    assert second_decision.should_analyze is False
    assert second_decision.reason == "cooldown_active"
    assert second_decision.cooldown_remaining == 15.0


def test_object_set_change_triggers_analysis() -> None:
    fixed_context = load_demo_context()
    first_scene = load_scene("demo")
    second_scene = load_scene("after_move")
    first_decision = evaluate_event_policy(
        fixed_context=fixed_context,
        dynamic_context=first_scene,
        previous_state=None,
        environment_mode="outdoor",
        now_seconds=100.0,
    )
    state = next_event_state(
        fixed_context=fixed_context,
        dynamic_context=first_scene,
        decision=first_decision,
        environment_mode="outdoor",
        now_seconds=100.0,
    )

    second_decision = evaluate_event_policy(
        fixed_context=fixed_context,
        dynamic_context=second_scene,
        previous_state=state,
        environment_mode="outdoor",
        now_seconds=105.0,
    )

    assert second_decision.should_analyze is True
    assert second_decision.reason == "object_set_changed"


def test_indoor_empty_scene_does_not_trigger() -> None:
    fixed_context = load_demo_context()
    empty_scene = DynamicContext(source="unit_test", objects=[])

    decision = evaluate_event_policy(
        fixed_context=fixed_context,
        dynamic_context=empty_scene,
        previous_state=None,
        environment_mode="indoor",
        now_seconds=100.0,
    )

    assert decision.should_analyze is False
    assert decision.reason == "no_actionable_context"


def test_fallback_policy_ranks_sensitive_items() -> None:
    fixed_context = load_demo_context()
    dynamic_context = load_scene("demo")

    recommendations = build_fallback_recommendations(fixed_context, dynamic_context)
    top_action = recommendations.actions[0]

    assert top_action.target == "seed_tray"
    assert top_action.action == "protect_first"
    assert "plant_sensitive" in top_action.reason_tags
    assert "high_ozone_context" in top_action.reason_tags
    assert recommendations.actions[1].target == "battery_pack"
    assert recommendations.actions[1].action == "move_to_storage"


def run_tests() -> None:
    tests = [
        test_initial_scene_triggers_analysis,
        test_same_scene_respects_cooldown,
        test_object_set_change_triggers_analysis,
        test_indoor_empty_scene_does_not_trigger,
        test_fallback_policy_ranks_sensitive_items,
    ]

    for test in tests:
        test()
        print(f"pass: {test.__name__}")


if __name__ == "__main__":
    run_tests()
