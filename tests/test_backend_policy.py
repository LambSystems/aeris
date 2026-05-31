import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.data import load_demo_context, load_scene  # noqa: E402
from app.event_policy import evaluate_event_policy, next_event_state  # noqa: E402
from app.fallback_policy import build_fallback_recommendations  # noqa: E402
from app.schemas import DynamicContext  # noqa: E402


class BackendPolicyTests(unittest.TestCase):
    def test_initial_scene_triggers_analysis(self) -> None:
        fixed_context = load_demo_context()
        dynamic_context = load_scene("demo")

        decision = evaluate_event_policy(
            fixed_context=fixed_context,
            dynamic_context=dynamic_context,
            previous_state=None,
            environment_mode="outdoor",
            now_seconds=100.0,
        )

        self.assertTrue(decision.should_analyze)
        self.assertEqual(decision.reason, "initial_scene")
        self.assertIn("seed_tray", decision.advice_key)

    def test_same_scene_respects_cooldown(self) -> None:
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

        self.assertFalse(second_decision.should_analyze)
        self.assertEqual(second_decision.reason, "cooldown_active")
        self.assertEqual(second_decision.cooldown_remaining, 15.0)

    def test_object_set_change_triggers_analysis(self) -> None:
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

        self.assertTrue(second_decision.should_analyze)
        self.assertEqual(second_decision.reason, "object_set_changed")

    def test_indoor_empty_scene_does_not_trigger(self) -> None:
        fixed_context = load_demo_context()
        empty_scene = DynamicContext(source="unit_test", objects=[])

        decision = evaluate_event_policy(
            fixed_context=fixed_context,
            dynamic_context=empty_scene,
            previous_state=None,
            environment_mode="indoor",
            now_seconds=100.0,
        )

        self.assertFalse(decision.should_analyze)
        self.assertEqual(decision.reason, "no_actionable_context")

    def test_fallback_policy_ranks_sensitive_items(self) -> None:
        fixed_context = load_demo_context()
        dynamic_context = load_scene("demo")

        recommendations = build_fallback_recommendations(fixed_context, dynamic_context)
        top_action = recommendations.actions[0]

        self.assertEqual(top_action.target, "seed_tray")
        self.assertEqual(top_action.action, "protect_first")
        self.assertIn("plant_sensitive", top_action.reason_tags)
        self.assertIn("high_ozone_context", top_action.reason_tags)
        self.assertEqual(recommendations.actions[1].target, "battery_pack")
        self.assertEqual(recommendations.actions[1].action, "move_to_storage")


if __name__ == "__main__":
    unittest.main()
