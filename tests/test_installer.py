from app.installer import InstallJobManager, build_install_commands


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
