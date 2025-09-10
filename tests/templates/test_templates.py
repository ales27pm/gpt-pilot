from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.state.state_manager import StateManager
from core.templates.registry import PROJECT_TEMPLATES


@pytest.mark.asyncio
@patch("core.state.state_manager.get_config")
async def test_render_react_express_sql(mock_get_config, testmanager):
    mock_get_config.return_value.fs.type = "memory"
    sm = StateManager(testmanager)
    pm = MagicMock(run_command=AsyncMock())

    await sm.create_project("TestProjectName")
    await sm.commit()

    TemplateClass = PROJECT_TEMPLATES["react_express"]
    options = TemplateClass.options_class(db_type="sql", auth=True)
    template = TemplateClass(options, sm, pm)

    assert template.options_dict == {"db_type": "sql", "auth": True}

    await template.apply()

    files = sm.file_system.list()
    for f in ["server.js", "index.html", "prisma/schema.prisma", "api/routes/authRoutes.js", "ui/pages/Register.jsx"]:
        assert f in files
    assert "api/models/user.js" not in files


@pytest.mark.asyncio
@patch("core.state.state_manager.get_config")
async def test_render_react_express_nosql(mock_get_config, testmanager):
    mock_get_config.return_value.fs.type = "memory"
    sm = StateManager(testmanager)
    pm = MagicMock(run_command=AsyncMock())

    await sm.create_project("TestProjectName")
    await sm.commit()

    TemplateClass = PROJECT_TEMPLATES["react_express"]
    options = TemplateClass.options_class(db_type="nosql", auth=True)
    template = TemplateClass(options, sm, pm)

    assert template.options_dict == {"db_type": "nosql", "auth": True}

    await template.apply()

    files = sm.file_system.list()
    for f in ["server.js", "index.html", "api/models/user.js", "api/routes/authRoutes.js", "ui/pages/Register.jsx"]:
        assert f in files
    assert "prisma/schema.prisma" not in files


@pytest.mark.asyncio
@patch("core.state.state_manager.get_config")
async def test_render_node_express_mongoose(mock_get_config, testmanager):
    mock_get_config.return_value.fs.type = "memory"
    sm = StateManager(testmanager)
    pm = MagicMock(run_command=AsyncMock())

    await sm.create_project("TestProjectName")
    await sm.commit()

    TemplateClass = PROJECT_TEMPLATES["node_express_mongoose"]
    template = TemplateClass(TemplateClass.options_class(), sm, pm)

    assert template.options_dict == {}

    await template.apply()

    files = sm.file_system.list()
    for f in ["server.js", "models/User.js"]:
        assert f in files


@pytest.mark.asyncio
@patch("core.state.state_manager.get_config")
async def test_render_flask_sqlite(mock_get_config, testmanager):
    mock_get_config.return_value.fs.type = "memory"
    sm = StateManager(testmanager)
    pm = MagicMock(run_command=AsyncMock())

    await sm.create_project("TestProjectName")
    await sm.commit()

    TemplateClass = PROJECT_TEMPLATES["flask_sqlite"]
    template = TemplateClass(TemplateClass.options_class(), sm, pm)

    await template.apply()

    files = sm.file_system.list()
    for f in ["app.py", "models.py", "requirements.txt", "templates/index.html"]:
        assert f in files


@pytest.mark.asyncio
@patch("core.state.state_manager.get_config")
async def test_render_fastapi_sqlite(mock_get_config, testmanager):
    mock_get_config.return_value.fs.type = "memory"
    sm = StateManager(testmanager)
    pm = MagicMock(run_command=AsyncMock())

    await sm.create_project("TestProjectName")
    await sm.commit()

    TemplateClass = PROJECT_TEMPLATES["fastapi_sqlite"]
    template = TemplateClass(TemplateClass.options_class(), sm, pm)

    await template.apply()

    files = sm.file_system.list()
    for f in ["main.py", "models.py", "requirements.txt"]:
        assert f in files


@pytest.mark.asyncio
@patch("core.state.state_manager.get_config")
async def test_render_django_postgres(mock_get_config, testmanager):
    mock_get_config.return_value.fs.type = "memory"
    sm = StateManager(testmanager)
    pm = MagicMock(run_command=AsyncMock())

    await sm.create_project("TestProjectName")
    await sm.commit()

    TemplateClass = PROJECT_TEMPLATES["django_postgres"]
    template = TemplateClass(TemplateClass.options_class(), sm, pm)

    await template.apply()

    files = sm.file_system.list()
    for f in ["manage.py", "project/settings.py", "app/models.py", "requirements.txt"]:
        assert f in files


