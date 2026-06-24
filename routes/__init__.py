from fastapi import APIRouter
from routes.user import router as user_router
from routes.project import router as project_router
from routes.asha import router as asha_router
from routes.asr import router as asr_router


api_router = APIRouter()
api_router.include_router(user_router)
api_router.include_router(project_router)
api_router.include_router(asha_router)
api_router.include_router(asr_router)
