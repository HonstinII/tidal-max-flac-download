# Tidal Max FLAC Studio

A local web app for binding a Tidal account and downloading Tidal track or album URLs as Max/Hi-Res FLAC files with embedded cover art.

This app is designed for personal offline listening. It does not ask for or store your Tidal password. Binding happens through Tidal's official device authorization page.

## Requirements

- macOS
- Homebrew
- Python 3.14 or newer
- `ffmpeg`
- `metaflac` from the `flac` package
- A Tidal account with access to the tracks you download

## Install

```bash
./scripts/install.sh
```

Manual setup:

```bash
brew install ffmpeg flac
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Run

```bash
.venv/bin/python -m uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

## Binding Tidal

On first launch, the app shows a three-step binding guide.

1. Check local tools.
2. Click **Start Tidal binding**.
3. Sign in on the Tidal page that opens.

The app automatically detects the token and writes it to the local streamrip-compatible config:

```text
~/Library/Application Support/streamrip/config.toml
```

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

The download workspace can open the output folder picker and open the selected folder in Finder. It can also embed available Tidal lyrics into the FLAC `LYRICS` tag.

## Troubleshooting

If binding expires, generate a new Tidal link from the setup screen.

If `ffmpeg` or `metaflac` is missing:

```bash
brew install ffmpeg flac
```

If a track fails with "No FLAC representation", your account, region, or that specific Tidal release may not expose a FLAC Max stream.

## GitHub Safety

Do not commit local tokens, downloaded music, cached cover art, or database files. The `.gitignore` is configured to avoid those files.
