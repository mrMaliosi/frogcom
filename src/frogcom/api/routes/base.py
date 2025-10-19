from fastapi import APIRouter
from frogcom.internal.services.llm_service import LLMService
from frogcom.internal.services.logging_service import LoggingService
from frogcom.internal.services.orchestrator_service import OrchestratorService
from frogcom.internal.services.prompt_service import PromptService

class BaseRoutes:
    """Базовый класс для всех маршрутов API."""

    def __init__(
        self,
        llm_service: LLMService,
        logging_service: LoggingService,
        orchestrator: OrchestratorService,
    ):
        self.llm_service = llm_service
        self.logging_service = logging_service
        self.orchestrator = orchestrator
        self.prompt_service = PromptService()
        self.router = APIRouter()

    def get_router(self) -> APIRouter:
        """Возвращает готовый роутер для регистрации в FastAPI."""
        return self.router
