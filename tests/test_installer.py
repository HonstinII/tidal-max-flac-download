from app.installer import InstallJobManager, build_install_commands, build_install_plan


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

    assert commands == [["brew", "install", "ffmpeg", "flac"]]


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


def test_macos_install_plan_uses_homebrew_for_audio_tools():
    plan = build_install_plan(
        environment(
            "Darwin",
            {"streamrip": False, "ffmpeg": False, "metaflac": False},
            homebrew=True,
        )
    )

    assert [step.tool for step in plan.steps] == ["streamrip", "ffmpeg", "metaflac"]
    assert ["brew", "install", "ffmpeg"] in plan.commands
    assert ["brew", "install", "flac"] in plan.commands


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
