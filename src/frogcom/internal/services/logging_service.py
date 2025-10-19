"""
Сервис логирования для FrogCom.

Этот модуль предоставляет функциональность для логирования запросов и ответов.
"""

import json
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any

from frogcom.config.config import LoggingConfig


class LoggingService:
    """Сервис для управления логами."""
    
    def __init__(self, config: LoggingConfig):
        """Инициализация сервиса логирования."""
        self.config = config
        self._ensure_log_directory()
    
    def _ensure_log_directory(self) -> None:
        """Создает директорию для логов если она не существует."""
        Path(self.config.log_dir).mkdir(parents=True, exist_ok=True)
    
    def _should_rotate_log(self) -> bool:
        """Проверяет, нужно ли ротировать лог файл."""
        if not os.path.exists(self.config.log_file_path):
            return False
        
        # Проверка размера файла
        size_mb = os.path.getsize(self.config.log_file_path) / (1024 * 1024)
        if size_mb > self.config.max_log_size_mb:
            return True
        
        # Проверка возраста файла
        mtime = datetime.fromtimestamp(os.path.getmtime(self.config.log_file_path))
        if datetime.now() - mtime > timedelta(days=self.config.log_ttl_days):
            return True
        
        return False
    
    def _rotate_log(self) -> None:
        """Ротирует лог файл."""
        if not os.path.exists(self.config.log_file_path):
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{self.config.log_file_path.stem}_{timestamp}.log"
        backup_path = self.config.log_file_path.parent / backup_name
        
        shutil.move(str(self.config.log_file_path), str(backup_path))
    
    def log_request(self, data: Dict[str, Any]) -> None:
        """Логирует входящий запрос."""
        self._log_data(data, "REQUEST")
    
    def log_response(self, data: Dict[str, Any]) -> None:
        """Логирует исходящий ответ."""
        self._log_data(data, "RESPONSE")
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None) -> None:
        """Логирует ошибку."""
        error_data = {
            "error": str(error),
            "type": type(error).__name__,
            "context": context or {},
        }
        self._log_data(error_data, "ERROR")
    
    def _log_data(self, data: Dict[str, Any], log_type: str) -> None:
        """Записывает данные в лог файл."""
        if self._should_rotate_log():
            self._rotate_log()
        
        with open(self.config.log_file_path, "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.now().isoformat()}] {log_type}\n")
            f.write(json.dumps(data, ensure_ascii=False, indent=2))
            f.write("\n" + "=" * 60 + "\n")
