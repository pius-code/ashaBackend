from repository.projects import create_an_asha_project
from schema.project import projectCreate
from fastapi import APIRouter, HTTPException
from utils.logger import slogger

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


@router.post("/create_project")
async def create_project(projectCreate: projectCreate):
    try:
        result = await create_an_asha_project(projectCreate)
        slogger.info(f"Project created successfully: {projectCreate.name}")
        return {"detail": result}
    except Exception as e:
        slogger.error(f"Error creating project: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
