from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from core.config import DBConfig, get_config
from core.db.session import SessionManager
from core.db.setup import run_migrations
from core.state.state_manager import StateManager

app = FastAPI(title="GPT Pilot Web")

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
FRONTEND_DIST = FRONTEND_DIR / "dist"
FRONTEND_INDEX = FRONTEND_DIST / "index.html"
if FRONTEND_INDEX.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

db_config: Optional[DBConfig] = None


@app.on_event("startup")
def startup() -> None:
    global db_config
    config = get_config()
    run_migrations(config.db)
    db_config = config.db


@app.get("/api/projects")
async def get_projects():
    sm = StateManager(SessionManager(db_config))
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
    sm = StateManager(SessionManager(db_config))
    project = await sm.create_project(name)
    await sm.session_manager.close()
    return {"id": project.id.hex, "name": project.name}


@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: UUID):
    sm = StateManager(SessionManager(db_config))
    deleted = await sm.delete_project(project_id)
    await sm.session_manager.close()
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
    return JSONResponse(status_code=204, content=None)


@app.get("/")
def index():
    if FRONTEND_INDEX.exists():
        return FileResponse(FRONTEND_INDEX)
    return HTMLResponse("<h1>GPT Pilot API</h1><p>Frontend build not found.</p>")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
