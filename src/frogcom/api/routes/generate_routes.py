from datetime import datetime
from fastapi import Request, HTTPException
from frogcom.api.routes.base import BaseRoutes
from frogcom.api.dto.models import FunctionDescription, GenerateResponse, Choice, Message, CommentRequest, CommentResponse

class GenerateRoutes(BaseRoutes):
    """Маршруты генерации текста."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_routes()

    def _setup_routes(self):
        self.router.add_api_route(
            "/generate",
            self.generate_comment,
            methods=["POST"],
            response_model=CommentResponse,
            summary="Генерация текста",
            description="Генерирует текст на основе промпта или сообщений"
        )

        self.router.add_api_route(
            "/update_method",
            self.update_method,
            methods=["POST"],
            response_model=CommentResponse,
            summary="Генерация текста",
            description="Генерирует текст на основе промпта или сообщений"
        )

    async def generate_comment(self, request: Request, req: CommentRequest) -> CommentResponse:
        """
        Генерирует комментарий на основе предобработанного запроса.
        """
        try:
            data = req.model_dump()
            prompt_task : str = self.prompt_service.extract_prompt_task(data)
            code : str = self.prompt_service.extract_code(data)
            function_desc : FunctionDescription = self.prompt_service.extract_function_description(data)

            # Create prompt
            task = self.prompt_service.task_creation(prompt_task, code, function_desc)

            answer = self.orchestrator.generate_with_orchestration(
                user_prompt=task,
                max_tokens=self.llm_service_primary.get_config().max_tokens,
                temperature=self.llm_service_primary.get_config().temperature,
                top_p=self.llm_service_primary.get_config().top_p,
                stop=[],
                seed=self.llm_service_primary.get_config().seed,
            )

            response = CommentResponse(
                comment=answer
            )

            self.logging_service.log_response({"response": response.model_dump()})
            return response
        except Exception as e:
            self.logging_service.log_error(e, {"request": data})
            raise HTTPException(status_code=500, detail=f"Ошибка генерации: {str(e)}")

    #async def update_method(self, request: Request, req: CommentRequest) -> CommentResponse: