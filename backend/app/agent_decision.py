from app.fallback_policy import build_fallback_recommendations
from app.llm.gemini import GeminiProvider
from app.llm.openai_provider import OpenAIProvider
from app.llm.template import TemplateProvider
from app.schemas import DecisionProvider, DynamicContext, FixedContext, RecommendationOutput


def generate_agentic_recommendations(
    fixed_context: FixedContext,
    dynamic_context: DynamicContext,
    provider: DecisionProvider = "gemini",
) -> RecommendationOutput:
    """Generate the async decision output.

    Gemini is the intended primary provider, OpenAI is the fallback provider,
    and local fallback policy is the final safety net.
    """
    try:
        selected = _select_provider(provider)
        return selected.generate_recommendations(fixed_context, dynamic_context)
    except Exception:
        if provider == "gemini":
            try:
                return OpenAIProvider().generate_recommendations(fixed_context, dynamic_context)
            except Exception:
                pass

        return build_fallback_recommendations(fixed_context, dynamic_context)


def _select_provider(provider: DecisionProvider) -> TemplateProvider:
    if provider == "openai":
        return OpenAIProvider()
    if provider == "template":
        return TemplateProvider()
    return GeminiProvider()

