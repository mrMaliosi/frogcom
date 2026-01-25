"""
Модели данных для API FrogCom.

Этот модуль содержит Pydantic модели для валидации входящих и исходящих данных.
"""
import ast
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class Message(BaseModel):
    """Модель сообщения в чате."""
    
    role: str = Field(..., description="Роль отправителя (user, assistant, system)")
    content: str = Field(..., description="Содержимое сообщения")


class GenerateRequest(BaseModel):
    """Модель запроса на генерацию текста."""
    
    prompt: Optional[str] = Field(None, description="Прямой промпт для генерации")
    messages: Optional[List[Message]] = Field(None, description="Список сообщений в формате чата")
    max_tokens: Optional[int] = Field(None, ge=1, le=4096, description="Максимальное количество токенов")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Температура для генерации")
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0, description="Top-p параметр")
    stop: Optional[List[str]] = Field(None, description="Список стоп-слов")
    seed: Optional[int] = Field(None, description="Сид для воспроизводимости")
    model: Optional[str] = Field(None, description="Название модели (игнорируется, используется текущая)")


class Choice(BaseModel):
    """Модель выбора в ответе."""
    
    index: int = Field(..., description="Индекс выбора")
    message: Message = Field(..., description="Сообщение ассистента")
    finish_reason: str = Field(..., description="Причина завершения генерации")


class GenerateResponse(BaseModel):
    """Модель ответа на запрос генерации."""
    
    id: str = Field(..., description="Уникальный идентификатор запроса")
    object: str = Field(default="text_completion", description="Тип объекта")
    created: int = Field(..., description="Время создания в Unix timestamp")
    model: str = Field(..., description="Использованная модель")
    choices: List[Choice] = Field(..., description="Список сгенерированных вариантов")


class LLMConfigRequest(BaseModel):
    """Модель запроса на изменение конфигурации LLM."""
    
    model_name: Optional[str] = Field(None, description="Название модели")
    gpu_memory_utilization: Optional[float] = Field(
        None, ge=0.1, le=1.0, description="Использование GPU памяти"
    )
    disable_log_stats: Optional[bool] = Field(None, description="Отключить статистику логов")
    max_tokens: Optional[int] = Field(None, ge=1, le=4096, description="Максимальное количество токенов")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Температура")
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0, description="Top-p параметр")
    stop: Optional[List[str]] = Field(None, description="Список стоп-слов")
    seed: Optional[int] = Field(None, description="Сид для воспроизводимости")


class LLMConfigResponse(BaseModel):
    """Модель ответа с текущей конфигурацией LLM."""
    
    model_name: str = Field(..., description="Текущее название модели")
    gpu_memory_utilization: float = Field(..., description="Использование GPU памяти")
    disable_log_stats: bool = Field(..., description="Статистика логов отключена")
    max_tokens: int = Field(..., description="Максимальное количество токенов")
    temperature: float = Field(..., description="Температура")
    top_p: float = Field(..., description="Top-p параметр")
    stop: Optional[List[str]] = Field(None, description="Список стоп-слов")
    seed: Optional[int] = Field(None, description="Сид")
    status: str = Field(..., description="Статус конфигурации")


class ErrorResponse(BaseModel):
    """Модель ответа с ошибкой."""
    
    error: str = Field(..., description="Описание ошибки")
    type: str = Field(..., description="Тип ошибки")
    details: Optional[Dict[str, Any]] = Field(None, description="Дополнительные детали ошибки")


class HealthResponse(BaseModel):
    """Модель ответа для проверки здоровья сервиса."""
    
    status: str = Field(..., description="Статус сервиса")
    timestamp: datetime = Field(..., description="Время проверки")
    version: str = Field(..., description="Версия API")
    model_loaded: bool = Field(..., description="Модель загружена")


class OrchestrationConfigRequest(BaseModel):
    """Модель запроса на изменение конфигурации оркестрации."""
    
    enabled: Optional[bool] = Field(None, description="Включить оркестрацию")
    communication_rounds: Optional[int] = Field(
        None, ge=0, le=10, description="Количество раундов общения со второй моделью"
    )
    secondary_goal_prompt: Optional[str] = Field(
        None, description="Целевой промпт второй модели"
    )


class OrchestrationConfigResponse(BaseModel):
    """Модель ответа с текущей конфигурацией оркестрации."""
    
    enabled: bool = Field(..., description="Оркестрация включена")
    communication_rounds: int = Field(..., description="Количество раундов")
    secondary_goal_prompt: str = Field(..., description="Целевой промпт второй модели")


class CommentResponse(BaseModel):
    """Модель Ответа для списка комментариев к функциям."""

    comment: str = Field(..., description="Комментарий к функции")


class CommentRequest(BaseModel):
    """Модель запроса для создания комментариев к списку функций."""

    task: str = Field(..., description="Задача к функции")
    code: str = Field(..., description="Сама функций")
    function: str = Field(..., description="Распаршенная функция")

@dataclass
class FunctionDescription:
    language: str
    full_function_text: str = None
    function_text: str = None
    docstring: Optional[str] = None
    full_function_lines_length: int = 0
    function_lines_length: int = 0
    docstring_lines_length: Optional[int] = 0
    name: str = None
    qualified_name: str = None
    namespace: Optional[str] = None
    signature_text: str = ""
    return_type: Optional[str] = None
    parameters: list[str] = field(default_factory=list)
    start_line: int = -1
    end_line: int = -1
    is_method: bool = False
    class_name: Optional[str] = None
    class_description: Optional[str] = None
    decorators: list[str] = field(default_factory=list)
    modifiers: list[str] = field(default_factory=list)
    visibility: Optional[str] = None
    has_body: bool = True
    is_constructor: bool = False