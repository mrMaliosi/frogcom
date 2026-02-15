"""
Конфигурация приложения FrogCom.

Этот модуль содержит все настройки приложения, включая конфигурацию LLM,
логирования и API.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from pathlib import Path


@dataclass
class LoggingConfig:
    """Конфигурация системы логирования."""
    
    log_dir: str = "logs"
    requests_file: str = "requests.log"
    verificator_file: str = "verificator.log"
    trace_file: str = "orchestration_trace.log"
    
    @property
    def get_verificator_file_path(self) -> Path:
        """Полный путь к файлу логов."""
        return Path(self.log_dir, self.verificator_file)
    
    @property
    def get_requests_file_path(self) -> Path:
        """Полный путь к файлу логов."""
        return Path(self.log_dir, self.requests_file)
    
    @property
    def get_trace_file_path(self) -> Path:
        """Полный путь к файлу трассировки оркестрации."""
        return Path(self.log_dir, self.trace_file)


@dataclass
class LLMConfig:
    """Конфигурация LLM модели."""
    
    model_name: str = "facebook/opt-125m"
    gpu_memory_utilization: float = 0.5
    max_model_len: int = 4096
    disable_log_stats: bool = False
    max_tokens: int = 256
    temperature: float = 0.7
    top_p: float = 0.9
    stop: Optional[list[str]] = None
    seed: Optional[int] = 1234
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует конфигурацию в словарь для vLLM."""
        return {
            "model": self.model_name,
            "gpu_memory_utilization": self.gpu_memory_utilization,
            "max_model_len": self.max_model_len,
            "disable_log_stats": self.disable_log_stats,
            "max_num_batched_tokens": 8192,
            "max_num_seqs": 2,
            "enforce_eager": False,
            "seed": self.seed
        }
    
    def get_gen_config(self) -> Dict[str, Any]:
        return {
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "stop": self.stop,
            "seed": self.seed
        } 


@dataclass
class OrchestrationConfig:
    """Конфигурация оркестрации между основной и второй LLM."""
    
    communication_rounds: int = 1  # сколько раз общаться со второй моделью
    secondary_goal_prompt: str = (
        "Ты — проверяющий ассистент. Проанализируй ответ и предложи уточняющие вопросы, "
        "которые помогут улучшить ответ. Верни ТОЛЬКО список вопросов, которые могут помочь улучшить ответ."
        "Без объяснений. Без дополнений. Только список вопросов."
        "Пример вывода:"
        "- Какие конкретные недопустимые символы могут привести к IllegalArgumentException?"
        "- Какова максимальная длина текстового запроса в текущей реализации?"
    )
    enabled: bool = True
    enable_code_verification: bool = False
    enable_question_verification: bool = False
    enable_only_one_model: bool = False


@dataclass
class APIConfig:
    """Конфигурация API сервера."""
    
    host: str = "0.0.0.0"
    port: int = 8888
    reload: bool = True
    title: str = "FrogCom API"
    description: str = "API для генерации текста с использованием LLM"
    version: str = "0.2.0"
    
    # Middleware настройки
    rate_limit: int = 60  # запросов в минуту
    cors_origins: list[str] = field(default_factory=lambda: ["*"])  # CORS origins
    max_request_size: int = 10 * 1024 * 1024  # 10MB максимальный размер запроса
    api_key: Optional[str] = None  # API ключ для аутентификации (опционально)

@dataclass
class SolverConfig:
    """Конфигурация режима обработки запросов."""
    
    hard_definition_of_parse: bool = False
    enable_language_information: bool = False
    generator_work_type: str = "standart"


