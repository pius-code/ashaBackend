from fastapi import FastAPI
import uvicorn
from core.lifespan import lifespan
from utils.swagger import custom_openapi
from routes import api_router
from fastapi.middleware.cors import CORSMiddleware
from middleware.auth import verify_token_middleware
from dotenv import load_dotenv
import os
from agent.mcp_tools.tools import *
from agent.core.fastmcp import mcp




load_dotenv()


IS_DEV = os.getenv("ENV") == "development"

app = FastAPI(
    title="ASHA",
    description="Backend for ASHA",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if IS_DEV else None,
    redoc_url=None,
)


app.openapi = lambda: custom_openapi(app)
app.middleware("http")(verify_token_middleware)
app.include_router(api_router)

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
    uvicorn.run("main:app", host="0.0.0.0"
                , port=8080, reload=True)


if __name__ == "__main__":
    main()
