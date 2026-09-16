"""Agentic closed feedback loop package."""

from photometric_relighting.agent.critic import (
    BasePhotometricCritic,
    RuleBasedPhotometricCritic,
    VLMPromptBuilder,
)
from photometric_relighting.agent.loop import PhotometricFeedbackLoop
from photometric_relighting.agent.models import (
    FeedbackLoopResult,
    FeedbackStep,
    PhotometricTarget,
)

__all__ = [
    "BasePhotometricCritic",
    "RuleBasedPhotometricCritic",
    "VLMPromptBuilder",
    "PhotometricFeedbackLoop",
    "FeedbackLoopResult",
    "FeedbackStep",
    "PhotometricTarget",
]
