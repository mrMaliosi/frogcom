from datetime import datetime
from fastapi import Request, HTTPException
from frogcom.api.routes.base import BaseRoutes
from frogcom.api.dto.models import LLMConfigResponse, LLMConfigRequest
from frogcom.internal.services.llm_service import LLMService

class LLMConfigRoutes(BaseRoutes):
    """Класс для конфигурации моделей"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_routes()

    def _setup_routes(self) -> None:
        # Единый путь с выбором сервиса через {llm_id}
        self.router.add_api_route(
            "/config/llm/{llm_id}",
            self.get_llm_config,
            methods=["GET"],
            response_model=LLMConfigResponse,
            summary="Получить конфигурацию LLM",
            description="Возвращает текущую конфигурацию выбранной LLM по идентификатору llm_id",
        )
        self.router.add_api_route(
            "/config/llm/{llm_id}",
            self.update_llm_config,
            methods=["PUT"],
            response_model=LLMConfigResponse,
            summary="Обновить конфигурацию LLM",
            description="Обновляет конфигурацию выбранной LLM по идентификатору llm_id",
        )

    def _get_llm_by_id(self, llm_id: str, request: Request) -> LLMService:
        llms: Dict[str, LLMService] = request.app.state.llms
        svc = llms.get(llm_id)
        if svc is None:
            # Подсказка пользователю по доступным ключам
            available = list(llms.keys())
            raise HTTPException(
                status_code=404,
                detail=f"LLM '{llm_id}' not found. Available: {available}",
            )
        return svc
            
    async def get_llm_config(self, llm_id: str, request: Request) -> LLMConfigResponse:
        """Возвращает текущую конфигурацию выбранной LLM."""
        try:
            svc = self._get_llm_by_id(llm_id, request)
            config = svc.get_config()
            # структурированное логирование
            self.logging_service.log_response(
                {"event": "llm_config_read", "llm_id": llm_id, "config": getattr(config, "model_dump", lambda: config)()}
            )
            return config
        except HTTPException:
            # уже корректно сформировано
            raise
        except Exception as e:
            self.logging_service.log_error(e, {"op": "get_llm_config", "llm_id": llm_id})
            raise HTTPException(status_code=500, detail=f"Ошибка получения конфигурации: {str(e)}")

    async def update_llm_config(
        self,
        llm_id: str,
        request: Request,
        config_request: LLMConfigRequest,
    ) -> LLMConfigResponse:
        """Обновляет конфигурацию выбранной LLM."""
        try:
            svc = self._get_llm_by_id(llm_id, request)
            updated_config = svc.update_config(config_request)
            self.logging_service.log_response(
                {
                    "event": "llm_config_updated",
                    "llm_id": llm_id,
                    "payload": config_request.model_dump(),
                    "updated": getattr(updated_config, "model_dump", lambda: updated_config)(),
                }
            )
            return updated_config
        except HTTPException:
            raise
        except Exception as e:
            self.logging_service.log_error(
                e, {"op": "update_llm_config", "llm_id": llm_id, "payload": config_request.model_dump()}
            )
            raise HTTPException(status_code=500, detail=f"Ошибка обновления конфигурации: {str(e)}")