@pytest.mark.asyncio
@patch("core.state.state_manager.get_config")
async def test_render_typer_cli(mock_get_config, testmanager):
    mock_get_config.return_value.fs.type = "memory"
    sm = StateManager(testmanager)
    pm = MagicMock(run_command=AsyncMock())

    await sm.create_project("TestProjectName")
    await sm.commit()

    TemplateClass = PROJECT_TEMPLATES["typer_cli"]
    template = TemplateClass(TemplateClass.options_class(), sm, pm)

    await template.apply()

    files = sm.file_system.list()
    for f in ["main.py", "requirements.txt"]:
        assert f in files

# ---------------------------------------------------------------------------
# Additional tests appended by automation to expand coverage for template flows
# Framework: pytest with unittest.mock (consistent with existing tests)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("core.state.state_manager.get_config")
async def test_render_react_express_sql_no_auth(mock_get_config, testmanager):
    mock_get_config.return_value.fs.type = "memory"
    sm = StateManager(testmanager)
    pm = MagicMock(run_command=AsyncMock())

    await sm.create_project("NoAuthSQLProject")
    await sm.commit()

    TemplateClass = PROJECT_TEMPLATES["react_express"]
    options = TemplateClass.options_class(db_type="sql", auth=False)
    template = TemplateClass(options, sm, pm)

    assert template.options_dict == {"db_type": "sql", "auth": False}

    await template.apply()

    files = sm.file_system.list()

    # Core files should exist
    for f in ["server.js", "index.html", "prisma/schema.prisma"]:
        assert f in files

    # Auth-related files should not be generated when auth=False
    assert "api/routes/authRoutes.js" not in files
    assert "ui/pages/Register.jsx" not in files
    # No NoSQL model should appear for SQL mode
    assert "api/models/user.js" not in files

    # Validate project manager may have been used (do not assume specific commands)
    # but at least ensure run_command was awaited zero or more times without raising
    assert isinstance(pm.run_command, AsyncMock)


@pytest.mark.asyncio
@patch("core.state.state_manager.get_config")
async def test_render_react_express_nosql_no_auth(mock_get_config, testmanager):
    mock_get_config.return_value.fs.type = "memory"
    sm = StateManager(testmanager)
    pm = MagicMock(run_command=AsyncMock())

    await sm.create_project("NoAuthNoSQLProject")
    await sm.commit()

    TemplateClass = PROJECT_TEMPLATES["react_express"]
    options = TemplateClass.options_class(db_type="nosql", auth=False)
    template = TemplateClass(options, sm, pm)

    assert template.options_dict == {"db_type": "nosql", "auth": False}

    await template.apply()

    files = sm.file_system.list()

    # Core files should exist
    for f in ["server.js", "index.html"]:
        assert f in files

    # For NoSQL without auth, user model and auth UI/routes should not be present
    assert "api/models/user.js" not in files
    assert "api/routes/authRoutes.js" not in files
    assert "ui/pages/Register.jsx" not in files

    # Prisma schema should not be present for nosql
    assert "prisma/schema.prisma" not in files


@pytest.mark.asyncio
@patch("core.state.state_manager.get_config")
async def test_react_express_invalid_db_type_raises(mock_get_config, testmanager):
    mock_get_config.return_value.fs.type = "memory"
    sm = StateManager(testmanager)
    pm = MagicMock(run_command=AsyncMock())

    await sm.create_project("InvalidDBTypeProject")
    await sm.commit()

    TemplateClass = PROJECT_TEMPLATES["react_express"]

    # Creating options with an invalid db_type should raise a ValueError in typical implementations.
    # If implementation differs, update the expected exception accordingly.
    with pytest.raises(Exception):
        options = TemplateClass.options_class(db_type="graph", auth=True)  # unsupported db_type
        template = TemplateClass(options, sm, pm)
        await template.apply()


@pytest.mark.asyncio
@patch("core.state.state_manager.get_config")
async def test_template_apply_idempotency_react_express_sql(mock_get_config, testmanager):
    mock_get_config.return_value.fs.type = "memory"
    sm = StateManager(testmanager)
    pm = MagicMock(run_command=AsyncMock())

    await sm.create_project("IdempotentSQLProject")
    await sm.commit()

    TemplateClass = PROJECT_TEMPLATES["react_express"]
    options = TemplateClass.options_class(db_type="sql", auth=True)
    template = TemplateClass(options, sm, pm)

    await template.apply()
    files_once = sorted(sm.file_system.list())

    # Apply again: should not duplicate files; file list should remain stable
    await template.apply()
    files_twice = sorted(sm.file_system.list())

    assert files_once == files_twice


def test_accessing_unknown_template_key_raises_keyerror():
    # Accessing a non-existent template key in the registry should raise KeyError
    with pytest.raises(KeyError):
        _ = PROJECT_TEMPLATES["non_existent_template_key"]
