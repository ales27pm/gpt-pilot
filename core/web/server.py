from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from core.config import get_config
from core.db.session import SessionManager
from core.db.setup import run_migrations
from core.state.state_manager import StateManager

app = FastAPI(title="GPT Pilot Web")

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

db: Optional[SessionManager] = None


@app.on_event("startup")
def startup() -> None:
    global db
    config = get_config()
    run_migrations(config.db)
    db = SessionManager(config.db)


@app.get("/api/projects")
async def get_projects():
    sm = StateManager(db)
    projects = await sm.list_projects()
    data = []
    for project in projects:
        last_updated = None
        p = {"name": project.name, "id": project.id.hex, "branches": []}
        for branch in project.branches:
            b = {"name": branch.name, "id": branch.id.hex, "steps": []}
            for state in branch.states:
                if not last_updated or state.created_at > last_updated:
                    last_updated = state.created_at
                b["steps"].append({"name": state.action or f"Step #{state.step_index}", "step": state.step_index})
            if b["steps"]:
                b["steps"][-1]["name"] = "Latest step"
            p["branches"].append(b)
        p["updated_at"] = last_updated.isoformat() if last_updated else None
        data.append(p)
    return {"projects": data}


@app.post("/api/projects")
async def create_project(payload: dict):
    name = payload.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Missing project name")
    sm = StateManager(db)
    project = await sm.create_project(name)
    return {"id": project.id.hex, "name": project.name}


@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: UUID):
    sm = StateManager(db)
    deleted = await sm.delete_project(project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
    return JSONResponse(status_code=204, content=None)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")
