from datetime import datetime
from fastapi import Request, HTTPException
from frogcom.api.routes.base import BaseRoutes
from frogcom.api.dto.models import FunctionDescription, GenerateResponse, GenerateRequest, Choice, Message, CommentRequest, CommentResponse, SolverConfigResponse, SolverConfigRequest
from frogcom.config.config import config, SolverConfig
from typing import List, Optional

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
            "/prompt-comment",
            self.prompt_comment,
            methods=["POST"],
            response_model=GenerateResponse,
            summary="Генерация текста",
            description="Генерирует текст на основе промпта или сообщений"
        )

        self.router.add_api_route(
            "/prompt-primary",
            self.prompt_to_primary_llm,
            methods=["POST"],
            response_model=GenerateResponse,
            summary="Генерация текста",
            description="Генерирует текст на основе промпта или сообщений"
        )

        self.router.add_api_route(
            "/prompt-primary",
            self.prompt_to_secondary_llm,
            methods=["POST"],
            response_model=GenerateResponse,
            summary="Генерация текста",
            description="Генерирует текст на основе промпта или сообщений"
        )

        self.router.add_api_route(
            "/config/solver",
            self.update_solver_config,
            methods=["PUT"],
            response_model=SolverConfigResponse,
            summary="Обновить конфигурацию LLM",
            description="Обновляет конфигурацию выбранной LLM по идентификатору llm_id",
        )

    async def generate_comment(self, request: Request, req: CommentRequest) -> CommentResponse:
        """
        Генерирует комментарий на основе предобработанного запроса.
        """
        try:
            data = req.model_dump()
            full_prompt_text : str = self.prompt_service.extract_full_prompt_task(data)
            prompt_task : str = self.prompt_service.extract_prompt_task(data)
            code : str = self.prompt_service.extract_code(data)
            function_desc : FunctionDescription = self.prompt_service.extract_function_description(data)

            # Create prompt
            task = self.prompt_service.task_creation(full_prompt_text, prompt_task, code, function_desc)

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
        
    async def prompt_comment(self, request: Request, req: GenerateRequest) -> GenerateResponse:
        """
        Генерирует комментарий на основе предобработанного запроса.
        """
        try:
            data = req.model_dump()
            full_prompt_text : str = self.prompt_service.extract_full_prompt_task(data)
            prompt_task : str = self.prompt_service.extract_prompt_task(data)
            code : str = self.prompt_service.extract_code(data)
            function_desc : FunctionDescription = self.prompt_service.extract_function_description(data)

            # Create prompt
            task = self.prompt_service.task_creation(full_prompt_text, prompt_task, code, function_desc)

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
    
    async def prompt_to_primary_llm(self, request: Request, req: GenerateRequest) -> GenerateResponse:
        """
        Генерирует комментарий на основе предобработанного запроса.
        """
        try:
            data = req.model_dump()             # TODO: exclude_unset=True - добавить в release
            prompt = self.prompt_service.extract_prompt(data)
            if not prompt.strip():
                raise HTTPException(status_code=400, detail="Не предоставлен промпт")

            request_id : str = str(datetime.now().timestamp())
            answer = self.orchestrator.generate_with_primary(
                user_prompt=prompt,
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

            self.logging_service.log_response({"response": response.model_dump()})
            return response
        except Exception as e:
            self.logging_service.log_error(e, {"request": data})
            raise HTTPException(status_code=500, detail=f"Ошибка генерации: {str(e)}")
        
    async def prompt_to_secondary_llm(self, request: Request, req: GenerateRequest) -> GenerateResponse:
        """
        Генерирует комментарий на основе предобработанного запроса.
        """
        try:
            data = req.model_dump()             # TODO: exclude_unset=True - добавить в release
            prompt = self.prompt_service.extract_prompt(data)
            if not prompt.strip():
                raise HTTPException(status_code=400, detail="Не предоставлен промпт")

            request_id : str = str(datetime.now().timestamp())
            answer = self.orchestrator.generate_with_secondary(
                user_prompt=prompt,
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

            self.logging_service.log_response({"response": response.model_dump()})
            return response
        except Exception as e:
            self.logging_service.log_error(e, {"request": data})
            raise HTTPException(status_code=500, detail=f"Ошибка генерации: {str(e)}")
        

    async def prompt_comment(self, request: Request, req: GenerateRequest) -> GenerateResponse:
        """
        Генерирует комментарий на основе предобработанного запроса.
        """
        try:
            data = req.model_dump()
            prompt = self.prompt_service.extract_prompt(data)
            if not prompt.strip():
                raise HTTPException(status_code=400, detail="Не предоставлен промпт")

            request_id : str = str(datetime.now().timestamp())
            answer = self.orchestrator.generate_with_orchestration(
                user_prompt=prompt,
                max_tokens=self.llm_service_primary.get_config().max_tokens,
                temperature=req.temperature,
                top_p=req.top_p,
                stop=[], #req.stop,
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

            self.logging_service.log_response({"response": response.model_dump()})
            return response
        except Exception as e:
            self.logging_service.log_error(e, {"request": data})
            raise HTTPException(status_code=500, detail=f"Ошибка генерации: {str(e)}")

    async def update_solver_config(
            self,
            request: Request,
            config_request: SolverConfigRequest,
        ) -> SolverConfigResponse:
            """Обновляет конфигурацию выбранной LLM."""
            config.solver.hard_definition_of_parse = config_request.hard_definition_of_parse
            config.solver.enable_language_information = config_request.enable_language_information
            return SolverConfigResponse(**config_request.model_dump())