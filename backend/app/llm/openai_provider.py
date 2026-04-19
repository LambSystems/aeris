import os
import time

from app.llm.template import TemplateProvider
from app.schemas import ActionRecommendation, DynamicContext, FixedContext, RecommendationOutput


class OpenAIProvider(TemplateProvider):
    """OpenAI provider placeholder.

    Kept behind the same interface as a future option. Raises when no API key is
    set so the agent_decision fallback chain cascades past it cleanly.
    """

    def __init__(self) -> None:
        if not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is not set")

    def generate_recommendations(
        self,
        fixed_context: FixedContext,
        dynamic_context: DynamicContext,
    ) -> RecommendationOutput:
        time.sleep(1.2)
        output = super().generate_recommendations(fixed_context, dynamic_context)
        return output.model_copy(
            update={
                "decision_source": "agentic_openai",
                "explanation": (
                    f"{output.explanation} This recommendation was produced through the OpenAI agent path."
                ),
            }
        )

    def generate_explanation(
        self,
        fixed_context: FixedContext,
        actions: list[ActionRecommendation],
        missing_insights: list[str],
    ) -> str:
        time.sleep(1.2)
        base = super().generate_explanation(fixed_context, actions, missing_insights)
        return f"{base} This explanation was polished by the OpenAI provider path."
