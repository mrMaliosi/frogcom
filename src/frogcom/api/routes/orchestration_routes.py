from datetime import datetime
from fastapi import Request, HTTPException
from frogcom.api.routes.base import BaseRoutes
from frogcom.api.dto.models import OrchestrationConfigResponse, OrchestrationConfigRequest, PutLogsRequest, PutLogsResponse
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

        self.router.add_api_route(
            "/logs/bench",
            self.create_logs_bench,
            methods=["PUT"],
            response_model=PutLogsResponse,
            summary="Создать новую папку для логов",
            description="Создаёт новую папку для логов"
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
            if body.enable_question_verification is not None:
                config.orchestration.enable_code_verification = body.enable_code_verification
            if body.enable_question_verification is not None:
                config.orchestration.enable_question_verification = body.enable_question_verification
            if body.enable_only_one_model is not None:
                config.orchestration.enable_only_one_model = body.enable_only_one_model

            updated = OrchestrationConfigResponse(
                enabled=config.orchestration.enabled,
                communication_rounds=config.orchestration.communication_rounds,
                secondary_goal_prompt=config.orchestration.secondary_goal_prompt,
                enable_question_verification=config.orchestration.enable_question_verification
            )
            self.logging_service.log_response({"orchestration_config_updated": updated.model_dump()})
            return updated
        except Exception as e:
            self.logging_service.log_error(e, {"body": body.model_dump()})
            raise HTTPException(status_code=500,detail=f"Ошибка обновления конфигурации оркестрации: {str(e)}")
        
    async def create_logs_bench(self, body: PutLogsRequest) -> PutLogsResponse:
        try:
            self.logging_service.create_new_bench(body.logs)
            self.logging_service.log_response({"logs_updated": body.logs})
            return PutLogsResponse(logs=body.logs)
        except Exception as e:
            self.logging_service.log_error(e, {"body": body.model_dump()})
            raise HTTPException(status_code=500,detail=f"Ошибка обновления конфигурации оркестрации: {str(e)}")