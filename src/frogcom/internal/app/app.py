"""
Основное приложение FrogCom.

Этот модуль создает и настраивает FastAPI приложение.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from frogcom.config.config import config
from frogcom.internal.services.llm_service import LLMService
from frogcom.internal.services.logging_service import LoggingService
from frogcom.internal.services.tracing_service import TracingService
from frogcom.api.routes.health_routes import HealthRoutes
from frogcom.api.routes.generate_routes import GenerateRoutes
from frogcom.api.routes.llm_config_routes import LLMConfigRoutes
from frogcom.api.routes.orchestration_routes import OrchestrationRoutes
from frogcom.api.middleware import (
    LoggingMiddleware,
    SecurityMiddleware,
    RateLimitMiddleware,
    ErrorHandlingMiddleware,
    MonitoringMiddleware,
    AuthenticationMiddleware,
)
from frogcom.internal.services.orchestrator_service import OrchestratorService


def create_app() -> FastAPI:
    """Создает и настраивает FastAPI приложение."""
    
    # Создаем FastAPI приложение
    app = FastAPI(
        title=config.api.title,
        description=config.api.description,
        version=config.api.version,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # Инициализируем сервисы
    llm_service = LLMService(config.llm)
    secondary_llm_service = LLMService(config.secondary_llm)
    logging_service = LoggingService(config.logging)
    tracing_service = TracingService(config.logging)
    
    # Настраиваем middleware (порядок важен - последний добавленный выполняется первым)
    
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
    
    orchestrator = OrchestratorService(
        primary=llm_service,
        secondary=secondary_llm_service,
        orchestration_config=config.orchestration,
        tracing_service=tracing_service,
    )
    
    # Создаем и подключаем маршруты
    routes = [
        HealthRoutes(llm_service, logging_service, orchestrator),
        GenerateRoutes(llm_service, logging_service, orchestrator),
        LLMConfigRoutes(llm_service, logging_service, orchestrator),
        OrchestrationRoutes(llm_service, logging_service, orchestrator),
    ]
    for route in routes:
        app.include_router(route.get_router())
    
    return app


# Создаем экземпляр приложения
app = create_app()
