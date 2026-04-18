from app.llm.template import TemplateProvider
from app.schemas import ActionRecommendation, FixedContext


class GeminiProvider(TemplateProvider):
    """Gemini-first provider placeholder.

    Keep this class so routes and policy logic do not depend directly on a vendor
    SDK. Wire the Gemini SDK here only after the template path is stable.
    """

    def generate_explanation(
        self,
        fixed_context: FixedContext,
        actions: list[ActionRecommendation],
        missing_insights: list[str],
    ) -> str:
        return super().generate_explanation(fixed_context, actions, missing_insights)

