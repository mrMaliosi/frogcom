from datetime import datetime
from fastapi import Request, HTTPException
from frogcom.api.routes.base import BaseRoutes
from frogcom.api.dto.models import OrchestrationConfigResponse, OrchestrationConfigRequest
from frogcom.config.config import config

class OrchestrationRoutes(BaseRoutes):
    """Класс для оркестрации моделей"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_routes()

    def _setup_routes(self):
        # Конфигурация оркестрации
        self.router.add_api_route(
            "/config/orchestration",
            self.get_orchestration_config,
            methods=["GET"],
            response_model=OrchestrationConfigResponse,
            summary="Получить конфигурацию оркестрации",
            description="Возвращает текущие настройки взаимодействия моделей"
        )

        self.router.add_api_route(
            "/config/orchestration",
            self.update_orchestration_config,
            methods=["PUT"],
            response_model=OrchestrationConfigResponse,
            summary="Обновить конфигурацию оркестрации",
            description="Обновляет настройки взаимодействия основной и второй модели"
        )
        
    async def get_orchestration_config(self) -> OrchestrationConfigResponse:
        """Возвращает текущую конфигурацию оркестрации."""
        try:
            return OrchestrationConfigResponse(
                enabled=config.orchestration.enabled,
                communication_rounds=config.orchestration.communication_rounds,
                secondary_goal_prompt=config.orchestration.secondary_goal_prompt,
            )
        except Exception as e:
            self.logging_service.log_error(e)
            raise HTTPException(status_code=500, detail=f"Ошибка получения конфигурации оркестрации: {str(e)}")

    async def update_orchestration_config(self, body: OrchestrationConfigRequest) -> OrchestrationConfigResponse:
        """Обновляет конфигурацию оркестрации."""
        try:
            if body.enabled is not None:
                config.orchestration.enabled = body.enabled
            if body.communication_rounds is not None:
                config.orchestration.communication_rounds = body.communication_rounds
            if body.secondary_goal_prompt is not None:
                config.orchestration.secondary_goal_prompt = body.secondary_goal_prompt

            updated = OrchestrationConfigResponse(
                enabled=config.orchestration.enabled,
                communication_rounds=config.orchestration.communication_rounds,
                secondary_goal_prompt=config.orchestration.secondary_goal_prompt,
            )
            self.logging_service.log_response({"orchestration_config_updated": updated.model_dump()})
            return updated
        except Exception as e:
            self.logging_service.log_error(e, {"body": body.model_dump()})
            raise HTTPException(status_code=500,detail=f"Ошибка обновления конфигурации оркестрации: {str(e)}")