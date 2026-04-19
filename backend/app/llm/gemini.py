import os

from google import genai
from google.genai import types

from app.llm.prompt import SYSTEM_PROMPT, build_user_prompt, parse_recommendation_json
from app.llm.template import TemplateProvider
from app.schemas import DynamicContext, FixedContext, RecommendationOutput


DEFAULT_MODEL = "gemini-2.5-flash"


class GeminiProvider(TemplateProvider):
    """Gemini-backed adviser. Calls the real SDK and parses structured JSON."""

    def __init__(self, model: str | None = None) -> None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        self._client = genai.Client(api_key=api_key)
        self._model = model or os.environ.get("GEMINI_MODEL") or DEFAULT_MODEL

    def generate_recommendations(
        self,
        fixed_context: FixedContext,
        dynamic_context: DynamicContext,
    ) -> RecommendationOutput:
        response = self._client.models.generate_content(
            model=self._model,
            contents=build_user_prompt(fixed_context, dynamic_context),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                temperature=0.3,
            ),
        )
        return parse_recommendation_json(response.text or "", decision_source="agentic_gemini")
