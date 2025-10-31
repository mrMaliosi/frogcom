# frogcom/internal/contexts/llm_orchestrator.py
from __future__ import annotations
from typing import Dict
from frogcom.config.config import config
from frogcom.internal.services.llm_service import LLMService
from frogcom.internal.services.logging_service import LoggingService
from frogcom.internal.services.tracing_service import TracingService
from frogcom.internal.services.orchestrator_service import OrchestratorService

class LLMOrchestrator:
    def __init__(self) -> None:
        # формируем словарь сервисов по удобным ключам
        self.llms: Dict[str, LLMService] = {
            "primary": LLMService(config.llm),
            "secondary": LLMService(config.secondary_llm),
        }
        self.logging_service = LoggingService(config.logging)
        self.tracing_service = TracingService(config.logging)
        self.orchestrator = OrchestratorService(
            primary=self.llms["primary"],
            secondary=self.llms["secondary"],
            orchestration_config=config.orchestration,
            tracing_service=self.tracing_service,
        )
