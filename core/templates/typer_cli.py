from .base import BaseProjectTemplate, NoOptions


class TyperCliProjectTemplate(BaseProjectTemplate):
    stack = "backend"
    name = "typer_cli"
    path = "typer_cli"
    description = "CLI application using Typer"
    file_descriptions = {
        "main.py": "Entry point defining Typer commands.",
        "requirements.txt": "Python dependencies for Typer.",
        "README.md": "Project overview and usage instructions.",
    }
    summary = "\n".join(
        [
            "* Command-line interface built with Typer",
            "* `hello` command greeting the user",
            "* requirements.txt for dependencies",
        ]
    )
    options_class = NoOptions
    options_description = ""

    async def install_hook(self):
        """
        Run installation of Python dependencies for the generated project.
        
        This asynchronous hook invokes the template's process manager to execute
        `pip install -r requirements.txt` in the current working directory, installing
        packages listed in the generated requirements.txt file.
        """
        await self.process_manager.run_command("pip install -r requirements.txt")
