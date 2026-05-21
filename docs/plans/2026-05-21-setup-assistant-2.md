# Setup Assistant 2.0 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a safer, clearer first-run installer for macOS and Windows, including Windows bundled FLAC tools for metaflac.

**Architecture:** Add an environment layer that detects platform, package managers, system tools, and app-managed tools. Extend the installer to produce platform-specific install plans and stream readable step events. Update setup UI to show platform-aware cards, progress, manual recovery commands, and the Windows bundled FLAC option.

**Tech Stack:** Python 3, FastAPI, PyInstaller, static HTML/CSS/JS, pytest, zipfile, pathlib, subprocess.

---

### Task 1: Add Environment Detection Model

**Files:**
- Create: `app/environment.py`
- Modify: `app/config.py`
- Test: `tests/test_environment.py`

**Step 1: Write failing tests**

Create tests for:

- macOS Homebrew path detection using `/opt/homebrew/bin`.
- Windows app-managed tool path detection.
- Runtime search path includes app-managed tools and Homebrew paths.
- Backward-compatible `tool_status()` still returns booleans.

**Step 2: Run tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_environment.py tests/test_config.py -v
```

Expected: new tests fail because `app.environment` does not exist.

**Step 3: Implement environment layer**

Implement:

- `PlatformInfo`
- `ToolInfo`
- `PackageManagerInfo`
- `app_data_dir()`
- `managed_tools_dir()`
- `candidate_tool_paths()`
- `find_tool(name)`
- `detect_environment()`
- `prime_runtime_path()`

Keep `app.config.tool_status()` as a wrapper that returns booleans from `detect_environment()`.

**Step 4: Run tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_environment.py tests/test_config.py -v
```

Expected: pass.

**Step 5: Commit**

```bash
git add app/environment.py app/config.py tests/test_environment.py
git commit -m "feat: add platform environment detection"
```

### Task 2: Return Rich Setup Status

**Files:**
- Modify: `app/config.py`
- Modify: `app/main.py` if needed
- Test: `tests/test_config.py`

**Step 1: Write failing tests**

Assert `setup_status()` includes:

- `platform`
- `tools_detail`
- `package_managers`
- `manual_commands`

Also assert existing `tools` boolean map still exists.

**Step 2: Run tests**

```bash
.venv/bin/python -m pytest tests/test_config.py -v
```

Expected: fail on missing keys.

**Step 3: Implement status shape**

Update `setup_status()` to merge rich environment data while keeping:

```json
"tools": {"streamrip": true, "ffmpeg": true, "metaflac": true}
```

**Step 4: Run tests**

```bash
.venv/bin/python -m pytest tests/test_config.py -v
```

Expected: pass.

**Step 5: Commit**

```bash
git add app/config.py tests/test_config.py
git commit -m "feat: expose rich setup status"
```

### Task 3: Build Platform-Specific Install Plans

**Files:**
- Modify: `app/installer.py`
- Test: `tests/test_installer.py`

**Step 1: Write failing tests**

Add tests for:

- macOS with Homebrew creates streamrip, ffmpeg, and flac steps.
- macOS without Homebrew returns manual Homebrew guidance.
- Windows with winget creates streamrip and ffmpeg steps.
- Windows missing winget returns manual ffmpeg guidance.
- Windows missing metaflac offers bundled FLAC option rather than failing core install.

**Step 2: Run tests**

```bash
.venv/bin/python -m pytest tests/test_installer.py -v
```

Expected: fail because install plan API is not rich enough.

**Step 3: Implement install plans**

Add:

- `InstallStep`
- `InstallPlan`
- `build_install_plan(environment)`

Each step should include:

- `tool`
- `label`
- `command`
- `required`
- `manual_command`

**Step 4: Run tests**

```bash
.venv/bin/python -m pytest tests/test_installer.py -v
```

Expected: pass.

**Step 5: Commit**

```bash
git add app/installer.py tests/test_installer.py
git commit -m "feat: add platform install plans"
```

### Task 4: Add Bundled FLAC Extraction

