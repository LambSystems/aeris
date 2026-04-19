from abc import ABC, abstractmethod

from app.schemas import ActionRecommendation, DynamicContext, FixedContext, RecommendationOutput


class LLMProvider(ABC):
    @abstractmethod
    def generate_recommendations(
        self,
        fixed_context: FixedContext,
        dynamic_context: DynamicContext,
    ) -> RecommendationOutput:
        raise NotImplementedError

    @abstractmethod
    def generate_explanation(
        self,
        fixed_context: FixedContext,
        actions: list[ActionRecommendation],
        missing_insights: list[str],
    ) -> str:
        raise NotImplementedError
