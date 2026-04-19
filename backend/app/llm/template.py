from app.explanations import build_template_explanation
from app.fallback_policy import build_fallback_recommendations
from app.llm.provider import LLMProvider
from app.schemas import ActionRecommendation, DynamicContext, FixedContext, RecommendationOutput


class TemplateProvider(LLMProvider):
    def generate_recommendations(
        self,
        fixed_context: FixedContext,
        dynamic_context: DynamicContext,
    ) -> RecommendationOutput:
        return build_fallback_recommendations(fixed_context, dynamic_context)

    def generate_explanation(
        self,
        fixed_context: FixedContext,
        actions: list[ActionRecommendation],
        missing_insights: list[str],
    ) -> str:
        return build_template_explanation(fixed_context, actions, missing_insights)
