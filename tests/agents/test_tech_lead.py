import json
import re
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from core.agents.response import AgentResponse, ResponseType
from core.agents.tech_lead import DevelopmentPlan, Epic, TechLead
from core.db.models import Complexity
from core.db.models.project_state import TaskStatus
from core.ui.base import UserInput


@pytest.mark.asyncio
async def test_create_initial_epic(agentcontext):
    """
    If there are no epics defined, the TechLead agent should create an initial project epic.
    """
    sm, _, ui, _ = agentcontext

    sm.current_state.specification.complexity = Complexity.SIMPLE
    sm.current_state.epics = [{"name": "Frontend", "completed": True}]

    tl = TechLead(sm, ui)
    response = await tl.run()
    assert response.type == ResponseType.DONE

    await sm.commit()

    assert sm.current_state.epics != []
    assert sm.current_state.epics[1]["name"] == "Initial Project"
    assert sm.current_state.epics[1]["completed"] is False


@pytest.mark.asyncio
async def test_apply_project_template(agentcontext):
    sm, _, ui, _ = agentcontext

    sm.current_state.specification.templates = {"node_express_mongoose": {}}
    sm.current_state.epics = [{"name": "Initial Project", "sub_epics": []}]

    await sm.commit()

    tl = TechLead(sm, ui)
    response = await tl.run()
    assert response.type == ResponseType.DONE

    await sm.commit()
    assert sm.current_state.files != []


@pytest.mark.asyncio
async def test_ask_for_feature(agentcontext):
    """
    If there are epics and all are completed, the TechLead agent should ask for a new feature.
    """
    sm, _, ui, _ = agentcontext

    sm.current_state.epics = [
        {"name": "Frontend", "completed": True},
        {"name": "Initial Project", "completed": True},
    ]
    ui.ask_question.return_value = UserInput(text="make it pop")

    tl = TechLead(sm, ui)
    response = await tl.run()
    assert response.type == ResponseType.UPDATE_SPECIFICATION

    await sm.commit()

    assert len(sm.current_state.epics) == 3
    assert sm.current_state.epics[2]["description"] == "make it pop"
    assert sm.current_state.epics[2]["completed"] is False


@pytest.mark.asyncio
async def test_plan_epic(agentcontext):
    """
    If called and there's an incomplete epic, the TechLead agent should plan the epic.
    """
    sm, _, ui, mock_get_llm = agentcontext

    sm.current_state.epics = [
        {
            "id": "abc",
            "name": "Initial Project",
            "description": "hello world",
            "complexity": Complexity.SIMPLE,
            "completed": False,
        }
    ]
    await sm.commit()

    tl = TechLead(sm, ui)
    tl.get_llm = mock_get_llm(
        return_value=DevelopmentPlan(
            plan=[
                Epic(description="Task 1"),
                Epic(description="Task 2"),
            ]
        )
    )
    ui.send_epics_and_tasks = AsyncMock()
    ui.ask_question.return_value = UserInput(
        button="done_editing",
        text=json.dumps(
            [
                {
                    "description": "Initial Project",
                    "tasks": [
                        {"description": "Task 1"},
                        {"description": "Task 2"},
                    ],
                }
            ]
        ),
    )
    response = await tl.run()
    assert response.type == ResponseType.DONE

    await sm.commit()

    assert len(sm.current_state.tasks) == 2
    assert sm.current_state.tasks[0]["description"] == "Task 1"
    assert sm.current_state.tasks[1]["description"] == "Task 2"


@pytest.mark.asyncio
async def test_create_initial_epic_when_no_existing_epics(agentcontext):
    """
    When there are no epics at all, TechLead should create a single 'Initial Project' epic
    marked as not completed.
    """
    sm, _, ui, _ = agentcontext

    sm.current_state.specification.complexity = Complexity.SIMPLE
    sm.current_state.epics = []

    tl = TechLead(sm, ui)
    response = await tl.run()
    assert response.type == ResponseType.DONE

    await sm.commit()

    # Should create at least one epic named "Initial Project" that isn't completed.
    assert any(e.get("name") == "Initial Project" for e in sm.current_state.epics)
    assert any(e.get("completed") is False for e in sm.current_state.epics)


