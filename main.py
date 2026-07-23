from pathlib import Path
from fastapi import FastAPI
import uvicorn
from core.lifespan import create_lifespan
from utils.swagger import custom_openapi
from routes import api_router
from fastapi.middleware.cors import CORSMiddleware
from middleware.auth import verify_token_middleware
from dotenv import load_dotenv
import os
from agent.mcp_tools.tools import * # noqa
from agent.core.fastmcp import mcp


load_dotenv()


IS_DEV = os.getenv("ENV") == "development"
mcp_app = mcp.http_app()
app = FastAPI(
    title="ASHA",
    description="Backend for ASHA",
    version="1.0.0",
    lifespan=create_lifespan(mcp_app),
    docs_url="/docs" if IS_DEV else None,
    redoc_url=None,
)


app.include_router(api_router)
app.mount("/", mcp_app)
app.openapi = lambda: custom_openapi(app)
app.middleware("http")(verify_token_middleware)

frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        frontend_url,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def main():
    print("Hello from AHSA Backend!")
    venv_dir = str(Path(__file__).parent / ".venv")
    uvicorn.run("main:app", host="0.0.0.0" # noqa
                , port=8080, reload=True, reload_excludes=[venv_dir])


if __name__ == "__main__":
    main()
