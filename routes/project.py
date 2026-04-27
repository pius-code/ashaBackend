from middleware.auth import admin_protected_route, get_current_user
from repository.projects import create_an_asha_project, get_all_asha_projects
from schema.project import projectCreate
from fastapi import APIRouter, HTTPException, Depends
from utils.logger import slogger

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


@router.post("/create_project")
async def create_project(projectdet: projectCreate, current_user: dict = Depends(get_current_user)): # noqa
    try:
        result = await create_an_asha_project(projectdet, current_user)
        slogger.info(f"Project created successfully: {projectdet.Name}")
        return {"detail": result}
    except Exception as e:
        slogger.error(f"Error creating project: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/get_all_projects")
async def get_all_projects(_=Depends(admin_protected_route)):
    try:
        projects = await get_all_asha_projects() # noqa
        slogger.info("Fetched all projects successfully")
        return projects
    except Exception as e:
        slogger.error(f"Error fetching projects: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
