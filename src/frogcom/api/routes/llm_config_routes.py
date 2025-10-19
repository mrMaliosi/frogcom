from datetime import datetime
from fastapi import Request, HTTPException
from frogcom.api.routes.base import BaseRoutes
from frogcom.api.dto.models import LLMConfigResponse, LLMConfigRequest

class LLMConfigRoutes(BaseRoutes):
    """Класс для конфигурации моделей"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_routes()

    def _setup_routes(self):
        self.router.add_api_route(
            "/config/llm",
            self.get_llm_config,
            methods=["GET"],
            response_model=LLMConfigResponse,
            summary="Получить конфигурацию LLM",
            description="Возвращает текущую конфигурацию LLM модели"
        )
        
        self.router.add_api_route(
            "/config/llm",
            self.update_llm_config,
            methods=["PUT"],
            response_model=LLMConfigResponse,
            summary="Обновить конфигурацию LLM",
            description="Обновляет конфигурацию LLM модели и параметры генерации"
        )

    async def get_llm_config(self) -> LLMConfigResponse:
        """Возвращает текущую конфигурацию LLM."""
        try:
            return self.llm_service.get_config()
        except Exception as e:
            self.logging_service.log_error(e)
            raise HTTPException(status_code=500, detail=f"Ошибка получения конфигурации: {str(e)}")
            
    async def update_llm_config(
        self,
        config_request: LLMConfigRequest
    ) -> LLMConfigResponse:
        """Обновляет конфигурацию LLM."""
        try:
            updated_config = self.llm_service.update_config(config_request)
            self.logging_service.log_response({"config_updated": updated_config.dict()})
            return updated_config
        except Exception as e:
            self.logging_service.log_error(e, {"config_request": config_request.model_dump()})
            raise HTTPException(status_code=500, detail=f"Ошибка обновления конфигурации: {str(e)}")