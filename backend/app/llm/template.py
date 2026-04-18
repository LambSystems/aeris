from app.explanations import build_template_explanation
from app.llm.provider import LLMProvider
from app.schemas import ActionRecommendation, FixedContext


class TemplateProvider(LLMProvider):
    def generate_explanation(
        self,
        fixed_context: FixedContext,
        actions: list[ActionRecommendation],
        missing_insights: list[str],
    ) -> str:
        return build_template_explanation(fixed_context, actions, missing_insights)

