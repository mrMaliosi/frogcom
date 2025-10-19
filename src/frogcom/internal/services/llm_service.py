"""
Сервис для работы с LLM моделями.

Этот модуль предоставляет функциональность для управления LLM моделями
и генерации текста.
"""

import threading
from typing import List, Optional, Dict, Any
from vllm import LLM, SamplingParams

from frogcom.config.config import LLMConfig
from frogcom.api.dto.models import LLMConfigRequest, LLMConfigResponse


class LLMService:
    """Сервис для работы с LLM моделями."""
    
    def __init__(self, initial_config: LLMConfig):
        """Инициализация сервиса LLM."""
        self._config = initial_config
        self._llm: Optional[LLM] = None
        self._lock = threading.Lock()
        self._initialize_llm()
    
    def _initialize_llm(self) -> None:
        """Инициализирует LLM модель."""
        with self._lock:
            if self._llm is not None:
                # Освобождаем ресурсы предыдущей модели
                del self._llm
            
            try:
                self._llm = LLM(**self._config.to_dict())
            except Exception as e:
                raise RuntimeError(f"Не удалось инициализировать LLM: {e}")
    
    def get_config(self) -> LLMConfigResponse:
        """Возвращает текущую конфигурацию LLM."""
        return LLMConfigResponse(
            model_name=self._config.model_name,
            gpu_memory_utilization=self._config.gpu_memory_utilization,
            disable_log_stats=self._config.disable_log_stats,
            max_tokens=self._config.max_tokens,
            temperature=self._config.temperature,
            top_p=self._config.top_p,
            stop=self._config.stop,
            seed=self._config.seed,
            status="loaded" if self._llm is not None else "not_loaded"
        )
    
    def update_config(self, config_request: LLMConfigRequest) -> LLMConfigResponse:
        """Обновляет конфигурацию LLM."""
        with self._lock:
            # Обновляем конфигурацию
            if config_request.model_name is not None:
                self._config.model_name = config_request.model_name
            if config_request.gpu_memory_utilization is not None:
                self._config.gpu_memory_utilization = config_request.gpu_memory_utilization
            if config_request.disable_log_stats is not None:
                self._config.disable_log_stats = config_request.disable_log_stats
            if config_request.max_tokens is not None:
                self._config.max_tokens = config_request.max_tokens
            if config_request.temperature is not None:
                self._config.temperature = config_request.temperature
            if config_request.top_p is not None:
                self._config.top_p = config_request.top_p
            if config_request.stop is not None:
                self._config.stop = config_request.stop
            if config_request.seed is not None:
                self._config.seed = config_request.seed
            
            # Переинициализируем модель если изменились критические параметры
            critical_params_changed = (
                config_request.model_name is not None or
                config_request.gpu_memory_utilization is not None or
                config_request.disable_log_stats is not None
            )
            
            if critical_params_changed:
                self._initialize_llm()
        
        return self.get_config()
    
    def is_loaded(self) -> bool:
        """Проверяет, загружена ли модель."""
        return self._llm is not None
    
    def get_model_name(self) -> str:
        """Возвращает название текущей модели."""
        return self._config.model_name
    
    def generate_text(
        self,
        prompts: List[str],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        stop: Optional[List[str]] = None,
        seed: Optional[int] = None,
    ) -> List[str]:
        """
        Генерирует текст на основе промптов.
        
        Args:
            prompts: Список промптов для генерации
            max_tokens: Максимальное количество токенов (по умолчанию из конфигурации)
            temperature: Температура (по умолчанию из конфигурации)
            top_p: Top-p параметр (по умолчанию из конфигурации)
            stop: Список стоп-слов (по умолчанию из конфигурации)
            seed: Сид для воспроизводимости (по умолчанию из конфигурации)
        
        Returns:
            Список сгенерированных текстов
            
        Raises:
            RuntimeError: Если LLM не инициализирован
        """
        if not self.is_loaded():
            raise RuntimeError("LLM не инициализирован")
        
        # Используем параметры из запроса или из конфигурации
        sampling_params = SamplingParams(
            max_tokens=max_tokens or self._config.max_tokens,
            temperature=temperature or self._config.temperature,
            top_p=top_p or self._config.top_p,
            stop=stop or self._config.stop,
            seed=seed or self._config.seed,
        )
        
        with self._lock:
            outputs = self._llm.generate(prompts, sampling_params)
        
        return [output.outputs[0].text for output in outputs]
