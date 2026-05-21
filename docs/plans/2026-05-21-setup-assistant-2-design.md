# Setup Assistant 2.0 Design

## Goal

Improve first-run installation for ordinary users while keeping streamrip as the core download engine. The setup flow should detect platform-specific requirements, offer safe one-click installation where reasonable, and give clear manual recovery steps when automation fails.

## Scope

This design covers:

- Platform detection for macOS and Windows.
- Tool detection for streamrip, ffmpeg, metaflac, Homebrew, winget, Python, and app-managed tool directories.
- macOS one-click installation for streamrip, ffmpeg, and flac/metaflac when Homebrew is available.
- macOS Homebrew guidance when Homebrew is missing.
- Windows one-click installation for streamrip and ffmpeg where winget/Python are available.
- Windows metaflac options:
  - Use bundled FLAC tools by extracting a packaged zip into the app data directory.
  - Manual install guide for users who prefer global installation.
- Step-based install progress.
- Failed install recovery with copyable commands.
- Automatic recheck after installation.

Out of scope for the first implementation:

- Silent Homebrew installation.
- Silent administrator privilege elevation.
- Silent system PATH mutation.
- Automatic download from unknown third-party archives.
- Replacing streamrip as the core downloader.

## User Flow

1. User opens the app.
2. App detects platform and toolchain state.
3. If core tools are ready, user proceeds to Tidal binding.
4. If core tools are missing, setup shows a platform-specific install panel.
5. User chooses one-click install where available.
6. App streams step progress:
   - Checking package manager
   - Installing streamrip
   - Installing ffmpeg
   - Installing flac/metaflac or unpacking bundled FLAC tools
   - Rechecking environment
7. If a step fails, setup shows:
   - Failed tool name
   - Human-readable reason
   - Exact command to copy
   - Recheck button
8. When required tools are ready, setup unlocks Tidal binding.

## Platform Behavior

### macOS

Detection:

- `platform.system() == "Darwin"`
- Homebrew is ready if `brew` exists in known paths.
- ffmpeg is ready if `ffmpeg` exists in PATH or known Homebrew paths.
- metaflac is ready if `metaflac` exists in PATH or known Homebrew paths.
- streamrip is ready if `rip`, `streamrip`, or the existing `~/Applications/streamrip-dev/bin/rip` exists.

Install:

- If Homebrew exists:
  - `python3 -m pip install --user streamrip`
  - `brew install ffmpeg`
  - `brew install flac`
- If Homebrew is missing:
  - Do not install it automatically.
  - Show the official Homebrew install command with copy support.
  - Allow user to recheck afterward.

### Windows

Detection:

- `platform.system() == "Windows"`
- winget is ready if `winget.exe` exists.
- ffmpeg is ready if `ffmpeg.exe` exists in PATH or app-managed tools.
- metaflac is ready if `metaflac.exe` exists in PATH or app-managed tools.
- streamrip is ready if `rip.exe`, `streamrip.exe`, or Python user scripts contain streamrip.

Install:

- streamrip:
  - `python -m pip install --user streamrip`
- ffmpeg:
  - Prefer `winget install --id Gyan.FFmpeg -e --accept-package-agreements --accept-source-agreements`
  - If winget is missing, show manual guidance.
- metaflac:
  - Offer `Use bundled FLAC tools`.
  - This extracts `app/tools/windows/flac.zip` into `%LOCALAPPDATA%/Tidal Max FLAC Studio/tools/flac`.
  - App adds the extracted directory to its runtime PATH.
  - Offer manual install guide as an alternative.

## Data Model

Setup status should return richer tool data:

```json
{
  "platform": {
    "system": "Darwin",
    "name": "macOS",
    "supports_auto_install": true
  },
  "tools": {
    "streamrip": {
      "ok": true,
      "required": true,
      "path": "/Users/user/.local/bin/rip",
      "installable": true,
      "description": "Core download tool"
    },
    "ffmpeg": {
      "ok": false,
      "required": true,
      "path": null,
      "installable": true,
      "description": "Core audio processor"
    },
    "metaflac": {
      "ok": false,
      "required": false,
      "path": null,
      "installable": true,
      "description": "Optional FLAC metadata helper"
    }
  },
  "package_managers": {
    "homebrew": {
      "ok": true,
      "path": "/opt/homebrew/bin/brew"
    },
    "winget": {
      "ok": false,
      "path": null
    }
  },
  "manual_commands": {
    "homebrew": "/bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"",
    "ffmpeg": "brew install ffmpeg",
    "metaflac": "brew install flac"
  }
}
```

The current boolean `tools` shape can be kept for compatibility during migration, but UI should prefer the richer structure once available.

## Backend Components

Add or extend:

- `app/environment.py`
  - Platform detection.
  - Tool path detection.
  - App-managed tools directory.
  - Runtime PATH construction.
- `app/installer.py`
  - Step-based install plans.
  - macOS Homebrew-aware install.
  - Windows winget-aware install.
  - Bundled FLAC extraction.
  - Copyable manual command generation.
- `app/main.py`
  - Existing setup and install endpoints can stay.
  - Add endpoint for bundled FLAC extraction if easier to keep separate.

## Frontend Components

Update setup UI in:

- `app/static/index.html`
- `app/static/app.js`
- `app/static/styles.css`

UI should show:

- Platform label.
- Tool cards with:
  - Ready / Missing / Installing / Failed.
  - Required / Optional.
  - Install path when found.
  - Short description.
- Install action area:
  - Install missing tools.
  - Use bundled FLAC tools on Windows when metaflac is missing.
  - Manual install guide when package manager is missing.
- Install log as user-readable step events, not raw command spam.
- Failure card with copyable command and Recheck.

## Error Handling

Installer events should include:

```json
{
  "stage": "step_failed",
  "tool": "ffmpeg",
  "message": "brew install ffmpeg exited with code 1",
  "command": "brew install ffmpeg"
}
```

Frontend should show the copyable command and keep the Recheck button available. One failed optional tool should not block the download workspace if core tools are ready.

## Testing

Backend tests:

- macOS detection finds Homebrew paths.
- Windows detection finds app-managed tools.
- Missing Homebrew produces guide, not auto install.
- Windows metaflac extraction creates app tool files.
- Install events include readable step names and copyable commands.

Frontend tests remain lightweight because this project currently uses static JS without a browser test harness. Add Python tests for generated installer plans and API responses.

## Release Notes

This should become `v0.2.0` because it changes first-run setup behavior materially.