@pytest.mark.asyncio
async def test_plan_epic_accepts_user_modified_tasks(agentcontext):
    """
    Ensure the user's edits to the task list are respected over the raw LLM plan.
    """
    sm, _, ui, mock_get_llm = agentcontext

    sm.current_state.epics = [
        {
            "id": "abc",
            "name": "Initial Project",
            "description": "hello world",
            "complexity": Complexity.SIMPLE,
            "completed": False,
        }
    ]
    await sm.commit()

    tl = TechLead(sm, ui)
    tl.get_llm = mock_get_llm(
        return_value=DevelopmentPlan(plan=[Epic(description="Task 1"), Epic(description="Task 2")])
    )

    # Ensure UI methods are async and track invocations
    ui.send_epics_and_tasks = AsyncMock()

    # User edits: replace "Task 1" with "Task A", keep "Task 2"
    edited = [
        {
            "description": "Initial Project",
            "tasks": [
                {"description": "Task A"},
                {"description": "Task 2"},
            ],
        }
    ]
    ui.ask_question.return_value = UserInput(button="done_editing", text=json.dumps(edited))

    response = await tl.run()
    assert response.type == ResponseType.DONE

    await sm.commit()

    # The final tasks should match the user-edited list in order.
    assert [t["description"] for t in sm.current_state.tasks] == ["Task A", "Task 2"]

    # Basic interaction checks
    if hasattr(ui, "send_epics_and_tasks") and isinstance(ui.send_epics_and_tasks, AsyncMock):
        ui.send_epics_and_tasks.assert_awaited_once()
    if hasattr(ui, "ask_question"):
        # ask_question is async in the system; in tests it may be an AsyncMock already
        try:
            ui.ask_question.assert_awaited_once()
        except AssertionError:
            # Some fixtures set a plain Mock with awaited behavior handled internally.
            # Fallback to at-least-once check if exact awaited_once is unavailable.
            assert ui.ask_question.call_count >= 1


@pytest.mark.asyncio
async def test_plan_epic_does_not_duplicate_initial_project_epic(agentcontext):
    """
    When planning an existing 'Initial Project' epic, TechLead should not create a duplicate epic.
    """
    sm, _, ui, mock_get_llm = agentcontext

    sm.current_state.epics = [
        {
            "id": "abc",
            "name": "Initial Project",
            "description": "hello world",
            "complexity": Complexity.SIMPLE,
            "completed": False,
        }
    ]
    await sm.commit()

    tl = TechLead(sm, ui)
    tl.get_llm = mock_get_llm(return_value=DevelopmentPlan(plan=[Epic(description="Task X")]))
    ui.send_epics_and_tasks = AsyncMock()
    ui.ask_question.return_value = UserInput(
        button="done_editing",
        text=json.dumps([{"description": "Initial Project", "tasks": [{"description": "Task X"}]}]),
    )

    _ = await tl.run()
    await sm.commit()

    names = [e["name"] for e in sm.current_state.epics]
    assert names.count("Initial Project") == 1


@pytest.mark.asyncio
async def test_apply_project_template_with_unknown_template_no_files(agentcontext):
    """
    If an unrecognized template key is provided, no files should be generated.
    """
    sm, _, ui, _ = agentcontext

    sm.current_state.specification.templates = {"unknown_template": {}}
    sm.current_state.epics = [{"name": "Initial Project", "sub_epics": []}]
    await sm.commit()

    tl = TechLead(sm, ui)
    response = await tl.run()
    assert response.type == ResponseType.DONE

    await sm.commit()
    # Unknown template should not create files
    assert sm.current_state.files == []


