import os

import anthropic

from app.llm.prompt import SYSTEM_PROMPT, build_user_prompt, parse_recommendation_json
from app.llm.template import TemplateProvider
from app.schemas import DynamicContext, FixedContext, RecommendationOutput


DEFAULT_MODEL = "claude-sonnet-4-6"


class AnthropicProvider(TemplateProvider):
    """Anthropic-backed adviser. Calls the Claude Messages API for structured JSON."""

    def __init__(self, model: str | None = None) -> None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model or os.environ.get("ANTHROPIC_MODEL") or DEFAULT_MODEL

    def generate_recommendations(
        self,
        fixed_context: FixedContext,
        dynamic_context: DynamicContext,
    ) -> RecommendationOutput:
        message = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            temperature=0.3,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": build_user_prompt(fixed_context, dynamic_context),
                }
            ],
        )
        text = "".join(
            block.text for block in message.content if getattr(block, "type", None) == "text"
        )
        return parse_recommendation_json(text, decision_source="agentic_anthropic")
