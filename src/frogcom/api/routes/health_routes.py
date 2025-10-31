from datetime import datetime
from fastapi import HTTPException
from frogcom.api.routes.base import BaseRoutes
from frogcom.api.dto.models import HealthResponse
from frogcom.config.config import config

class HealthRoutes(BaseRoutes):
    """Маршруты проверки состояния сервиса."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_routes()

    def _setup_routes(self):
        self.router.add_api_route(
            "/health/main-model",
            self.health_check_primary,
            methods=["GET"],
            response_model=HealthResponse,
            summary="Проверка состояния основной модели",
            description="Возвращает статус основной модели"
        )

        self.router.add_api_route(
            "/health/secondary-model",
            self.health_check_secondary,
            methods=["GET"],
            response_model=HealthResponse,
            summary="Проверка состояния вспомогательной модели",
            description="Возвращает статус вспомогательной модели"
        )

    async def health_check_primary(self) -> HealthResponse:
        """Проверка состояния сервиса."""
        try:
            return HealthResponse(
                status="healthy",
                timestamp=datetime.now(),
                version=config.api.version,
                model_loaded=self.llm_service_primary.is_loaded(),
            )
        except Exception as e:
            self.logging_service.log_error(e)
            raise HTTPException(status_code=500, detail=f"Ошибка проверки: {str(e)}")

    async def health_check_secondary(self) -> HealthResponse:
        """Проверка состояния сервиса."""
        try:
            return HealthResponse(
                status="healthy",
                timestamp=datetime.now(),
                version=config.api.version,
                model_loaded=self.llm_service_secondary.is_loaded(),
            )
        except Exception as e:
            self.logging_service.log_error(e)
            raise HTTPException(status_code=500, detail=f"Ошибка проверки: {str(e)}")
