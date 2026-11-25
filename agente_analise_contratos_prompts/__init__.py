"""
Prompts especializados para o agente e suas skills.
"""

from .system_prompt import SYSTEM_PROMPT
from .classifier_prompt import CLASSIFIER_PROMPT
from .mapper_prompt import MAPPER_PROMPT
from .qa_prompt import QA_PROMPT

__all__ = [
    "SYSTEM_PROMPT",
    "CLASSIFIER_PROMPT",
    "MAPPER_PROMPT",
    "QA_PROMPT",
]
