import typer

app = typer.Typer()


@app.command()
def hello(name: str = "World"):
    """
    Print a greeting "Hello {name}" to stdout using typer.echo.
    
    Parameters:
        name (str): Name to include in the greeting. Defaults to "World".
    """
    typer.echo(f"Hello {name}")


if __name__ == "__main__":
    app()
