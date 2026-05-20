from __future__ import annotations

from dataclasses import dataclass, field
import json
import platform
import queue
import subprocess
import threading
import uuid
from typing import Callable


InstallRunner = Callable[[list[str], Callable[[str], None]], int]


@dataclass
class InstallJob:
    job_id: str
    commands: list[list[str]]
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
    if not tools.get("metaflac", False):
        brew_packages.append("flac")
    if brew_packages:
        commands.append(["brew", "install", *brew_packages])
    if not tools.get("streamrip", False):
        commands.append(["python3", "-m", "pip", "install", "--user", "streamrip"])
    return commands


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
        commands = build_install_commands(tools, self.platform_name)
        job = InstallJob(job_id=str(uuid.uuid4()), commands=commands)
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
            job.add_event({"stage": "failed", "message": "No installer is available for this platform."})
            job.queue.put(None)
            return

        job.status = "running"
        job.add_event({"stage": "started", "message": "Installing missing tools."})
        for command in job.commands:
            job.add_event({"stage": "command", "message": " ".join(command)})
            return_code = self.runner(
                command,
                lambda line: job.add_event({"stage": "log", "message": line}),
            )
            if return_code != 0:
                job.status = "failed"
                job.add_event({"stage": "failed", "message": f"Installer exited with {return_code}."})
                job.queue.put(None)
                return

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
