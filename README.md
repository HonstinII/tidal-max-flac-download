# Tidal Max FLAC Studio

A local desktop/web app for binding a Tidal account and downloading Tidal track or album URLs as Max/Hi-Res FLAC files with embedded cover art and lyrics.

This app is designed for personal offline listening. It does not ask for or store your Tidal password. Binding happens through Tidal's official device authorization page.

## Credit

The core downloader foundation is [streamrip](https://github.com/nathom/streamrip), created by [nathom](https://github.com/nathom).

This project is a local studio wrapper around that foundation. The work here is to integrate the one-click local setup flow, Tidal binding, Max FLAC download workflow, cover embedding, lyrics tagging, output folder controls, bilingual UI, and a desktop/web interface for the whole toolchain.

In short: `streamrip` is the core. Tidal Max FLAC Studio is the UI and workflow layer around it.

## GitHub Pages

GitHub Pages is the instruction page, not the product runtime. Users enter the product through the local desktop app, or through the local web server during development:

```text
GitHub Pages guide -> GitHub repository -> local desktop app
```

GitHub Pages cannot run the downloader itself because the downloader needs local tools, local Tidal authorization, and access to your local output folder.

The included Pages workflow publishes `docs/index.html` when `main` is pushed:

```text
.github/workflows/pages.yml
```

After pushing to GitHub, enable Pages from **Settings -> Pages -> GitHub Actions** if GitHub does not enable it automatically.

## Requirements

- macOS
- Homebrew
- Python 3.12 or newer
- `streamrip`
- `ffmpeg`
- `metaflac` from the `flac` package
- A Tidal account with access to the tracks you download

The UI can install missing macOS tools from the setup screen:

- `streamrip`: `python3 -m pip install --user streamrip`
- `ffmpeg`: `brew install ffmpeg`
- `metaflac`: `brew install flac`

## Install

For most users, download the packaged app from:

```text
https://github.com/HonstinII/tidal-max-flac-download/releases
```

Download the macOS zip or Windows zip, unzip it, then open **Tidal Max FLAC Studio**.

Developers can also run from source:

```bash
./scripts/install.sh
```

Manual setup:

```bash
brew install ffmpeg flac
python3 -m pip install --user streamrip
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Run

Desktop window:

```bash
.venv/bin/python -m app.desktop
```

Local browser server:

```bash
./scripts/run.sh
```

The script starts the local server and opens:

```text
http://127.0.0.1:8000
```

Manual run command:

```bash
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Package Desktop Apps

Release builds are generated automatically by GitHub Actions when a `v*` tag is pushed. The workflow builds:

- `Tidal-Max-FLAC-Studio-macOS.zip`
- `Tidal-Max-FLAC-Studio-Windows.zip`

Build a macOS `.app` on macOS:

```bash
./scripts/package_macos.sh
```

Build a Windows `.exe` on Windows PowerShell:

```powershell
.\scripts\package_windows.ps1
```

The packaged app opens the same UI in a native desktop window and starts the local backend automatically.

The packaged macOS app and Windows executable use the product name **Tidal Max FLAC Studio** and the custom icon in `assets/`. When running the development command directly with `python -m app.desktop`, macOS may still show the Python interpreter icon because that is not the packaged app.

## Binding Tidal

On first launch, the app shows a two-step binding guide.

1. Check local tools.
2. Click **Start Tidal binding**, then click the authorization page link.

The app automatically detects the token and writes it to the local streamrip-compatible config:

```text
~/Library/Application Support/streamrip/config.toml
```

You can unbind from the account menu after binding.

## Downloading

Paste one or more Tidal URLs:

```text
https://tidal.com/track/526130766/u
https://tidal.com/album/523643849/u
```

Output defaults to:

```text
~/Music/Streamrip/Tidal-Max-FLAC
```

The app requests Tidal `HI_RES` playback and requires a FLAC DASH representation. It does not silently save AAC when FLAC is unavailable.

The download workspace can open the output folder picker and open the selected folder in Finder. It can embed Tidal cover art into the FLAC file and write available Tidal lyrics into the FLAC `LYRICS` tag.

## Troubleshooting

If binding expires, generate a new Tidal link from the setup screen.

If `ffmpeg`, `metaflac`, or `streamrip` is missing, use the setup screen's **Install missing tools** button or run:

```bash
brew install ffmpeg flac
python3 -m pip install --user streamrip
```

If a track fails with "No FLAC representation", your account, region, or that specific Tidal release may not expose a FLAC Max stream.

## Safety

Do not commit local tokens, downloaded music, cached cover art, or database files. The `.gitignore` is configured to avoid those files.

Use this only in ways consistent with your streaming service terms and local law.
