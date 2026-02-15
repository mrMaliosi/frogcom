"""
Сервис логирования для FrogCom.

Этот модуль предоставляет функциональность для логирования запросов и ответов.
"""

import json
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, TextIO
from uuid import uuid4

from frogcom.config.config import LoggingConfig


class LoggingService:
    """Сервис для управления логами."""
    log_dir: str = "default"
    log_dir_path: Path = None
    request_file_path: Path = None
    tracing_file_path: Path = None
    verificator_file: Path = None

    def __init__(self, config: LoggingConfig):
        """Инициализация сервиса логирования."""
        self.config = config
        self.log_dir_path = Path(config.log_dir)
        self.request_file_path = config.get_requests_file_path
        self.tracing_file_path = config.get_trace_file_path
        self.verificator_file_path = config.get_verificator_file_path
        self._ensure_log_directory()
    
    def _ensure_log_directory(self) -> None:
        """Создает директорию для логов если она не существует."""
        self.log_dir_path.mkdir(parents=True, exist_ok=True)
    
    def _update_files(self) -> None:
        """Обновляет пути к файлам логов."""
        self.request_file_path = self.log_dir_path / self.config.requests_file
        self.tracing_file_path = self.log_dir_path / self.config.trace_file
        self.verificator_file_path = self.log_dir_path / self.config.verificator_file

    def create_new_bench(self, new_bench_name: str) -> None:
        """Создаёт папку для нового бенчмарка."""
        self.log_dir = new_bench_name
        self.log_dir_path = Path(self.config.log_dir) / new_bench_name
        self._ensure_log_directory()
        self._update_files()

    # Логгирование специфичных данных
    # 1. Requests
    def log_request(self, data: Dict[str, Any]) -> None:
        """Логирует входящий запрос."""
        self._log_data(data, "REQUEST", self.request_file_path)

    def log_response(self, data: Dict[str, Any]) -> None:
        """Логирует исходящий ответ."""
        self._log_data(data, "RESPONSE", self.request_file_path)

    def log_error(self, error: Exception, context: Dict[str, Any] = None) -> None:
        """Логирует ошибку."""
        error_data = {
            "error": str(error),
            "type": type(error).__name__,
            "context": context or {},
        }
        self._log_data(error_data, "ERROR", self.request_file_path)

    # 2. Tracings.
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

    def log_trace_step(self, trace_id: str, data: str, type: str, step_number: int = 0) -> None:
        step_data = {
            "step": step_number,
            "type": type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        self._append_to_trace(step_data)

    # 3. Verificator
    def log_verificator_result(self, data: Dict[str, Any] = None) -> None:
        self._log_data(data, "LOG", self.verificator_file_path)

    def _write_data(self, data: Dict[str, Any], f: TextIO) -> None:
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        f.write(json_str.replace("\\n", "\n"))

    def _log_data(self, data: Dict[str, Any], log_type: str, file_path: str) -> None:
        """Записывает данные в лог файл."""
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.now().isoformat()}] {log_type}\n")
            self._write_data(data, f)
            f.write("\n" + "=" * 60 + "\n")
            f.flush()

    def _write_trace_entry(self, trace_data: Dict[str, Any]) -> None:
        """Записывает новую запись трассировки."""      
        with open(self.tracing_file_path, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"TRACE START: {trace_data['trace_id']}\n")
            f.write(f"{'='*80}\n")
            self._write_data(trace_data, f)
            f.flush()

    def _append_to_trace(self, step_data: Dict[str, Any]) -> None:
        """Добавляет шаг к существующей трассировке."""
        with open(self.tracing_file_path, "a", encoding="utf-8") as f:
            f.write(f"\n--- STEP {step_data.get('step', 'unknown')} ---\n")
            self._write_data(step_data, f)
            f.flush()