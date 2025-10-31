# main.py
from fastapi import FastAPI
from frogcom.config.config import config
from frogcom.api.middleware.middleware import init_middleware
from frogcom.internal.contexts.llm_orchestrator import LLMOrchestrator
from frogcom.api.routes.health_routes import HealthRoutes
from frogcom.api.routes.generate_routes import GenerateRoutes
from frogcom.api.routes.llm_config_routes import LLMConfigRoutes
from frogcom.api.routes.orchestration_routes import OrchestrationRoutes

def register_routes(app: FastAPI) -> None:
    """Создаёт инстансы роутов и регистрирует их в приложении."""
    routes = [
        HealthRoutes(
            app.state.llms["primary"],
            app.state.llms["secondary"],
            app.state.logging_service,
            app.state.orchestrator,
        ),
        GenerateRoutes(
            app.state.llms["primary"],
            app.state.llms["secondary"],
            app.state.logging_service,
            app.state.orchestrator,
        ),
        LLMConfigRoutes(
            app.state.llms["primary"],
            app.state.llms["secondary"],
            app.state.logging_service,
            app.state.orchestrator,
        ),
        OrchestrationRoutes(
            app.state.llms["primary"],
            app.state.llms["secondary"],
            app.state.logging_service,
            app.state.orchestrator,
        ),
    ]
    for route in routes:
        app.include_router(route.get_router())

def create_app() -> FastAPI:
    app = FastAPI(
        title=config.api.title,
        description=config.api.description,
        version=config.api.version,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    orchestrator_ctx = LLMOrchestrator()

    # раздаём зависимости
    app.state.llms = orchestrator_ctx.llms
    app.state.logging_service = orchestrator_ctx.logging_service
    app.state.tracing_service = orchestrator_ctx.tracing_service
    app.state.orchestrator = orchestrator_ctx.orchestrator

    init_middleware(app, app.state.logging_service)

    register_routes(app)

    return app

app = create_app()