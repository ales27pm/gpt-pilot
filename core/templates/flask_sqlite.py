from .base import BaseProjectTemplate, NoOptions


class FlaskSqliteProjectTemplate(BaseProjectTemplate):
    stack = "backend"
    name = "flask_sqlite"
    path = "flask_sqlite"
    description = "Flask app using SQLAlchemy ORM with SQLite database"
    file_descriptions = {
        "app.py": "Entry point for the Flask application configuring SQLAlchemy and registering routes.",
        "models.py": "Defines a basic User model using SQLAlchemy.",
        "requirements.txt": "Python dependencies for Flask and SQLAlchemy.",
        "templates/base.html": "Base Jinja2 template providing the page layout.",
        "templates/index.html": "Simple index page extending the base template.",
        "README.md": "Project overview and setup instructions.",
    }
    summary = "\n".join(
        [
            "* Flask web app configured for SQLite using SQLAlchemy",
            "* Basic User model and database initialization",
            "* Jinja2 templates with base layout and index page",
            "* requirements.txt for dependencies",
        ]
    )
    options_class = NoOptions
    options_description = ""

    async def install_hook(self):
        """
        Install the template's Python dependencies by running "pip install -r requirements.txt".
        
        This asynchronous install hook uses the template's process manager to execute the pip
        command in the current working directory so that the scaffolded project's requirements
        are installed after generation.
        """
        await self.process_manager.run_command("pip install -r requirements.txt")
