from abc import ABC, abstractmethod

from app.schemas import ActionRecommendation, FixedContext


class LLMProvider(ABC):
    @abstractmethod
    def generate_explanation(
        self,
        fixed_context: FixedContext,
        actions: list[ActionRecommendation],
        missing_insights: list[str],
    ) -> str:
        raise NotImplementedError

