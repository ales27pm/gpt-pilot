from __future__ import annotations

from typing import Optional

from core.log import get_logger
from core.ui.base import JSONDict, JSONList, UIBase, UISource, UserInput

log = get_logger(__name__)


class VirtualUI(UIBase):
    """
    Testing UI adapter.
    """

    def __init__(self, inputs: list[dict[str, str]]):
        self.virtual_inputs = [UserInput(**input) for input in inputs]
        self._app_link: Optional[str] = None
        self._important_stream_open = False
        self._breakdown_stream_open = False

    async def start(self) -> bool:
        log.debug("Starting test UI")
        return True

    async def stop(self):
        log.debug("Stopping test UI")

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
            print(f"(key-expired) {message}")

    async def send_app_finished(
        self,
        app_id: Optional[str] = None,
        app_name: Optional[str] = None,
        folder_name: Optional[str] = None,
    ):
        print(f"(app-finished) {app_id or ''} {app_name or ''} {folder_name or ''}".strip())

    async def send_feature_finished(
        self,
        app_id: Optional[str] = None,
        app_name: Optional[str] = None,
        folder_name: Optional[str] = None,
    ):
        print(f"(feature-finished) {app_id or ''} {app_name or ''} {folder_name or ''}".strip())

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
        if source:
            print(f"[{source}] {question}")
        else:
            print(f"{question}")

        if self.virtual_inputs:
            ret = self.virtual_inputs[0]
            self.virtual_inputs = self.virtual_inputs[1:]
            return ret

        if "continue" in buttons:
            return UserInput(button="continue", text=None)
        elif default:
            if buttons:
                return UserInput(button=default, text=None)
            else:
                return UserInput(text=default)
        elif buttons_only:
            return UserInput(button=list(buttons.keys())[0])
        else:
            return UserInput(text="")

    async def send_project_stage(self, data: JSONDict) -> None:
        print(f"(project-stage) {data}")

    async def send_epics_and_tasks(
        self,
        epics: JSONList | None = None,
        tasks: JSONList | None = None,
    ) -> None:
        print("(epics-and-tasks)")
        if epics:
            print(f"  epics={epics}")
        if tasks:
            print(f"  tasks={tasks}")

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
            f"(task-progress) {index}/{n_tasks} {description}"
            f" source={source} status={status}"
        )

    async def send_step_progress(
        self,
        index: int,
        n_steps: int,
        step: JSONDict,
        task_source: str,
    ) -> None:
        print(f"(step-progress) {index}/{n_steps} {step} source={task_source}")

    async def send_data_about_logs(
        self,
        data_about_logs: JSONDict,
    ) -> None:
        print(f"(logs) {data_about_logs}")

    async def get_debugging_logs(self) -> tuple[str, str]:
        return "", ""

    async def send_modified_files(
        self,
        modified_files: JSONList,
    ) -> None:
        print(f"(modified-files) {modified_files}")

    async def send_run_command(self, run_command: str):
        print(f"(run) {run_command}")

    async def send_app_link(self, app_link: str):
        self._app_link = app_link
        print(f"(app-link) {app_link}")

    async def open_editor(self, file: str, line: Optional[int] = None):
        print(f"(open-editor) {file}:{line if line is not None else ''}")

    async def send_project_root(self, path: str):
        print(f"(project-root) {path}")

    async def start_important_stream(self):
        self._important_stream_open = True
        print("(stream-important:start)")

    async def start_breakdown_stream(self):
        self._breakdown_stream_open = True
        print("(stream-breakdown:start)")

    async def send_project_stats(self, stats: JSONDict) -> None:
        print(f"(project-stats) {stats}")

    async def send_test_instructions(self, test_instructions: str, project_state_id: Optional[str] = None):
        print(f"(test-instructions) {test_instructions}")

    async def knowledge_base_update(self, knowledge_base: JSONDict) -> None:
        print(f"(kb-update) {knowledge_base}")

    async def send_file_status(self, file_path: str, file_status: str, source: Optional[UISource] = None) -> None:
        print(f"(file-status) {file_status} {file_path}")

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
        print("(app-stop)")

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


__all__ = ["VirtualUI"]
