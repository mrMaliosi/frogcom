"""
Middleware для API FrogCom.

Этот модуль содержит middleware для логирования, безопасности,
мониторинга и обработки запросов.
"""

import json
import time

from typing import Callable, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request, Response
from fastapi.responses import JSONResponse

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from frogcom.config.config import config
from frogcom.internal.services.logging_service import LoggingService


def init_middleware(app : FastAPI, logging_service : LoggingService):
    """ Настраиваем middleware (порядок важен - последний добавленный выполняется первым) """
    # 1. Обработка ошибок (должен быть первым)
    app.add_middleware(ErrorHandlingMiddleware, logging_service=logging_service)
    
    # 2. Мониторинг производительности
    app.add_middleware(MonitoringMiddleware)
    
    # 3. Ограничение скорости запросов
    app.add_middleware(RateLimitMiddleware, requests_per_minute=config.api.rate_limit)
    
    # 4. Аутентификация (если настроена)
    if config.api.api_key:
        app.add_middleware(AuthenticationMiddleware, api_key=config.api.api_key)
    
    # 5. Безопасность
    app.add_middleware(SecurityMiddleware, max_request_size=config.api.max_request_size)
    
    # 6. Логирование
    app.add_middleware(LoggingMiddleware, logging_service=logging_service)
    
    # 7. CORS (должен быть последним)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.api.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware для логирования HTTP запросов и ответов."""
    
    def __init__(self, app: ASGIApp, logging_service: LoggingService):
        """Инициализация middleware."""
        super().__init__(app)
        self.logging_service = logging_service
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Обрабатывает запрос и логирует его."""
        start_time = time.time()
        
        # Логируем входящий запрос
        request_data = await self._extract_request_data(request)
        self.logging_service.log_request(request_data)
        
        # Обрабатываем запрос
        response = await call_next(request)
        
        process_time = time.time() - start_time
        
        response_data = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "process_time": process_time,
        }
        self.logging_service.log_response(response_data)
        
        # Добавляем заголовок с временем обработки
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    
    async def _extract_request_data(self, request: Request) -> dict:
        """Извлекает данные из запроса для логирования."""
        # Читаем тело запроса
        body = await request.body()
        
        request_data = {
            "url": str(request.url),
            "method": request.method,
            "headers": dict(request.headers),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "body_raw": body.decode("utf-8", errors="replace"),
        }
        
        # Пытаемся парсить JSON
        try:
            if body:
                request_data["body_json"] = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            pass
        
        return request_data


class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware для базовой безопасности."""
    
    def __init__(self, app: ASGIApp, max_request_size: int = 10 * 1024 * 1024):
        """Инициализация middleware."""
        super().__init__(app)
        self.max_request_size = max_request_size
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Обрабатывает запрос с проверками безопасности."""
        
        # Проверка размера тела запроса
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_request_size:
            return JSONResponse(
                status_code=413,
                content={
                    "error": "Request body too large", 
                    "max_size": f"{self.max_request_size // (1024 * 1024)}MB"
                }
            )
        
        # Добавляем заголовки безопасности
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware для ограничения скорости запросов."""
    
    def __init__(self, app: ASGIApp, requests_per_minute: int = 60):
        """Инициализация middleware."""
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = {}  # В продакшене использовать Redis
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Обрабатывает запрос с проверкой лимитов."""
        
        # Получаем IP клиента
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Очищаем старые записи (старше минуты)
        self.requests = {
            ip: timestamps for ip, timestamps in self.requests.items()
            if any(ts > current_time - 60 for ts in timestamps)
        }
        
        # Проверяем лимит для текущего IP
        if client_ip in self.requests:
            # Удаляем старые запросы
            self.requests[client_ip] = [
                ts for ts in self.requests[client_ip] 
                if ts > current_time - 60
            ]
            
            if len(self.requests[client_ip]) >= self.requests_per_minute:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "limit": self.requests_per_minute,
                        "window": "1 minute"
                    }
                )
        else:
            self.requests[client_ip] = []
        
        # Добавляем текущий запрос
        self.requests[client_ip].append(current_time)
        
        response = await call_next(request)
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware для обработки ошибок."""
    
    def __init__(self, app: ASGIApp, logging_service: LoggingService):
        """Инициализация middleware."""
        super().__init__(app)
        self.logging_service = logging_service
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Обрабатывает запрос с обработкой ошибок."""
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Логируем ошибку
            self.logging_service.log_error(e, {
                "url": str(request.url),
                "method": request.method,
                "client_ip": request.client.host if request.client else None,
            })
            
            # Возвращаем стандартизированный ответ об ошибке
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "type": type(e).__name__,
                    "message": str(e) if hasattr(e, '__str__') else "Unknown error"
                }
            )


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware для мониторинга производительности."""
    
    def __init__(self, app: ASGIApp):
        """Инициализация middleware."""
        super().__init__(app)
        self.request_count = 0
        self.total_time = 0.0
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Обрабатывает запрос с мониторингом."""
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        
        # Обновляем метрики
        self.request_count += 1
        self.total_time += process_time
        
        # Добавляем метрики в заголовки
        response.headers["X-Request-Count"] = str(self.request_count)
        response.headers["X-Average-Response-Time"] = str(
            self.total_time / self.request_count
        )
        
        return response


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware для базовой аутентификации (опциональный)."""
    
    def __init__(self, app: ASGIApp, api_key: Optional[str] = None, skip_paths: list[str] = None):
        """Инициализация middleware."""
        super().__init__(app)
        self.api_key = api_key
        self.skip_paths = skip_paths or ["/health", "/docs", "/redoc", "/openapi.json"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Обрабатывает запрос с проверкой аутентификации."""
        
        # Пропускаем аутентификацию для определенных путей
        if any(request.url.path.startswith(path) for path in self.skip_paths):
            return await call_next(request)
        
        # Если API ключ не настроен, пропускаем аутентификацию
        if not self.api_key:
            return await call_next(request)
        
        # Проверяем API ключ
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"error": "Missing or invalid authorization header"}
            )
        
        provided_key = auth_header[7:]  # Убираем "Bearer "
        if provided_key != self.api_key:
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid API key"}
            )
        
        return await call_next(request)
