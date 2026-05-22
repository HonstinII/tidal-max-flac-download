from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
import platform
import queue
import shutil
import subprocess
import sys
import threading
import uuid
import zipfile
from pathlib import Path
from typing import Callable

from .environment import EnvironmentInfo
from .environment import detect_environment
from .environment import managed_tools_dir
from .environment import prime_runtime_path


InstallRunner = Callable[[list[str], Callable[[str], None]], int]


@dataclass
class InstallStep:
    tool: str
    label: str
    command: list[str] | None
    required: bool
    manual_command: str | None = None
    manual_url: str | None = None
    kind: str = "command"


@dataclass
class InstallPlan:
    steps: list[InstallStep]
    manual_guides: list[InstallStep] = field(default_factory=list)
    bundled_options: list[InstallStep] = field(default_factory=list)

    @property
    def commands(self) -> list[list[str]]:
        return [step.command for step in self.steps if step.command]


@dataclass
class InstallJob:
    job_id: str
    commands: list[list[str]]
    steps: list[InstallStep] = field(default_factory=list)
    status: str = "queued"
    events: list[dict] = field(default_factory=list)
    queue: queue.Queue[dict | None] = field(default_factory=queue.Queue)

    def add_event(self, event: dict) -> None:
        self.events.append(event)
        self.queue.put(event)


def build_install_commands(tools: dict[str, bool], platform_name: str | None = None) -> list[list[str]]:
    platform_name = platform_name or platform.system()
    if platform_name != "Darwin":
        return []

    commands: list[list[str]] = []
    brew_packages = []
    if not tools.get("ffmpeg", False):
        brew_packages.append("ffmpeg")
    if brew_packages:
        commands.append(["brew", "install", *brew_packages])
    if not tools.get("streamrip", False):
        commands.append(["python3", "-m", "pip", "install", "--user", "streamrip"])
    return commands


def build_install_plan(environment: EnvironmentInfo | dict) -> InstallPlan:
    if isinstance(environment, EnvironmentInfo):
        env = environment.to_dict()
    else:
        env = environment

    system = env["platform"]["system"]
    tools = env["tools"]
    managers = env.get("package_managers", {})
    commands = env.get("manual_commands", {})
    urls = env.get("manual_urls", {})
    steps: list[InstallStep] = []
    manual_guides: list[InstallStep] = []
    bundled_options: list[InstallStep] = []

    def missing(tool: str) -> bool:
        info = tools[tool]
        return not (info["ok"] if isinstance(info, dict) else info.ok)

    if system == "Darwin":
        homebrew_ok = managers.get("homebrew", {}).get("ok", False)
        if not homebrew_ok and missing("ffmpeg"):
            manual_guides.append(
                InstallStep(
                    tool="homebrew",
                    label="Install Homebrew",
                    command=None,
                    required=True,
                    manual_command=commands.get("homebrew"),
                    manual_url=urls.get("homebrew"),
                    kind="manual",
                )
            )
        if missing("streamrip"):
            steps.append(
                InstallStep(
                    tool="streamrip",
                    label="Install streamrip",
                    command=["python3", "-m", "pip", "install", "--user", "streamrip"],
                    required=True,
                    manual_command=commands.get("streamrip"),
                    manual_url=urls.get("streamrip"),
                )
            )
        if homebrew_ok and missing("ffmpeg"):
            steps.append(
                InstallStep(
                    tool="ffmpeg",
                    label="Install ffmpeg",
                    command=["brew", "install", "ffmpeg"],
                    required=True,
                    manual_command=commands.get("ffmpeg"),
                    manual_url=urls.get("ffmpeg"),
                )
            )
    elif system == "Windows":
        if missing("streamrip"):
            steps.append(
                InstallStep(
                    tool="streamrip",
                    label="Install streamrip",
                    command=["python", "-m", "pip", "install", "--user", "streamrip"],
                    required=True,
                    manual_command=commands.get("streamrip"),
                    manual_url=urls.get("streamrip"),
                )
            )
        winget_ok = managers.get("winget", {}).get("ok", False)
        if missing("ffmpeg") and winget_ok:
            steps.append(
                InstallStep(
                    tool="ffmpeg",
                    label="Install ffmpeg",
                    command=[
                        "winget",
                        "install",
                        "--id",
                        "Gyan.FFmpeg",
                        "-e",
                        "--accept-package-agreements",
                        "--accept-source-agreements",
                    ],
                    required=True,
                    manual_command=commands.get("ffmpeg"),
                    manual_url=urls.get("ffmpeg"),
                )
            )
        elif missing("ffmpeg"):
            manual_guides.append(
                InstallStep(
                    tool="ffmpeg",
                    label="Install ffmpeg manually",
                    command=None,
                    required=True,
                    manual_command=commands.get("ffmpeg"),
                    manual_url=urls.get("ffmpeg"),
                    kind="manual",
                )
            )
        if missing("metaflac"):
            bundled_options.append(
                InstallStep(
                    tool="metaflac",
                    label="Use bundled FLAC tools",
                    command=None,
                    required=False,
                    manual_command=commands.get("metaflac"),
                    manual_url=urls.get("metaflac"),
                    kind="bundled_flac",
                )
            )
    return InstallPlan(steps=steps, manual_guides=manual_guides, bundled_options=bundled_options)


def subprocess_runner(command: list[str], on_line: Callable[[str], None]) -> int:
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert process.stdout is not None
    for line in process.stdout:
        on_line(line.rstrip())
    return process.wait()


