# Metadata Enhancement Design

## Goal

Add a v0.4 metadata pass that makes downloaded FLAC files easier to organize and use outside the app: repaired tags, optional cover repair, `.lrc` sidecar files, selectable lyrics mode, and configurable album/file templates.

## Scope

- Default album directory: `{album_artist}/{album} ({year})`
- Default album filename: `{track_number}. {artist} - {title}`
- Default single filename: `{artist} - {title}`
- Lyrics modes: `auto`, `synced`, `plain`
- `.lrc` sidecar writing uses the final FLAC path stem.
- Metadata validation rewrites title, artist, album, album artist, date/year, and track number from Tidal preview data.
- Cover repair embeds cover art when the FLAC has no picture, or replaces existing cover art when explicit cover embedding is enabled.

## Architecture

Introduce a small `metadata.py` module for template rendering, FLAC tag repair, and cover presence checks. Keep network cover download in `covers.py` and lyrics extraction in `lyrics.py`. The queue worker becomes the orchestrator: resolve lyrics payload according to mode, download, then finalize metadata and sidecars.

The downloader remains responsible for FLAC assembly only. Output path generation moves behind template-aware helpers so queue and tests can reason about paths without touching ffmpeg.

## Data Flow

1. UI posts queue options with `lyrics_mode`, `write_lrc`, `album_template`, `filename_template`, and `single_filename_template`.
2. `DownloadJobManager` stores options in the run record.
3. For each track, the downloader renders the output path from templates.
4. After successful download, the worker:
   - embeds or repairs cover art when enabled,
   - extracts lyrics according to mode,
   - embeds lyrics when enabled,
   - writes `.lrc` when enabled,
   - validates and rewrites core FLAC tags.

## Error Handling

Metadata extras should not turn a successful download into a failed track. Cover, lyrics, LRC, and tag repair failures emit warning events and leave the track complete.

## Tests

Add focused tests for:

- Template rendering and sanitization.
- Metadata tag rewrite using `mutagen.flac.FLAC`.
- Lyrics mode extraction and `.lrc` sidecar writing.
- Queue option persistence.
- Job worker calling metadata finalization without failing the track on warning.