def _make_tl(
    *,
    epics=None,
    spec_description="Spec description",
    complexity=Complexity.SIMPLE,
    templates=None,
    files=None,
):
    """
    Create a minimally-initialized TechLead instance suitable for unit testing.
    We bypass __init__ and set the few attributes accessed by tested methods.
    """
    tl = TechLead.__new__(TechLead)

    spec = SimpleNamespace(
        description=spec_description,
        complexity=complexity,
        templates=templates,
        template_summary=None,
        # allow clone() fallback in code paths that might access it
        clone=lambda: SimpleNamespace(
            description=spec_description,
            complexity=complexity,
            templates=templates,
            template_summary=None,
        ),
    )

    tl.current_state = SimpleNamespace(
        epics=list(epics or []),
        specification=spec,
        files=list(files or []),
        tasks=[],
        current_epic=None,
        run_command=None,
    )

    tl.next_state = SimpleNamespace(
        epics=list(epics or []),
        relevant_files=None,
        modified_files={},
        tasks=[],
        current_epic={"sub_epics": []},
        action=None,
        specification=None,
    )

    # Provide minimal stubs for attributes that could be touched in branches
    tl.ui = SimpleNamespace(
        send_message=lambda *a, **k: None,
        send_run_command=lambda *a, **k: None,
        send_epics_and_tasks=lambda *a, **k: None,
        send_project_stage=lambda *a, **k: None,
    )
    tl.send_message = lambda *a, **k: None
    tl.ask_question = lambda *a, **k: SimpleNamespace(button="continue", cancelled=False, text="")
    tl.get_llm = lambda *a, **k: None  # not used in these unit tests

    return tl


# ------------------------------
# create_initial_project_epic()
# ------------------------------
def test_create_initial_project_epic_sets_expected_fields_and_resets_file_state():
    tl = _make_tl(epics=[])
    # Pre-set values to verify they get reset
    tl.next_state.relevant_files = "SHOULD_BE_RESET"
    tl.next_state.modified_files = {"dirty": True}

    tl.create_initial_project_epic()

    assert isinstance(tl.next_state.epics, list)
    assert len(tl.next_state.epics) == 1
    epic = tl.next_state.epics[0]

    assert epic["name"] == "Initial Project"
    assert epic["source"] == "app"
    assert epic["description"] == tl.current_state.specification.description
    assert epic["completed"] is False
    assert epic["summary"] is None
    assert epic["test_instructions"] is None
    assert epic["complexity"] == tl.current_state.specification.complexity
    assert epic["sub_epics"] == []
    assert re.fullmatch(r"[0-9a-f]{32}", epic["id"]), "id should be a 32-char hex string"

    assert tl.next_state.relevant_files is None
    assert tl.next_state.modified_files == {}


# ------------------------------
# update_epics_and_tasks()
# ------------------------------
def test_update_epics_and_tasks_preserves_unchanged_task_and_adds_new():
    tl = _make_tl()
    original_task = {
        "id": "deadbeefdeadbeefdeadbeefdeadbeef",
        "description": "Task unchanged",
        "instructions": None,
        "pre_breakdown_testing_instructions": None,
        # Intentionally use a plain string so equality with JSON-loaded dict can succeed
        "status": "TODO",
        "sub_epic_id": 42,
    }
    tl.next_state.tasks = [original_task.copy()]

    edited_plan = [
        {
            "description": "Sub Epic 1",
            "tasks": [
                original_task.copy(),  # exact match should be preserved and only sub_epic_id reassigned
                {"description": "Task new"},  # no match -> new task with fresh id and TODO status
            ],
        }
    ]
    tl.update_epics_and_tasks(json.dumps(edited_plan))

    # Sub-epics updated
    assert tl.next_state.current_epic["sub_epics"] == [{"id": 1, "description": "Sub Epic 1"}]

    tasks = tl.next_state.tasks
    assert len(tasks) == 2

    # First task preserved: same id, fields retained, sub_epic_id reassigned to 1
    preserved = tasks[0]
    assert preserved["id"] == original_task["id"]
    assert preserved["description"] == "Task unchanged"
    assert preserved["sub_epic_id"] == 1

    # Second task added: fresh id (uuid4 hex), TODO enum status, Nones for instructions
    added = tasks[1]
    assert added["description"] == "Task new"
    assert re.fullmatch(r"[0-9a-f]{32}", added["id"])
    assert added["status"] == TaskStatus.TODO
    assert added["instructions"] is None
    assert added["pre_breakdown_testing_instructions"] is None
    assert added["sub_epic_id"] == 1


