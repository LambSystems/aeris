from app.fallback_policy import build_fallback_recommendations
from app.llm.anthropic_provider import AnthropicProvider
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

    Tries the requested provider first. If it fails (missing key, network,
    parse error), falls back through the remaining remote providers and
    finally to the local fallback policy so the demo always returns a result.
    """
    for candidate in _fallback_chain(provider):
        try:
            return _instantiate(candidate).generate_recommendations(fixed_context, dynamic_context)
        except Exception:
            continue

    return build_fallback_recommendations(fixed_context, dynamic_context)


def _fallback_chain(provider: DecisionProvider) -> list[DecisionProvider]:
    if provider == "template":
        return ["template"]
    remote_order: list[DecisionProvider] = ["gemini", "anthropic", "openai"]
    chain = [provider] + [p for p in remote_order if p != provider]
    chain.append("template")
    return chain


def _instantiate(provider: DecisionProvider) -> TemplateProvider:
    if provider == "openai":
        return OpenAIProvider()
    if provider == "anthropic":
        return AnthropicProvider()
    if provider == "template":
        return TemplateProvider()
    return GeminiProvider()
