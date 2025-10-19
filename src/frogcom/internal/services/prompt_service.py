"""
Сервис для обработки промптов.

Этот модуль предоставляет функциональность для извлечения и обработки
промптов из различных форматов запросов.
"""

import json
from typing import Dict, Any, List

from frogcom.api.dto.models import Message


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
