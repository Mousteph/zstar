import uvicorn
from zstar.api.settings import get_settings


if __name__ == "__main__":
    settings = get_settings("config.yaml")

    uvicorn.run(
        "zstar.api.start_backend:app",
        host=settings.backend_host,
        port=settings.backend_port
    )
