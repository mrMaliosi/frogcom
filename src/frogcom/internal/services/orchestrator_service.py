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
from frogcom.internal.services.logging_service import LoggingService
from frogcom.internal.services.response_verifier import ResponseVerifier, VerificationResult
from frogcom.config.config import config
import ollama

class OrchestratorService:
    """Оркестратор взаимодействия между двумя LLM."""

    def __init__(
        self,
        primary: LLMService,
        secondary: LLMService,
        orchestration_config: OrchestrationConfig,
        logging_service: LoggingService
    ) -> None:
        self.primary = primary
        self.secondary = secondary
        self.config = orchestration_config
        self.verifier = ResponseVerifier()
        self.logging_service = logging_service

    def _verify_response(self, content: str, task_type: str, expected_questions: int = 0) -> VerificationResult:
        """Обертка над верификатором."""
        if task_type == "comment" and self.config.enable_code_verification is True:
            return self.verifier.verify_comment(content)
        elif task_type == "questions" and self.config.enable_question_verification is True:
            return self.verifier.verify_questions_list(content, expected_questions)
        return VerificationResult(True, content.strip())

    def _generate(
        self,
        model: LLMService,
        prompts: List[str],
        **kwargs
    ) -> str:
        """Универсальный метод генерации."""
        responses = model.generate_text(prompts=prompts, **kwargs)
        return responses[0]

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

        empty_reponse_retryes: int = 0
        for retry in range(max_retries):
            responses = model.generate_text(prompts=prompts, **kwargs)
            current_response = responses[0] if responses else ""
            # if len(current_response) < 40:
            #     last_response = current_response
            #     retry -= 1
            #     empty_reponse_retryes += 1
            #     retry += empty_reponse_retryes // 20
            #     continue

            verification = self._verify_response(current_response, task_type, expected_questions)
            
            if verification.is_valid:
                self.logging_service.log_verificator_result({"attempt": f"{retry + 1}/{max_retries}", "task_type": f"{task_type}", "content": f"{verification.content}", "is_valid": f"{verification.is_valid}"})
                return verification.content
            
            last_response = current_response

        # Если исчерпали попытки, возвращаем последний ответ (даже если он не валиден)
        self.logging_service.log_verificator_result({"attempt": f"{retry + 1}/{max_retries}", "task_type": f"{task_type}"})
        return last_response
    
    def _generate_with_ollama(
        self,
        prompts: List[str],
        task_type: str,
        expected_questions: int = 0,
        max_retries: int = 3,
        **kwargs
    ) -> str:
        response = ollama.chat(
            model="gpt-oss:120b-cloud",
            messages=[
                {"role": "user", "content": prompts[0]},
            ],
        )
        return response["message"]["content"].strip()

    def generate_with_primary(
        self,
        user_prompt: str
    ) -> str:
        primary_gen_params = self.primary.get_gen_conf()
        return self._generate(self.primary, prompts=[user_prompt], **primary_gen_params)
    
    def generate_with_secondary(
        self,
        user_prompt: str
    ) -> str:
        secondary_gen_params = self.secondary.get_gen_conf()
        return self._generate(self.secondary, prompts=[user_prompt], **secondary_gen_params)

    def _generate_answer(self,
        model: LLMService,
        prompts: List[str],
        task_type: str,
        expected_questions: int = 0,
        max_retries: int = 3,
        **kwargs) -> str:
        if model._config.is_ollama is True:
            return self._generate_with_ollama(
                prompts=prompts,
                task_type=task_type,
                expected_questions=expected_questions,
                max_retries=max_retries,
                **kwargs,
            )
        else:
            return self._generate_with_retry(
                model=model,
                prompts=prompts,
                task_type=task_type,
                expected_questions=expected_questions,
                max_retries=max_retries,
                **kwargs,
            )


    def generate_with_orchestration(
        self,
        user_prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None,
        seed: Optional[int] = None,
        request_id : str = str(datetime.now().timestamp())
    ) -> str:
        """
        Запускает генерацию с участием двух моделей согласно конфигурации.
        Возвращает финальный ответ первой модели.
        """
        # Начинаем трассировку
        trace_id = self.logging_service.start_trace(user_prompt, request_id)
        primary_gen_params = self.primary.get_gen_conf()
        secondary_gen_params = config.secondary_llm.get_gen_config()
        # 1. Первичный ответ (Primary)
        first_comment: str = self._generate_answer(
            model=self.primary,
            prompts=[user_prompt],
            task_type="comment",
            expected_questions=0,
            max_retries=3,
            **primary_gen_params
        )
        self.logging_service.log_trace_step(trace_id, first_comment, "first_comment", 0)

        if not self.config.enabled or self.config.communication_rounds <= 0:
            return first_comment

        # 2. Итеративная коммуникация
        for round_num in range(1, self.config.communication_rounds + 1):    
            # 2a. Вторая модель формирует уточнения (Secondary)
            secondary_prompt: str = (
                f"{self.config.secondary_goal_prompt}"
                f"{first_comment}\n"
            )
            questions: str = self._generate_answer(
                model=self.secondary,
                prompts=[secondary_prompt],
                task_type="questions",
                expected_questions=getattr(self.config, 'expected_questions_count', 3),
                max_retries=3,
                **secondary_gen_params
            )
            self.logging_service.log_trace_step(trace_id, questions, "questions", round_num)

            # 2b. Первая модель отвечает на уточнения (Primary)
            followup_prompt = (
                "Скорректирй исходный комментарий, учитывая список вопросов.\n"
                "\nНапиши ТОЛЬКО обновленный комментарий.\n"
                f"Список вопросов: {questions}\n"
                f"Исходный комментарий: {first_comment}\n"
                "Ничего кроме обновленного комментария писать НЕ нужно."
            )
            comment: str = self._generate_answer(
                model=self.primary,
                prompts=[followup_prompt],
                task_type="comment",
                expected_questions=getattr(self.config, 'expected_questions_count', 3),
                max_retries=3,
                **primary_gen_params
            )
            self.logging_service.log_trace_step(trace_id, comment, "after_comment", round_num)
        return comment

    def generate_with_questions_first(
        self,
        user_prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None,
        seed: Optional[int] = None,
        request_id : str = str(datetime.now().timestamp())
    ) -> str:
        """
        Запускает генерацию с участием двух моделей согласно конфигурации.
        Возвращает финальный ответ первой модели.
        """
        # "Ты — эксперт по промпт-инжинирингу. Проанализируй данный промпт и составь список конкретных вопросов, на которые LLM должна ответить при его выполнении. Верни ТОЛЬКО нумерованный список вопросов.\n\n"   #В конце списка вопросов напиши \"•\"
        #    f"Промпт: {user_prompt}\n"
        followup_prompt: str = (
            "Задай несколько (3-5) вопросов к коду.\nВопросы должны помочь улучшить комментарий, помогая понять поведение функции и проверять корректность комментария.\nКаждый вопрос с новой строки.\n\nИспользуй нумерацию:\n1. ...\n2. ...\nБез пояснений.\n\n"
            f"Промпт: {user_prompt}\n"
        )
        
        trace_id = self.logging_service.start_trace(followup_prompt, request_id)
        primary_gen_params = self.primary.get_gen_conf()
        secondary_gen_params = config.secondary_llm.get_gen_config()

        # 1. Список вопросов
        questions = self._generate_with_retry(
            model=self.secondary,
            prompts=[followup_prompt],
            task_type="questions",
            **secondary_gen_params,
        )
        self.logging_service.log_trace_step(trace_id, questions, "questions", 0)

        # 2. Первая модель отвечает на вопросы (Primary)
        followup_prompt = (
            "Выполни задание, учитывая список вопросов.\n\n"        # Как только выполнишь задание - напиши \"•\"\n
            f"Вопросы: {questions}\n"
            f"Задание: {user_prompt}\n"
            "Ничего кроме комментария в заданном формате писать НЕ нужно.\n"
        )
        answer: str = self._generate_with_retry(
            model=self.primary,
            prompts=[followup_prompt],
            task_type="comment",
            **primary_gen_params
        )
        self.logging_service.log_trace_step(trace_id, answer, "comment", 1)

        return answer

    def generate_comment(
            self,
            user_prompt: str,
            max_tokens: Optional[int] = None,
            temperature: Optional[float] = None,
            top_p: Optional[float] = None,
            stop: Optional[List[str]] = None,
            seed: Optional[int] = None,
            request_id : str = str(datetime.now().timestamp())
        ) -> str:
            if config.orchestration.generator_work_type == "question":
                return self.generate_with_questions_first(
                    user_prompt=user_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    stop=stop,
                    seed=seed,
                    request_id=request_id
                )
            else:
                return self.generate_with_orchestration(
                    user_prompt=user_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    stop=stop,
                    seed=seed,
                    request_id=request_id
                )