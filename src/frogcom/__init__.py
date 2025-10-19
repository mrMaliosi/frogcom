"""
FrogCom - API для генерации комментариев и докумментации с использованием LLM моделей.

Этот пакет предоставляет REST API для взаимодействия с различными
LLM моделями через vLLM.
"""

from frogcom.internal.services.llm_service import LLMService
from frogcom.internal.services.logging_service import LoggingService
from frogcom.internal.services.prompt_service import PromptService
from frogcom.config.config import config, AppConfig

__version__ = "0.2.0"
__all__ = [
    "LLMService",
    "LoggingService", 
    "PromptService",
    "config",
    "AppConfig",
]