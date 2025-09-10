from .base import BaseProjectTemplate, NoOptions


class FastapiSqliteProjectTemplate(BaseProjectTemplate):
    stack = "backend"
    name = "fastapi_sqlite"
    path = "fastapi_sqlite"
    description = "FastAPI app using SQLModel ORM with SQLite database"
    file_descriptions = {
        "main.py": "FastAPI application with startup hook and sample endpoint.",
        "models.py": "SQLModel models used by the application.",
        "requirements.txt": "Python dependencies for FastAPI and SQLModel.",
        "README.md": "Project overview and setup instructions.",
    }
    summary = "\n".join(
        [
            "* FastAPI web app configured for SQLite using SQLModel",
            "* User model and automatic table creation on startup",
            "* Simple endpoint listing users",
            "* requirements.txt for dependencies",
        ]
    )
    options_class = NoOptions
    options_description = ""

    async def install_hook(self):
        await self.process_manager.run_command("pip install -r requirements.txt")
