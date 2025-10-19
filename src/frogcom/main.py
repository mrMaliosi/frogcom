"""
Точка входа для FrogCom приложения.
"""

import uvicorn
from frogcom.config.config import config

if __name__ == "__main__":
    uvicorn.run(
        "frogcom.internal.app.app:app",
        host=config.api.host,
        port=config.api.port,
        reload=config.api.reload,
    )
