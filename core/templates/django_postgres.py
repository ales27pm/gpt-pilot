from .base import BaseProjectTemplate, NoOptions


class DjangoPostgresProjectTemplate(BaseProjectTemplate):
    stack = "backend"
    name = "django_postgres"
    path = "django_postgres"
    description = "Django project configured for PostgreSQL"
    file_descriptions = {
        "manage.py": "Django management script.",
        "project/settings.py": "Minimal settings configured for PostgreSQL.",
        "app/models.py": "Simple model example.",
        "requirements.txt": "Dependencies for Django and PostgreSQL driver.",
        "README.md": "Project overview and setup instructions.",
    }
    summary = "\n".join(
        [
            "* Django project configured for PostgreSQL",
            "* Basic app with single model and view",
            "* manage.py for administrative tasks",
            "* requirements.txt listing dependencies",
        ]
    )
    options_class = NoOptions
    options_description = ""

    async def install_hook(self):
        await self.process_manager.run_command("pip install -r requirements.txt")
