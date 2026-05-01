import sys

import uvicorn
from zstar.api.start_backend import create_app
from zstar.config import load_config

if __name__ == "__main__":
    config_path = sys.argv[1] if len(sys.argv) > 1 else None
    settings = load_config(config_path)
    app = create_app(settings)

    uvicorn.run(
        app,
        host=settings.backend.host,
        port=settings.backend.port,
    )
