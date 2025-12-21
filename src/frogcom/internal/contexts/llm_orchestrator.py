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
        primary_config = config.llm
        print(primary_config)
        print(primary_config.to_dict())
        print(config.secondary_llm.to_dict())
        primary_service = LLMService(primary_config)
        print("[LOG]: First model ready!")
        

        secondary_config = config.secondary_llm
        if secondary_config.to_dict() == primary_config.to_dict():
            secondary_service = primary_service
        else:
            secondary_service = LLMService(secondary_config)
            print("[LOG]: Second model ready!")


        # формируем словарь сервисов по удобным ключам
        self.llms: Dict[str, LLMService] = {
            "primary": primary_service,
            "secondary": secondary_service,
        }
        self.logging_service = LoggingService(config.logging)
        self.tracing_service = TracingService(config.logging)
        self.orchestrator = OrchestratorService(
            primary=self.llms["primary"],
            secondary=self.llms["secondary"],
            orchestration_config=config.orchestration,
            tracing_service=self.tracing_service,
        )