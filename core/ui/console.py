from __future__ import annotations

import inspect
from typing import Optional

from prompt_toolkit.shortcuts import PromptSession

from core.log import get_logger
from core.ui.base import JSONDict, JSONList, UIBase, UIClosedError, UISource, UserInput

log = get_logger(__name__)


class PlainConsoleUI(UIBase):
    """UI adapter for plain (no color) console output."""

    def __init__(self) -> None:
        self._app_link: Optional[str] = None
        self._streaming_logs = False
        self._important_stream_open = False
        self._breakdown_stream_open = False

    # -- helpers -----------------------------------------------------------------

    def _write(self, text: str = "", *, end: str = "\n", flush: bool = False) -> None:
        print(text, end=end, flush=flush)

    def _marker(self, tag: str, detail: Optional[str] = None) -> None:
        line = f"({tag})" if detail is None else f"({tag}) {detail}"
        self._write(line)

    # -- UIBase methods -----------------------------------------------------------

    async def start(self) -> bool:
        log.debug("Console UI started")
        return True

    async def stop(self):
        log.debug("Console UI stopped")

    async def send_stream_chunk(
        self, chunk: Optional[str], *, source: Optional[UISource] = None, project_state_id: Optional[str] = None
    ) -> None:
        if chunk is None:
            # end of stream
            self._write(flush=True)
        else:
            self._write(chunk, end="", flush=True)

    async def send_message(
        self,
        message: str,
        *,
        source: Optional[UISource] = None,
        project_state_id: Optional[str] = None,
        extra_info: Optional[str] = None,
    ):
        if source:
            self._write(f"[{source}] {message}")
        else:
            self._write(message)

    async def send_key_expired(self, message: Optional[str] = None):
        if message:
            await self.send_message(message)

    async def send_app_finished(
        self,
        app_id: Optional[str] = None,
        app_name: Optional[str] = None,
        folder_name: Optional[str] = None,
    ):
        self._marker("app-finished", f"{app_id or ''} {app_name or ''} {folder_name or ''}".strip())

    async def send_feature_finished(
        self,
        app_id: Optional[str] = None,
        app_name: Optional[str] = None,
        folder_name: Optional[str] = None,
    ):
        self._marker("feature-finished", f"{app_id or ''} {app_name or ''} {folder_name or ''}".strip())

    def _print_question(
        self,
        question: str,
        hint: Optional[str],
        buttons: Optional[dict[str, str]],
        default: Optional[str],
        source: Optional[UISource],
    ) -> None:
        if source:
            self._write(f"[{source}] {question}")
        else:
            self._write(question)
        if hint:
            self._write(f"Hint: {hint}")
        if buttons:
            for k, v in buttons.items():
                default_str = " (default)" if k == default else ""
                self._write(f"  [{k}]: {v}{default_str}")

    async def ask_question(
        self,
        question: str,
        *,
        buttons: Optional[dict[str, str]] = None,
        default: Optional[str] = None,
        buttons_only: bool = False,
        allow_empty: bool = False,
        full_screen: Optional[bool] = False,
        hint: Optional[str] = None,
        verbose: bool = True,
        initial_text: Optional[str] = None,
        source: Optional[UISource] = None,
        project_state_id: Optional[str] = None,
        extra_info: Optional[str] = None,
        placeholder: Optional[str] = None,
    ) -> UserInput:
        """Prompt user with a question and return their response.

        Args:
            question: The question text to display.
            buttons: Optional mapping of button keys to descriptions.
            default: Default button key or text if user submits empty input.
            buttons_only: If True, only button choices are allowed.
            allow_empty: Allow empty text responses.
            full_screen: Unused placeholder for UI compatibility.
            hint: Optional helper text displayed under the question.
            verbose: If False, suppress printing of question, hint, and buttons.
            initial_text: Pre-populated text in the prompt.
            source: Optional source of the question printed in brackets.
            project_state_id: Unused project state identifier.
            extra_info: Additional info not used by this UI.
            placeholder: Placeholder text shown in the prompt input field.
        """
        if verbose:
            self._print_question(question, hint, buttons, default, source)

        session: PromptSession[str] = PromptSession("> ")

        prompt_kwargs: dict[str, object] = {"default": initial_text or ""}
        try:
            sig = inspect.signature(session.prompt_async)
        except (ValueError, TypeError):
            sig = None
        if sig and "placeholder" in sig.parameters:
            prompt_kwargs["placeholder"] = placeholder

        while True:
            try:
                text = await session.prompt_async(**prompt_kwargs)
            except (KeyboardInterrupt, EOFError):
                raise UIClosedError()

            text = text.strip()
            if buttons:
                if text in buttons:
                    return UserInput(button=text, text=None)
                if buttons_only:
                    if verbose:
                        self._write("Please choose one of available options")
                    continue

            if not text and not allow_empty:
                if default is not None:
                    text = default
                else:
                    if verbose:
                        self._write("Input required. Try again.")
                    continue

            return UserInput(button=None, text=text)

    async def send_project_stage(self, data: JSONDict) -> None:
        self._marker("project-stage", str(data))

    async def send_epics_and_tasks(
        self,
        epics: JSONList | None = None,
        tasks: JSONList | None = None,
    ) -> None:
        self._marker("epics-tasks", f"epics={epics} tasks={tasks}")

    async def send_task_progress(
        self,
        index: int,
        n_tasks: int,
        description: str,
        source: str,
        status: str,
        source_index: int = 1,
        tasks: JSONList | None = None,
    ) -> None:
        self._marker(
            "task-progress",
            f"{index}/{n_tasks} {description} [{status}] from {source}",
        )

    async def send_step_progress(
        self,
        index: int,
        n_steps: int,
        step: JSONDict,
        task_source: str,
    ) -> None:
        self._marker("step-progress", f"{index}/{n_steps} {step} from {task_source}")

    async def send_modified_files(
        self,
        modified_files: JSONList,
    ) -> None:
        self._marker("modified-files")
        for f in modified_files:
            self._write(f"  - {f}")

    async def send_data_about_logs(
        self,
        data_about_logs: JSONDict,
    ) -> None:
        self._marker("logs", str(data_about_logs))

    async def get_debugging_logs(self) -> tuple[str, str]:
        return "", ""

    async def send_run_command(self, run_command: str):
        self._marker("run-command", run_command)

    async def send_app_link(self, app_link: str):
        self._app_link = app_link
        self._marker("app-link", app_link)

    async def open_editor(self, file: str, line: Optional[int] = None):
        self._marker("open-editor", f"{file}:{line if line is not None else ''}")

    async def send_project_root(self, path: str):
        self._marker("project-root", path)

    async def send_project_stats(self, stats: JSONDict):
        self._marker("project-stats", str(stats))

    async def send_test_instructions(self, test_instructions: str, project_state_id: Optional[str] = None):
        self._marker("test-instructions", test_instructions)

    async def knowledge_base_update(self, knowledge_base: JSONDict):
        self._marker("knowledge-base", str(knowledge_base))

    async def send_file_status(self, file_path: str, file_status: str, source: Optional[UISource] = None):
        if source:
            self._marker("file-status", f"{file_path}: {file_status} [{source}]")
        else:
            self._marker("file-status", f"{file_path}: {file_status}")

    async def send_bug_hunter_status(self, status: str, num_cycles: int):
        self._marker("bug-hunter", f"{status} cycles={num_cycles}")

    async def generate_diff(
        self,
        file_path: str,
        file_old: str,
        file_new: str,
        n_new_lines: int = 0,
        n_del_lines: int = 0,
        source: Optional[UISource] = None,
    ):
        self._marker("diff-open", file_path)

    async def stop_app(self):
        self._marker("stop-app")

    async def close_diff(self):
        self._marker("diff-close")

    async def loading_finished(self):
        self._marker("loading-finished")

    async def send_project_description(self, description: str):
        self._marker("project-description", description)

    async def send_features_list(self, features: list[str]):
        self._marker("features-list")
        for f in features:
            self._write(f"  - {f}")

    async def import_project(self, project_dir: str):
        self._marker("import-project", project_dir)

    async def start_important_stream(self):
        self._important_stream_open = True
        self._marker("stream-important:start")

    async def start_breakdown_stream(self):
        self._breakdown_stream_open = True
        self._marker("stream-breakdown:start")


__all__ = ["PlainConsoleUI"]
