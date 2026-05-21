import zipfile

from app.installer import (
    InstallJobManager,
    build_install_commands,
    build_install_plan,
    extract_bundled_flac,
)


def environment(system, tools, homebrew=False, winget=False):
    return {
        "platform": {"system": system, "name": system, "supports_auto_install": True},
        "tools": {
            "streamrip": {"ok": tools.get("streamrip", False)},
            "ffmpeg": {"ok": tools.get("ffmpeg", False)},
            "metaflac": {"ok": tools.get("metaflac", False)},
        },
        "package_managers": {
            "homebrew": {"ok": homebrew, "path": "/opt/homebrew/bin/brew" if homebrew else None},
            "winget": {"ok": winget, "path": "C:/Windows/System32/winget.exe" if winget else None},
        },
        "manual_commands": {
            "homebrew": "install homebrew",
            "streamrip": "python -m pip install --user streamrip",
            "ffmpeg": "install ffmpeg",
            "metaflac": "install flac",
        },
    }


def test_build_install_commands_installs_missing_homebrew_tools():
    commands = build_install_commands(
        {"streamrip": True, "ffmpeg": False, "metaflac": False},
        platform_name="Darwin",
    )

    assert commands == [["brew", "install", "ffmpeg"]]


def test_build_install_commands_installs_streamrip_with_python():
    commands = build_install_commands(
        {"streamrip": False, "ffmpeg": True, "metaflac": True},
        platform_name="Darwin",
    )

    assert commands == [["python3", "-m", "pip", "install", "--user", "streamrip"]]


def test_install_job_manager_records_successful_command():
    calls = []

    def runner(command, on_line):
        calls.append(command)
        on_line("installed")
        return 0

    manager = InstallJobManager(runner=runner, platform_name="Darwin")
    job = manager.create_job({"streamrip": True, "ffmpeg": False, "metaflac": True})
    manager.run_job(job.job_id)

    assert calls == [["brew", "install", "ffmpeg"]]
    assert job.status == "complete"
    assert job.events[-1]["stage"] == "complete"
    assert any(event["stage"] == "step_started" for event in job.events)
    assert any(event["stage"] == "step_complete" for event in job.events)


def test_macos_install_plan_uses_homebrew_for_audio_tools():
    plan = build_install_plan(
        environment(
            "Darwin",
            {"streamrip": False, "ffmpeg": False, "metaflac": False},
            homebrew=True,
        )
    )

    assert [step.tool for step in plan.steps] == ["streamrip", "ffmpeg"]
    assert ["brew", "install", "ffmpeg"] in plan.commands


def test_macos_install_plan_without_homebrew_returns_manual_guide():
    plan = build_install_plan(
        environment(
            "Darwin",
            {"streamrip": True, "ffmpeg": False, "metaflac": False},
            homebrew=False,
        )
    )

    assert [step.tool for step in plan.steps] == []
    assert plan.manual_guides[0].tool == "homebrew"
    assert plan.manual_guides[0].manual_command == "install homebrew"


def test_macos_missing_only_metaflac_does_not_block_core_install():
    plan = build_install_plan(
        environment(
            "Darwin",
            {"streamrip": True, "ffmpeg": True, "metaflac": False},
            homebrew=True,
        )
    )

    assert plan.steps == []
    assert plan.manual_guides == []


def test_windows_install_plan_uses_winget_for_ffmpeg():
    plan = build_install_plan(
        environment(
            "Windows",
            {"streamrip": False, "ffmpeg": False, "metaflac": True},
            winget=True,
        )
    )

    assert [step.tool for step in plan.steps] == ["streamrip", "ffmpeg"]
    assert plan.steps[1].command[:4] == ["winget", "install", "--id", "Gyan.FFmpeg"]


def test_windows_install_plan_without_winget_returns_manual_ffmpeg_guide():
    plan = build_install_plan(
        environment(
            "Windows",
            {"streamrip": True, "ffmpeg": False, "metaflac": True},
            winget=False,
        )
    )

    assert plan.steps == []
    assert plan.manual_guides[0].tool == "ffmpeg"


def test_windows_missing_metaflac_offers_bundled_flac_option():
    plan = build_install_plan(
        environment(
            "Windows",
            {"streamrip": True, "ffmpeg": True, "metaflac": False},
            winget=True,
        )
    )

    assert plan.bundled_options[0].tool == "metaflac"
    assert plan.bundled_options[0].kind == "bundled_flac"


def test_extract_bundled_flac_extracts_zip(tmp_path):
    zip_path = tmp_path / "flac.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("flac-1.5.0-win/Win64/metaflac.exe", "fake")
        archive.writestr("flac-1.5.0-win/Win64/flac.exe", "flac")
    target = tmp_path / "tools"

    result = extract_bundled_flac(zip_path=zip_path, target_dir=target)

    assert result["ok"] is True
    assert (target / "metaflac.exe").read_text() == "fake"
    assert (target / "flac.exe").read_text() == "flac"


def test_extract_bundled_flac_missing_zip_returns_guide(tmp_path):
    result = extract_bundled_flac(zip_path=tmp_path / "missing.zip", target_dir=tmp_path / "tools")

    assert result["ok"] is False
    assert "not included" in result["message"]


def test_install_job_manager_records_failed_step_command():
    def runner(command, on_line):
        return 2

    manager = InstallJobManager(runner=runner, platform_name="Darwin")
    job = manager.create_job({"streamrip": True, "ffmpeg": False, "metaflac": True})
    manager.run_job(job.job_id)

    failed = [event for event in job.events if event["stage"] == "step_failed"][0]
    assert failed["copy_command"] == "brew install ffmpeg"
