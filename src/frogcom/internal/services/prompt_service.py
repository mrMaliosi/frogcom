"""
Сервис для обработки промптов.

Этот модуль предоставляет функциональность для извлечения и обработки
промптов из различных форматов запросов.
"""
import ast
import json
from typing import Dict, Any, List, Optional

from frogcom.api.dto.models import Message
from frogcom.api.dto.models import FunctionDescription

class PromptService:
    """Сервис для обработки промптов."""
    
    @staticmethod
    def extract_prompt(data: Dict[str, Any]) -> str:
        """
        Универсальный парсер промпта из JSON-запросов разных форматов.
        
        Поддерживаемые форматы:
        - {"prompt": "text"}
        - {"inputs": "..."}
        - {"messages": [{"role": "user", "content": "..."}]}
        
        Args:
            data: Словарь с данными запроса
            
        Returns:
            Извлеченный промпт в виде строки
        """
        if "messages" in data and data["messages"]:
            return PromptService._extract_from_messages(data["messages"])
    
        if "prompt" in data and data["prompt"]:
            return str(data["prompt"])
        
        if "inputs" in data and data["inputs"]:
            return str(data["inputs"])
        
        # Fallback: взять всё тело как строку
        return json.dumps(data, ensure_ascii=False)
    
    @staticmethod
    def _extract_from_messages(messages: List[Dict[str, Any]]) -> str:
        """
        Извлекает промпт из списка сообщений.
        
        Args:
            messages: Список сообщений
            
        Returns:
            Извлеченный промпт
        """
        if not messages:
            return ""
        
        # Ищем последнее сообщение от пользователя
        for msg in reversed(messages):
            if msg.get("role") == "user":
                return msg.get("content", "")
        
        # Если не найдено сообщение от пользователя, берем последнее
        return messages[-1].get("content", "")
    
    @staticmethod
    def validate_messages(messages: List[Message]) -> bool:
        """
        Валидирует список сообщений.
        
        Args:
            messages: Список сообщений для валидации
            
        Returns:
            True если сообщения валидны, False иначе
        """
        if not messages:
            return False
        
        valid_roles = {"user", "assistant", "system"}
        
        for message in messages:
            if message.role not in valid_roles:
                return False
            
            if not message.content.strip():
                return False
        
        return True
    
    @staticmethod
    def extract_prompt_task(data: Dict[str, Any]) -> str:
        if "task" in data and data["task"]:
            return str(data["task"])
        
    @staticmethod
    def extract_code(data: Dict[str, Any]) -> str:
        if "code" in data and data["code"]:
            return str(data["code"])
        
    @staticmethod
    def extract_function_description(data: Dict[str, Any]) -> Optional['FunctionDescription']:
        # 1. Извлекаем строку, если она есть (по аналогии с вашим extract_code)
        text = None
        if "function" in data and data["function"]:
            text = str(data["function"])
            
        if not text:
            return None

        # 2. Очищаем от префикса, если он попал внутрь строки
        # (на случай если строка хранится как "function=FunctionDescription(...)")
        if text.startswith("function="):
            text = text.split("=", 1)[1].strip()

        try:
            # 3. Парсим строку как Python-выражение
            tree = ast.parse(text, mode='eval')
            
            # Проверяем, что это вызов конструктора (например, FunctionDescription(...))
            if not isinstance(tree.body, ast.Call):
                # Если в словаре лежал не repr() класса, а что-то другое
                raise ValueError("Содержимое поля 'function' не является вызовом конструктора")

            # 4. Собираем аргументы
            kwargs = {}
            for keyword in tree.body.keywords:
                # ast.literal_eval безопасно преобразует строки, числа, списки и None
                kwargs[keyword.arg] = ast.literal_eval(keyword.value)
            
            # 5. Возвращаем готовый объект
            return FunctionDescription(**kwargs)
            
        except Exception as e:
            print(f"Ошибка парсинга FunctionDescription: {e}")
            return None


    @staticmethod
    def format_messages_for_display(messages: List[Message]) -> str:
        """
        Форматирует сообщения для отображения.
        
        Args:
            messages: Список сообщений
            
        Returns:
            Отформатированная строка
        """
        formatted = []
        for msg in messages:
            role_emoji = {
                "user": "👤",
                "assistant": "🤖",
                "system": "⚙️"
            }.get(msg.role, "❓")
            
            formatted.append(f"{role_emoji} {msg.role}: {msg.content}")
        
        return "\n".join(formatted)