**Files:**
- Create: `app/tools/windows/README.md`
- Modify: `app/installer.py`
- Modify: `app/main.py`
- Test: `tests/test_installer.py`
- Test: `tests/test_installer_api.py`

**Step 1: Write failing tests**

Test that:

- A bundled FLAC zip can be extracted to the managed tools directory.
- The extraction endpoint returns target path and ok status.
- Missing bundled zip returns a readable error.

Use a temporary zip fixture in the test, not a large committed binary.

**Step 2: Run tests**

```bash
.venv/bin/python -m pytest tests/test_installer.py tests/test_installer_api.py -v
```

Expected: fail.

**Step 3: Implement extraction**

Add:

- `extract_bundled_flac(zip_path=None, target_dir=None)`
- `POST /api/tools/bundled-flac`

The production zip path should be `app/tools/windows/flac.zip`. If it is absent, return a clear manual-install response.

**Step 4: Run tests**

```bash
.venv/bin/python -m pytest tests/test_installer.py tests/test_installer_api.py -v
```

Expected: pass.

**Step 5: Commit**

```bash
git add app/installer.py app/main.py app/tools/windows/README.md tests/test_installer.py tests/test_installer_api.py
git commit -m "feat: add bundled flac extraction flow"
```

### Task 5: Improve Install Event Stream

**Files:**
- Modify: `app/installer.py`
- Test: `tests/test_installer.py`
- Test: `tests/test_installer_api.py`

**Step 1: Write failing tests**

Assert install events include:

- `step_started`
- `step_complete`
- `step_failed`
- `command`
- `copy_command`
- readable `label`

**Step 2: Run tests**

```bash
.venv/bin/python -m pytest tests/test_installer.py tests/test_installer_api.py -v
```

Expected: fail.

**Step 3: Implement events**

Emit user-readable events before and after every command. On failure, include the command and a short message.

**Step 4: Run tests**

```bash
.venv/bin/python -m pytest tests/test_installer.py tests/test_installer_api.py -v
```

Expected: pass.

**Step 5: Commit**

```bash
git add app/installer.py tests/test_installer.py tests/test_installer_api.py
git commit -m "feat: improve installer progress events"
```

### Task 6: Update Setup UI

**Files:**
- Modify: `app/static/index.html`
- Modify: `app/static/app.js`
- Modify: `app/static/styles.css`
- Test: existing pytest suite

**Step 1: Add UI structure**

Update setup panel to include:

- Platform line.
- Rich tool cards.
- Install progress cards.
- Copy command button.
- Recheck button.
- Windows `Use bundled FLAC tools` button.

**Step 2: Update JS rendering**

Use `tools_detail` where available. Fall back to existing boolean `tools`.

Add handlers for:

- copy manual command
- bundled FLAC extraction
- recheck environment

**Step 3: Run tests**

```bash
.venv/bin/python -m pytest
```

Expected: pass.

**Step 4: Manual smoke test**

Run:

```bash
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

Expected: setup page still renders, install button works, and setup can reach workspace when core tools are ready.

**Step 5: Commit**

```bash
git add app/static/index.html app/static/app.js app/static/styles.css
git commit -m "feat: improve setup assistant UI"
```

### Task 7: Package and Release

**Files:**
- Modify if needed: `.github/workflows/release.yml`
- Modify: `docs/index.html`
- Modify: `tests/test_pages_download_links.py`

**Step 1: Run full tests**

```bash
.venv/bin/python -m pytest
```

Expected: pass.

**Step 2: Build macOS locally**

```bash
./scripts/package_macos.sh
```

Expected: `dist/Tidal Max FLAC Studio.app` builds.

**Step 3: Smoke test packaged app**

Run packaged app executable and call `/api/setup/status`.

Expected: app starts and setup status returns rich environment data.

**Step 4: Commit any release docs**

```bash
git add docs/index.html tests/test_pages_download_links.py .github/workflows/release.yml
git commit -m "docs: prepare v0.2.0 downloads"
```

Skip commit if no files changed.

**Step 5: Tag release**

```bash
git tag v0.2.0
git push origin main
git push origin v0.2.0
```

Expected: GitHub Actions builds macOS and Windows zips.
