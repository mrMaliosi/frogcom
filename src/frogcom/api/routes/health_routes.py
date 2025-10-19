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
            "/health",
            self.health_check,
            methods=["GET"],
            response_model=HealthResponse,
            summary="Проверка состояния сервиса",
            description="Возвращает статус сервиса и информацию о загруженной модели"
        )

    async def health_check(self) -> HealthResponse:
        """Проверка состояния сервиса."""
        try:
            return HealthResponse(
                status="healthy",
                timestamp=datetime.now(),
                version=config.api.version,
                model_loaded=self.llm_service.is_loaded(),
            )
        except Exception as e:
            self.logging_service.log_error(e)
            raise HTTPException(status_code=500, detail=f"Ошибка проверки: {str(e)}")