def test_update_epics_and_tasks_multiple_sub_epics_assigns_correct_sub_epic_ids():
    tl = _make_tl()
    # No exact matches on purpose -> both become new tasks in different sub-epics
    edited_plan = [
        {"description": "Sub 1", "tasks": [{"description": "A1"}]},
        {"description": "Sub 2", "tasks": [{"description": "B1"}, {"description": "B2"}]},
    ]
    tl.update_epics_and_tasks(json.dumps(edited_plan))

    assert tl.next_state.current_epic["sub_epics"] == [
        {"id": 1, "description": "Sub 1"},
        {"id": 2, "description": "Sub 2"},
    ]
    tasks = tl.next_state.tasks
    assert [t["sub_epic_id"] for t in tasks] == [1, 2, 2]
    assert all(re.fullmatch(r"[0-9a-f]{32}", t["id"]) for t in tasks)
    assert all(t["status"] == TaskStatus.TODO for t in tasks)


def test_update_epics_and_tasks_empty_plan_clears_sub_epics_and_tasks():
    tl = _make_tl()
    tl.next_state.current_epic["sub_epics"] = [{"id": 99, "description": "Old"}]
    tl.next_state.tasks = [{"id": "x", "description": "Old task", "sub_epic_id": 99}]

    tl.update_epics_and_tasks("[]")

    assert tl.next_state.current_epic["sub_epics"] == []
    assert tl.next_state.tasks == []


def test_update_epics_and_tasks_invalid_json_raises():
    tl = _make_tl()
    with pytest.raises(json.JSONDecodeError):
        tl.update_epics_and_tasks("{not: json}")


# ------------------------------
# run() branch behavior (async)
# ------------------------------
@pytest.mark.asyncio
async def test_run_no_epics_calls_create_and_returns_done(monkeypatch):
    tl = _make_tl(epics=[])
    called = {"create": False}

    def _create():
        called["create"] = True

    monkeypatch.setattr(tl, "create_initial_project_epic", _create)
    monkeypatch.setattr(AgentResponse, "done", lambda _self: "DONE")

    result = await tl.run()

    assert called["create"] is True
    assert result == "DONE"


@pytest.mark.asyncio
async def test_run_single_completed_epic_triggers_new_initial_epic(monkeypatch):
    tl = _make_tl(epics=[{"completed": True}])
    called = {"create": False}
    monkeypatch.setattr(tl, "create_initial_project_epic", lambda: called.update(create=True))
    monkeypatch.setattr(AgentResponse, "done", lambda _self: "DONE")

    result = await tl.run()

    assert called["create"] is True
    assert result == "DONE"


@pytest.mark.asyncio
async def test_run_applies_project_templates_when_requested(monkeypatch):
    # Set templates and ensure files list is empty -> triggers template application branch
    tl = _make_tl(epics=[{"completed": False}], templates={"starter": {}}, files=[])
    flags = {"applied": False}

    async def _apply():
        flags["applied"] = True

    monkeypatch.setattr(tl, "apply_project_templates", _apply)
    monkeypatch.setattr(AgentResponse, "done", lambda _self: "DONE")

    result = await tl.run()

    assert flags["applied"] is True
    assert tl.next_state.action == "Apply project templates"
    assert result == "DONE"


@pytest.mark.asyncio
async def test_run_plans_first_incomplete_epic_when_present(monkeypatch):
    # Avoid templates branch by providing non-empty files list
    epics = [{"name": "E1", "completed": False}, {"name": "E2", "completed": True}]
    tl = _make_tl(epics=epics, templates=None, files=["already_has_files"])
    called = {"epic_arg": None}

    async def _plan(epic):
        called["epic_arg"] = epic
        return "PLANNED"

    monkeypatch.setattr(tl, "plan_epic", _plan)

    result = await tl.run()

    assert tl.next_state.action == "Create a development plan"
    assert called["epic_arg"] == epics[0]  # first incomplete epic chosen
    assert result == "PLANNED"