def bundled_resource_path(relative_path: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    candidate = base / relative_path
    if candidate.exists():
        return candidate
    return Path(__file__).resolve().parent / relative_path


BUNDLED_FLAC_ZIP = bundled_resource_path("tools/windows/flac.zip")


def extract_bundled_flac(
    zip_path: Path | None = None,
    target_dir: Path | None = None,
) -> dict:
    zip_path = zip_path or BUNDLED_FLAC_ZIP
    target_dir = target_dir or managed_tools_dir("Windows") / "flac"
    if not zip_path.exists():
        return {
            "ok": False,
            "message": "Bundled FLAC tools are not included in this build.",
            "target": str(target_dir),
            "manual_url": "https://xiph.org/flac/download.html",
        }
    target_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(target_dir)
    preferred_dirs = [target_dir / "flac-1.5.0-win" / "Win64", target_dir / "Win64"]
    for source_dir in preferred_dirs:
        if (source_dir / "metaflac.exe").exists():
            for filename in ("metaflac.exe", "flac.exe", "libFLAC.dll", "libFLAC++.dll"):
                source = source_dir / filename
                if source.exists():
                    shutil.copy2(source, target_dir / filename)
            break
    _prepend_path(target_dir)
    prime_runtime_path("Windows")
    return {"ok": True, "message": "Bundled FLAC tools extracted.", "target": str(target_dir)}


def _prepend_path(path: Path) -> None:
    value = str(path)
    paths = [item for item in os.environ.get("PATH", "").split(os.pathsep) if item]
    if value not in paths:
        os.environ["PATH"] = os.pathsep.join([value, *paths])


class InstallJobManager:
    def __init__(
        self,
        runner: InstallRunner = subprocess_runner,
        platform_name: str | None = None,
    ):
        self.runner = runner
        self.platform_name = platform_name
        self.jobs: dict[str, InstallJob] = {}

    def create_job(self, tools: dict[str, bool]) -> InstallJob:
        if {"platform", "tools"}.issubset(tools.keys()):
            plan = build_install_plan(tools)
            commands = plan.commands
            steps = [*plan.steps, *plan.manual_guides]
        else:
            commands = build_install_commands(tools, self.platform_name)
            steps = [
                InstallStep(
                    tool=command[-1] if command[:2] != ["brew", "install"] else "tools",
                    label=" ".join(command),
                    command=command,
                    required=True,
                    manual_command=" ".join(command),
                    manual_url=None,
                )
                for command in commands
            ]
        job = InstallJob(job_id=str(uuid.uuid4()), commands=commands, steps=steps)
        self.jobs[job.job_id] = job
        return job

    def get_job(self, job_id: str) -> InstallJob | None:
        return self.jobs.get(job_id)

    def start_job(self, job_id: str) -> None:
        thread = threading.Thread(target=self.run_job, args=(job_id,), daemon=True)
        thread.start()

    def run_job(self, job_id: str) -> None:
        job = self.jobs[job_id]
        if not job.commands:
            job.status = "failed"
            if job.steps:
                for step in job.steps:
                    job.add_event(
                        {
                            "stage": "manual_guide",
                            "tool": step.tool,
                            "label": step.label,
                            "manual_command": step.manual_command,
                            "copy_command": step.manual_command,
                            "manual_url": step.manual_url,
                            "message": step.label,
                        }
                    )
            job.add_event(
                {
                    "stage": "failed",
                    "message": "No automatic installer is available. Use the manual guide, then recheck.",
                }
            )
            job.queue.put(None)
            return

        job.status = "running"
        job.add_event({"stage": "started", "message": "Installing missing tools."})
        for index, command in enumerate(job.commands):
            step = job.steps[index] if index < len(job.steps) else None
            label = step.label if step else " ".join(command)
            command_text = " ".join(command)
            job.add_event(
                {
                    "stage": "step_started",
                    "tool": step.tool if step else None,
                    "label": label,
                    "command": command_text,
                    "copy_command": command_text,
                    "manual_command": step.manual_command if step else command_text,
                    "manual_url": step.manual_url if step else None,
                    "message": label,
                }
            )
            return_code = self.runner(
                command,
                lambda line: job.add_event({"stage": "log", "message": line}),
            )
            if return_code != 0:
                job.status = "failed"
                job.add_event(
                    {
                        "stage": "step_failed",
                        "tool": step.tool if step else None,
                        "label": label,
                        "command": command_text,
                        "copy_command": command_text,
                        "manual_command": step.manual_command if step else command_text,
                        "manual_url": step.manual_url if step else None,
                        "message": f"{label} exited with {return_code}.",
                    }
                )
                job.add_event({"stage": "failed", "message": f"Installer exited with {return_code}."})
                job.queue.put(None)
                return
            job.add_event(
                {
                    "stage": "step_complete",
                    "tool": step.tool if step else None,
                    "label": label,
                    "command": command_text,
                    "copy_command": command_text,
                    "manual_command": step.manual_command if step else command_text,
                    "manual_url": step.manual_url if step else None,
                    "message": f"{label} complete.",
                }
            )

        job.status = "complete"
        job.add_event({"stage": "complete", "message": "Missing tools installed."})
        job.queue.put(None)

    def events(self, job_id: str):
        job = self.jobs.get(job_id)
        if job is None:
            yield "data: " + json.dumps({"stage": "failed", "message": "Install job not found."}) + "\n\n"
            return
        for event in job.events:
            yield "data: " + json.dumps(event) + "\n\n"
        while True:
            event = job.queue.get()
            if event is None:
                return
            yield "data: " + json.dumps(event) + "\n\n"
