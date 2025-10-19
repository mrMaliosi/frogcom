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
    log_file: str = "requests.log"
    trace_file: str = "orchestration_trace.log"
    max_log_size_mb: int = 100
    log_ttl_days: int = 7
    
    @property
    def log_file_path(self) -> Path:
        """Полный путь к файлу логов."""
        return Path(self.log_dir) / self.log_file
    
    @property
    def trace_file_path(self) -> Path:
        """Полный путь к файлу трассировки оркестрации."""
        return Path(self.log_dir) / self.trace_file


@dataclass
class LLMConfig:
    """Конфигурация LLM модели."""
    
    model_name: str = "facebook/opt-125m"
    gpu_memory_utilization: float = 0.5
    disable_log_stats: bool = False
    max_tokens: int = 256
    temperature: float = 0.7
    top_p: float = 0.9
    stop: Optional[list[str]] = None
    seed: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует конфигурацию в словарь для vLLM."""
        config = {
            "model": self.model_name,
            "gpu_memory_utilization": self.gpu_memory_utilization,
            "disable_log_stats": self.disable_log_stats,
        }
        return config


@dataclass
class OrchestrationConfig:
    """Конфигурация оркестрации между основной и второй LLM."""
    
    communication_rounds: int = 1  # сколько раз общаться со второй моделью
    secondary_goal_prompt: str = (
        "Ты — проверяющий ассистент. Проанализируй ответ и предложи уточняющие вопросы, "
        "которые помогут улучшить ответ. Верни только список вопросов или указания."
    )
    enabled: bool = True


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
class AppConfig:
    """Основная конфигурация приложения."""
    
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    secondary_llm: LLMConfig = field(default_factory=LLMConfig)
    api: APIConfig = field(default_factory=APIConfig)
    orchestration: OrchestrationConfig = field(default_factory=OrchestrationConfig)
    
    @classmethod
    def from_env(cls) -> "AppConfig":
        """Создает конфигурацию из переменных окружения."""
        return cls(
            logging=LoggingConfig(
                log_dir=os.getenv("LOG_DIR", "logs"),
                log_file=os.getenv("LOG_FILE", "requests.log"),
                max_log_size_mb=int(os.getenv("MAX_LOG_SIZE_MB", "100")),
                log_ttl_days=int(os.getenv("LOG_TTL_DAYS", "7")),
            ),
            llm=LLMConfig(
                model_name=os.getenv("LLM_MODEL", "Qwen/Qwen2.5-0.5B-Instruct"),
                gpu_memory_utilization=float(os.getenv("GPU_MEMORY_UTILIZATION", "0.5")),
                disable_log_stats=os.getenv("DISABLE_LOG_STATS", "false").lower() == "true",
                max_tokens=int(os.getenv("MAX_TOKENS", "4096")),
                temperature=float(os.getenv("TEMPERATURE", "0.7")),
                top_p=float(os.getenv("TOP_P", "0.9")),
            ),
            secondary_llm=LLMConfig(
                model_name=os.getenv("LLM_MODEL_SECONDARY", "Qwen/Qwen2.5-0.5B-Instruct"),
                gpu_memory_utilization=float(os.getenv("GPU_MEMORY_UTILIZATION_SECONDARY", "0.5")),
                disable_log_stats=os.getenv("DISABLE_LOG_STATS_SECONDARY", "false").lower() == "true",
                max_tokens=int(os.getenv("MAX_TOKENS_SECONDARY", "512")),
                temperature=float(os.getenv("TEMPERATURE_SECONDARY", "0.7")),
                top_p=float(os.getenv("TOP_P_SECONDARY", "0.9")),
            ),
            api=APIConfig(
                host=os.getenv("API_HOST", "0.0.0.0"),
                port=int(os.getenv("API_PORT", "8888")),
                reload=os.getenv("API_RELOAD", "true").lower() == "true",
                rate_limit=int(os.getenv("API_RATE_LIMIT", "60")),
                cors_origins=os.getenv("API_CORS_ORIGINS", "*").split(","),
                max_request_size=int(os.getenv("API_MAX_REQUEST_SIZE", str(10 * 1024 * 1024))),
                api_key=os.getenv("API_KEY"),
            ),
            orchestration=OrchestrationConfig(
                communication_rounds=int(os.getenv("COMMUNICATION_ROUNDS", "1")),
                secondary_goal_prompt=os.getenv("SECONDARY_GOAL_PROMPT", (
                    "Ты — проверяющий ассистент. Проанализируй ответ и предложи уточняющие вопросы, "
                    "которые помогут улучшить ответ. Верни только список вопросов или указания."
                )),
                enabled=os.getenv("ORCHESTRATION_ENABLED", "true").lower() == "true",
            ),
        )

config = AppConfig.from_env()
