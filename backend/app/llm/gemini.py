import time

from app.llm.template import TemplateProvider
from app.schemas import ActionRecommendation, DynamicContext, FixedContext, RecommendationOutput


class GeminiProvider(TemplateProvider):
    """Gemini-first agent provider placeholder.

    Wire the Gemini SDK here. The current scaffold sleeps briefly and uses the
    fallback output shape so the async job lifecycle can be tested immediately.
    """

    def generate_recommendations(
        self,
        fixed_context: FixedContext,
        dynamic_context: DynamicContext,
    ) -> RecommendationOutput:
        time.sleep(1.2)
        output = super().generate_recommendations(fixed_context, dynamic_context)
        return output.model_copy(
            update={
                "decision_source": "agentic_gemini",
                "explanation": (
                    f"{output.explanation} This recommendation was produced through the Gemini agent path."
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
        return f"{base} This explanation was polished by the Gemini provider path."