@dataclass
class AppConfig:
    """Основная конфигурация приложения."""
    
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    secondary_llm: LLMConfig = field(default_factory=LLMConfig)
    api: APIConfig = field(default_factory=APIConfig)
    orchestration: OrchestrationConfig = field(default_factory=OrchestrationConfig)
    solver: SolverConfig = field(default_factory=SolverConfig)
    
    @classmethod
    def from_env(cls) -> "AppConfig":
        """Создает конфигурацию из переменных окружения."""
        return cls(
            logging=LoggingConfig(
                log_dir=os.getenv("LOG_DIR", "logs"),
            ),
            llm=LLMConfig(
                model_name=os.getenv("LLM_MODEL", "Qwen/Qwen3-4B-Instruct-2507"),
                gpu_memory_utilization=float(os.getenv("GPU_MEMORY_UTILIZATION", "0.6")),
                max_model_len=int(os.getenv("MAX_MODEL_LEN", "4096")),
                disable_log_stats=os.getenv("DISABLE_LOG_STATS", "false").lower() == "true",
                max_tokens=int(os.getenv("MAX_TOKENS", "1024")),
                temperature=float(os.getenv("TEMPERATURE", "0.4")),
                top_p=float(os.getenv("TOP_P", "0.9")),
                stop=os.getenv("STOP", ["•"]),
                seed=int(os.getenv("SEED", "1234")),
            ),
            secondary_llm=LLMConfig(
                model_name=os.getenv("LLM_MODEL_SECONDARY", "bond005/meno-tiny-0.1"),
                gpu_memory_utilization=float(os.getenv("GPU_MEMORY_UTILIZATION_SECONDARY", "0.3")),
                max_model_len=int(os.getenv("MAX_MODEL_LEN", "4096")),
                disable_log_stats=os.getenv("DISABLE_LOG_STATS_SECONDARY", "false").lower() == "true",
                max_tokens=int(os.getenv("MAX_TOKENS_SECONDARY", "1024")),
                temperature=float(os.getenv("TEMPERATURE_SECONDARY", "0.4")),
                top_p=float(os.getenv("TOP_P_SECONDARY", "0.9")),
                stop=os.getenv("STOP", ["•"]),
                seed=int(os.getenv("SEED", "32767")),
            ),
            api=APIConfig(
                host=os.getenv("API_HOST", "0.0.0.0"),
                port=int(os.getenv("API_PORT", "8888")),
                reload=os.getenv("API_RELOAD", "true").lower() == "true",
                rate_limit=int(os.getenv("API_RATE_LIMIT", "500")),
                cors_origins=os.getenv("API_CORS_ORIGINS", "*").split(","),
                max_request_size=int(os.getenv("API_MAX_REQUEST_SIZE", str(10 * 1024 * 1024))),
                api_key=os.getenv("API_KEY"),
            ),
            orchestration=OrchestrationConfig(
                communication_rounds=int(os.getenv("COMMUNICATION_ROUNDS", "1")),
                secondary_goal_prompt=os.getenv("SECONDARY_GOAL_PROMPT", (
                    "Задача: Ты — программист.Проанализируй комментарий к функции и задай вопросы, чтобы лучше понять её логику. Верни ТОЛЬКО нумерованный список вопросов. В конце списка вопросов напиши \"•\"\n\n"
                )),
                enabled=os.getenv("ORCHESTRATION_ENABLED", "true").lower() == "true",
                enable_code_verification=os.getenv("ENABLE_QUESTION_VERIFICATION", "false").lower() == "true",
                enable_question_verification=os.getenv("ENABLE_QUESTION_VERIFICATION", "false").lower() == "true",
                enable_only_one_model=os.getenv("ENABLE_ONLY_ONE_MODEL", "true").lower() == "true",
            ),
            solver=SolverConfig(
                hard_definition_of_parse=os.getenv("hard_definition_of_parse", "false").lower() == "true",
                enable_language_information=os.getenv("ENABLE_LANGUAGE_INFORMATION", "false").lower() == "true",
                generator_work_type=os.getenv("GENERATOR_WORK_TYPE", "standart"),
            ),
        )

config = AppConfig.from_env()
