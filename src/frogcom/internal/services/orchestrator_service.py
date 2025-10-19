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

from frogcom.config.config import OrchestrationConfig
from frogcom.internal.services.llm_service import LLMService
from frogcom.internal.services.tracing_service import TracingService


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

    def _build_secondary_prompt(self, primary_answer: str) -> str:
        """Строит промпт для второй модели на основе цели и ответа первой."""
        return (
            f"{self.config.secondary_goal_prompt}\n\n"
            f"Ответ первой модели:\n{primary_answer}\n\n"
        )

    def generate_with_orchestration(
        self,
        user_prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None,
        seed: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> str:
        """
        Запускает генерацию с участием двух моделей согласно конфигурации.
        Возвращает финальный ответ первой модели.
        """
        # Начинаем трассировку
        trace_id = self.tracing.start_trace(user_prompt, request_id)
        
        # Первичный ответ от первой модели
        primary_answer = self.primary.generate_text(
            prompts=[user_prompt],
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=stop,
            seed=seed,
        )[0]

        if not self.config.enabled or self.config.communication_rounds <= 0:
            self.tracing.log_orchestration_disabled(trace_id, primary_answer)
            return primary_answer

        # Логируем первичный ответ
        self.tracing.log_primary_response(trace_id, primary_answer, 0)

        # Итеративная коммуникация
        for round_num in range(1, self.config.communication_rounds + 1):
            # Вторая формирует уточнения
            secondary_prompt = self._build_secondary_prompt(primary_answer)
            secondary_guidance = self.secondary.generate_text(
                prompts=[secondary_prompt],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop=stop,
                seed=seed,
            )[0]

            # Логируем уточнения второй модели
            self.tracing.log_secondary_guidance(trace_id, secondary_guidance, round_num)

            # Первая отвечает на уточнения второй
            followup_prompt = (
                f"Исходный ответ:\n{primary_answer}\n\n"
                f"Уточнения/вопросы второй модели:\n{secondary_guidance}\n\n"
                f"Обнови свой ответ, учитывая уточнения."
                f"Сделай вывод согласно тз: {user_prompt}"
            )
            primary_answer = self.primary.generate_text(
                prompts=[followup_prompt],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop=stop,
                seed=seed,
            )[0]

            # Логируем обновленный ответ первой модели
            self.tracing.log_primary_response(trace_id, primary_answer, round_num)

        # Логируем финальный ответ
        self.tracing.log_final_response(trace_id, primary_answer)
        
        return primary_answer


