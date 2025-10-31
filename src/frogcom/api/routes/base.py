# frogcom/api/routes/base_routes.py
from fastapi import APIRouter, HTTPException, Request
from frogcom.internal.services.llm_service import LLMService
from frogcom.internal.services.logging_service import LoggingService
from frogcom.internal.services.orchestrator_service import OrchestratorService
from frogcom.internal.services.prompt_service import PromptService

class BaseRoutes:
    """Базовый класс для всех маршрутов API."""

    def __init__(
        self,
        llm_service_primary: LLMService,
        llm_service_secondary: LLMService,
        logging_service: LoggingService,
        orchestrator: OrchestratorService,
    ):
        self.llm_service_primary = llm_service_primary
        self.llm_service_secondary = llm_service_secondary
        self.logging_service = logging_service
        self.orchestrator = orchestrator
        self.prompt_service = PromptService()
        self.router = APIRouter()

    def get_router(self) -> APIRouter:
        """Возвращает настроенный роутер для регистрации в FastAPI."""
        return self.router