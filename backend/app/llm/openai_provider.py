from app.llm.template import TemplateProvider
from app.schemas import ActionRecommendation, FixedContext


class OpenAIProvider(TemplateProvider):
    """OpenAI provider placeholder.

    Keep OpenAI as the secondary option behind the same interface. The demo can
    ship without enabling this class because TemplateProvider remains safe.
    """

    def generate_explanation(
        self,
        fixed_context: FixedContext,
        actions: list[ActionRecommendation],
        missing_insights: list[str],
    ) -> str:
        return super().generate_explanation(fixed_context, actions, missing_insights)

