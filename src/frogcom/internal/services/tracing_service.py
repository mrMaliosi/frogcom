"""
Сервис трассировки для оркестрации LLM.

Этот модуль предоставляет функциональность для логирования
взаимодействия между двумя LLM моделями в отдельный файл.
"""

import json
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from uuid import uuid4

from frogcom.config.config import LoggingConfig


class TracingService:
    """Сервис для трассировки взаимодействия LLM моделей."""
    
    def __init__(self, config: LoggingConfig):
        """Инициализация сервиса трассировки."""
        self.config = config
        self._ensure_log_directory()
    
    def _ensure_log_directory(self) -> None:
        """Создает директорию для логов если она не существует."""
        Path(self.config.log_dir).mkdir(parents=True, exist_ok=True)
    
    def _should_rotate_trace(self) -> bool:
        """Проверяет, нужно ли ротировать файл трассировки."""
        if not os.path.exists(self.config.trace_file_path):
            return False
        
        # Проверка размера файла
        size_mb = os.path.getsize(self.config.trace_file_path) / (1024 * 1024)
        if size_mb > self.config.max_log_size_mb:
            return True
        
        # Проверка возраста файла
        mtime = datetime.fromtimestamp(os.path.getmtime(self.config.trace_file_path))
        if datetime.now() - mtime > timedelta(days=self.config.log_ttl_days):
            return True
        
        return False
    
    def _rotate_trace(self) -> None:
        """Ротирует файл трассировки."""
        if not os.path.exists(self.config.trace_file_path):
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{self.config.trace_file_path.stem}_{timestamp}.log"
        backup_path = self.config.trace_file_path.parent / backup_name
        
        shutil.move(str(self.config.trace_file_path), str(backup_path))
    
    def start_trace(self, user_prompt: str, request_id: Optional[str] = None) -> str:
        """
        Начинает новую трассировку взаимодействия.
        
        Args:
            user_prompt: Промпт пользователя
            request_id: ID запроса (если не указан, генерируется автоматически)
            
        Returns:
            ID трассировки
        """
        if request_id is None:
            request_id = str(uuid4())
        
        trace_data = {
            "trace_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "user_prompt": user_prompt,
            "orchestration_enabled": True,
            "steps": []
        }
        
        self._write_trace_entry(trace_data)
        return request_id
    
    def log_primary_response(self, trace_id: str, response: str, step_number: int = 0) -> None:
        """
        Логирует ответ основной модели.
        
        Args:
            trace_id: ID трассировки
            response: Ответ основной модели
            step_number: Номер шага (0 для первичного ответа)
        """
        step_data = {
            "step": step_number,
            "type": "primary_response",
            "timestamp": datetime.now().isoformat(),
            "response": response
        }
        
        self._append_to_trace(trace_id, step_data)
    
    def log_secondary_guidance(self, trace_id: str, guidance: str, step_number: int) -> None:
        """
        Логирует уточнения от второй модели.
        
        Args:
            trace_id: ID трассировки
            guidance: Уточнения от второй модели
            step_number: Номер шага
        """
        step_data = {
            "step": step_number,
            "type": "secondary_guidance",
            "timestamp": datetime.now().isoformat(),
            "guidance": guidance
        }
        
        self._append_to_trace(trace_id, step_data)
    
    def log_final_response(self, trace_id: str, final_response: str) -> None:
        """
        Логирует финальный ответ.
        
        Args:
            trace_id: ID трассировки
            final_response: Финальный ответ
        """
        step_data = {
            "step": "final",
            "type": "final_response",
            "timestamp": datetime.now().isoformat(),
            "final_response": final_response
        }
        
        self._append_to_trace(trace_id, step_data)
    
    def log_orchestration_disabled(self, trace_id: str, response: str) -> None:
        """
        Логирует случай, когда оркестрация отключена.
        
        Args:
            trace_id: ID трассировки
            response: Ответ основной модели
        """
        step_data = {
            "step": 0,
            "type": "orchestration_disabled",
            "timestamp": datetime.now().isoformat(),
            "response": response
        }
        
        self._append_to_trace(trace_id, step_data)
    
    def _write_trace_entry(self, trace_data: Dict[str, Any]) -> None:
        """Записывает новую запись трассировки."""
        if self._should_rotate_trace():
            self._rotate_trace()
        
        with open(self.config.trace_file_path, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"TRACE START: {trace_data['trace_id']}\n")
            f.write(f"{'='*80}\n")
            f.write(json.dumps(trace_data, ensure_ascii=False, indent=2))
            f.write("\n")
    
    def _append_to_trace(self, trace_id: str, step_data: Dict[str, Any]) -> None:
        """Добавляет шаг к существующей трассировке."""
        if self._should_rotate_trace():
            self._rotate_trace()
        
        with open(self.config.trace_file_path, "a", encoding="utf-8") as f:
            f.write(f"\n--- STEP {step_data.get('step', 'unknown')} ---\n")
            f.write(json.dumps(step_data, ensure_ascii=False, indent=2))
            f.write("\n")
    
    def get_trace_summary(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает краткую сводку трассировки.
        
        Args:
            trace_id: ID трассировки
            
        Returns:
            Словарь с краткой информацией о трассировке или None
        """
        if not os.path.exists(self.config.trace_file_path):
            return None
        
        try:
            with open(self.config.trace_file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Простой поиск по ID (в реальном проекте лучше использовать базу данных)
            if f"TRACE START: {trace_id}" in content:
                return {
                    "trace_id": trace_id,
                    "found": True,
                    "file_path": str(self.config.trace_file_path)
                }
        except Exception:
            pass
        
        return None
