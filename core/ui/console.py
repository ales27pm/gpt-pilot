from __future__ import annotations

import inspect
from typing import Optional

from prompt_toolkit.shortcuts import PromptSession

from core.log import get_logger
from core.ui.base import JSONDict, JSONList, UIBase, UIClosedError, UISource, UserInput

log = get_logger(__name__)


class PlainConsoleUI(UIBase):
    """
    UI adapter for plain (no color) console output.
    """

    async def start(self) -> bool:
        log.debug("Console UI started")
        self._app_link: Optional[str] = None
        self._streaming_logs = False
        self._important_stream_open = False
        self._breakdown_stream_open = False
        return True

    async def stop(self):
        log.debug("Console UI stopped")

    async def send_stream_chunk(
        self, chunk: Optional[str], *, source: Optional[UISource] = None, project_state_id: Optional[str] = None
    ):
        if chunk is None:
            # end of stream
            print("", flush=True)
        else:
            print(chunk, end="", flush=True)

    async def send_message(
        self,
        message: str,
        *,
        source: Optional[UISource] = None,
        project_state_id: Optional[str] = None,
        extra_info: Optional[str] = None,
    ):
        if source:
            print(f"[{source}] {message}")
        else:
            print(message)

    async def send_key_expired(self, message: Optional[str] = None):
        if message:
            await self.send_message(message)

    async def send_app_finished(
        self,
        app_id: Optional[str] = None,
        app_name: Optional[str] = None,
        folder_name: Optional[str] = None,
    ):
        print(f"(app-finished) {app_id or ''} {app_name or ''} {folder_name or ''}")

    async def send_feature_finished(
        self,
        app_id: Optional[str] = None,
        app_name: Optional[str] = None,
        folder_name: Optional[str] = None,
    ):
        print(f"(feature-finished) {app_id or ''} {app_name or ''} {folder_name or ''}")

    def _print_question(
        self,
        question: str,
        hint: Optional[str],
        buttons: Optional[dict[str, str]],
        default: Optional[str],
        source: Optional[UISource],
    ) -> None:
        if source:
            print(f"[{source}] {question}")
        else:
            print(question)
        if hint:
            print(f"Hint: {hint}")
        if buttons:
            for k, v in buttons.items():
                default_str = " (default)" if k == default else ""
                print(f"  [{k}]: {v}{default_str}")

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
                        print("Please choose one of available options")
                    continue

            if not text and not allow_empty:
                if default is not None:
                    text = default
                else:
                    if verbose:
                        print("Input required. Try again.")
                    continue

            return UserInput(button=None, text=text)

    async def send_project_stage(self, data: JSONDict) -> None:
        print(f"(project-stage) {data}")

    async def send_epics_and_tasks(
        self,
        epics: JSONList | None = None,
        tasks: JSONList | None = None,
    ) -> None:
        print(f"(epics-tasks) epics={epics} tasks={tasks}")

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
        print(
            f"(task-progress) {index}/{n_tasks} {description} [{status}] from {source}"
        )

    async def send_step_progress(
        self,
        index: int,
        n_steps: int,
        step: JSONDict,
        task_source: str,
    ) -> None:
        print(f"(step-progress) {index}/{n_steps} {step} from {task_source}")

    async def send_modified_files(
        self,
        modified_files: JSONList,
    ) -> None:
        print("(modified-files)")
        for f in modified_files:
            print(f"  - {f}")

    async def send_data_about_logs(
        self,
        data_about_logs: JSONDict,
    ) -> None:
        print(f"(logs) {data_about_logs}")

    async def get_debugging_logs(self) -> tuple[str, str]:
        return "", ""

    async def send_run_command(self, run_command: str):
        print(f"(run-command) {run_command}")

    async def send_app_link(self, app_link: str):
        self._app_link = app_link
        print(f"(app-link) {app_link}")

    async def open_editor(self, file: str, line: Optional[int] = None):
        print(f"(open-editor) {file}:{line if line is not None else ''}")

    async def send_project_root(self, path: str):
        print(f"(project-root) {path}")

    async def send_project_stats(self, stats: JSONDict):
        print(f"(project-stats) {stats}")

    async def send_test_instructions(self, test_instructions: str, project_state_id: Optional[str] = None):
        print(f"(test-instructions) {test_instructions}")

    async def knowledge_base_update(self, knowledge_base: JSONDict):
        print(f"(knowledge-base) {knowledge_base}")

    async def send_file_status(self, file_path: str, file_status: str, source: Optional[UISource] = None):
        if source:
            print(f"(file-status) {file_path}: {file_status} [{source}]")
        else:
            print(f"(file-status) {file_path}: {file_status}")

    async def send_bug_hunter_status(self, status: str, num_cycles: int):
        print(f"(bug-hunter) {status} cycles={num_cycles}")

    async def generate_diff(
        self,
        file_path: str,
        file_old: str,
        file_new: str,
        n_new_lines: int = 0,
        n_del_lines: int = 0,
        source: Optional[UISource] = None,
    ):
        print(f"(diff-open) {file_path}")

    async def stop_app(self):
        print("(stop-app)")

    async def close_diff(self):
        print("(diff-close)")

    async def loading_finished(self):
        print("(loading-finished)")

    async def send_project_description(self, description: str):
        print(f"(project-description) {description}")

    async def send_features_list(self, features: list[str]):
        print("(features-list)")
        for f in features:
            print(f"  - {f}")

    async def import_project(self, project_dir: str):
        print(f"(import-project) {project_dir}")

    async def start_important_stream(self):
        self._important_stream_open = True
        print("(stream-important:start)")

    async def start_breakdown_stream(self):
        self._breakdown_stream_open = True
        print("(stream-breakdown:start)")


__all__ = ["PlainConsoleUI"]
