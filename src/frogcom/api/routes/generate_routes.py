from datetime import datetime
from fastapi import Request, HTTPException
from frogcom.api.routes.base import BaseRoutes
from frogcom.api.dto.models import GenerateRequest, GenerateResponse, Choice, Message

class GenerateRoutes(BaseRoutes):
    """Маршруты генерации текста."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_routes()

    def _setup_routes(self):
        self.router.add_api_route(
            "/generate",
            self.generate_text,
            methods=["POST"],
            response_model=GenerateResponse,
            summary="Генерация текста",
            description="Генерирует текст на основе промпта или сообщений"
        )

    async def generate_text(self, request: Request, req: GenerateRequest) -> GenerateResponse:
        """
        Генерирует текст на основе промпта или сообщений.
        
        Поддерживает различные форматы запросов:
        - Прямой промпт через поле 'prompt'
        - Сообщения в формате чата через поле 'messages'
        """
        try:
            data = req.model_dump()             # TODO: exclude_unset=True - добавить в release
            prompt = self.prompt_service.extract_prompt(data)
            if not prompt.strip():
                raise HTTPException(status_code=400, detail="Не предоставлен промпт")

            request_id = f"frogcom-{datetime.now().timestamp()}"
            answer = self.orchestrator.generate_with_orchestration(
                user_prompt=prompt,
                max_tokens=req.max_tokens,
                temperature=req.temperature,
                top_p=req.top_p,
                stop=req.stop,
                seed=req.seed,
                request_id=request_id,
            )

            response = GenerateResponse(
                id=request_id,
                created=int(datetime.now().timestamp()),
                model=self.llm_service_primary.get_model_name(),
                choices=[
                    Choice(
                        index=0,
                        message=Message(role="assistant", content=answer),
                        finish_reason="generation success",
                    )
                ],
            )
            
            #if not answer or not str(answer).strip():
            #    raise HTTPException(status_code=500, detail="Пустой ответ от модели")

            self.logging_service.log_response({"response": response.model_dump()})
            return response
        except Exception as e:
            self.logging_service.log_error(e, {"request": data})
            raise HTTPException(status_code=500, detail=f"Ошибка генерации: {str(e)}")
