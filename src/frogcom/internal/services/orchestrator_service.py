"""
Сервис оркестрации взаимодействия двух LLM моделей.

Логика:
- Первая (primary) модель генерирует первичный ответ по промпту пользователя
- Если orchestration.enabled и communication_rounds > 0:
  - Вторая (secondary) модель получает целевой промпт и ответ первой модели,
    формирует уточняющие вопросы/направления
  - Первая модель отвечает на эти уточнения, цикл повторяется заданное число раз
"""

from typing import List, Optional
from datetime import datetime
from frogcom.config.config import OrchestrationConfig
from frogcom.internal.services.llm_service import LLMService
from frogcom.internal.services.tracing_service import TracingService
from frogcom.internal.services.response_verifier import ResponseVerifier, VerificationResult


class OrchestratorService:
    """Оркестратор взаимодействия между двумя LLM."""

    def __init__(
        self,
        primary: LLMService,
        secondary: LLMService,
        orchestration_config: OrchestrationConfig,
        tracing_service: TracingService,
    ) -> None:
        self.primary = primary
        self.secondary = secondary
        self.config = orchestration_config
        self.tracing = tracing_service
        self.verifier = ResponseVerifier()

    def _build_secondary_prompt(self, primary_answer: str) -> str:
        """Строит промпт для второй модели на основе цели и ответа первой."""
        return (
            f"{self.config.secondary_goal_prompt}\n\n"
            f"Функция с комментарием:\n{primary_answer}\n\n"
        )
    
    def _verify_response(self, content: str, task_type: str, expected_questions: int = 0) -> VerificationResult:
        """Обертка над верификатором."""
        if task_type == "comment":
            return self.verifier.verify_comment(content)
        elif task_type == "questions":
            return self.verifier.verify_questions_list(content, expected_questions)
        return VerificationResult(True, content.strip())

    def _generate_with_retry(
        self,
        model: LLMService,
        prompts: List[str],
        task_type: str,
        expected_questions: int = 0,
        max_retries: int = 3,
        **kwargs
    ) -> str:
        """Универсальный метод генерации с повторными попытками."""
        last_response = ""
        
        for retry in range(max_retries):
            responses = model.generate_text(prompts=prompts, **kwargs)
            current_response = responses[0] if responses else ""
            
            print(f"[LOG] Attempt {retry + 1}/{max_retries} for {task_type}")

            # Верификация
            verification = self._verify_response(current_response, task_type, expected_questions)
            
            if verification.is_valid:
                return verification.content
            
            if not verification.needs_regeneration:
                # Если регенерация не поможет (ошибка не исправляема), возвращаем что есть
                return current_response
                
            last_response = current_response

        # Если исчерпали попытки, возвращаем последний ответ (даже если он не валиден)
        return last_response

    def generate_with_orchestration(
        self,
        user_prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None,
        seed: Optional[int] = None,
    ) -> str:
        """
        Запускает генерацию с участием двух моделей согласно конфигурации.
        Возвращает финальный ответ первой модели.
        """
        # Начинаем трассировку
        request_id : str = str(datetime.now().timestamp())
        trace_id = self.tracing.start_trace(user_prompt, request_id)
        print(user_prompt)

        gen_kwargs = {
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stop": stop,
            "seed": seed
        }

        # 1. Первичный ответ (Primary)
        primary_answer = self._generate_with_retry(
            model=self.primary,
            prompts=[user_prompt],
            task_type="comment",
            **gen_kwargs
        )

        if not self.config.enabled or self.config.communication_rounds <= 0:
            self.tracing.log_orchestration_disabled(trace_id, primary_answer)
            return primary_answer

        self.tracing.log_primary_response(trace_id, primary_answer, 0)

        # 2. Итеративная коммуникация
        for round_num in range(1, self.config.communication_rounds + 1):
            # Вторая формирует уточнения
            
            # 2a. Вторая модель формирует уточнения (Secondary)
            secondary_prompt = self._build_secondary_prompt(primary_answer)
            
            secondary_guidance = self._generate_with_retry(
                model=self.secondary,
                prompts=[secondary_prompt],
                task_type="questions",
                expected_questions=getattr(self.config, 'expected_questions_count', 3),
                **gen_kwargs
            )
            
            self.tracing.log_secondary_guidance(trace_id, secondary_guidance, round_num)

            # 2b. Первая модель отвечает на уточнения (Primary)
            followup_prompt = (
                "Обнови свой ответ, учитывая уточнения.\n"
                f"Уточнения:\n{secondary_guidance}\n"
                f"Исходный ответ:\n{primary_answer}\n"
                f"Сделай вывод согласно техническому заданию: {user_prompt}"
            )
            
            primary_answer = self._generate_with_retry(
                model=self.primary,
                prompts=[followup_prompt],
                task_type="comment",
                **gen_kwargs
            )

            self.tracing.log_primary_response(trace_id, primary_answer, round_num)

        # Логируем финальный ответ
        self.tracing.log_final_response(trace_id, primary_answer)
        
        return primary_answer
    

def _verify_response(self, content: str, task_type: str, expected_questions: int) -> VerificationResult:
    """Упрощенная верификация"""
    if task_type == "comment":
        return self.verifier.verify_comment(content)
    elif task_type == "questions" and expected_questions:
        return self.verifier.verify_questions_list(content, expected_questions)
    return VerificationResult(True, content.strip())


