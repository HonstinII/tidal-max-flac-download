# Download Workbench and Metadata Enhancement Design

## Goal

Turn the current downloader from a simple batch runner into a clearer local workstation:

- Users can preview what a Tidal URL resolves to before committing.
- Downloads appear as a queue with per-track state, progress, retry, pause, cancel, and history.
- Finished files use predictable directory and filename templates.
- Cover and lyrics handling become visible, configurable, and recoverable.

## Current System

The app currently has one download job per submitted URL batch. `app/jobs.py` resolves URLs, loops through tracks, calls `download_track_as_flac`, then optionally embeds cover art and lyrics. Events are streamed through Server-Sent Events and rendered in `app/static/app.js`.

This is enough for basic downloads, but it has limits:

- There is no durable queue or history.
- Events are session logs, not first-class track rows.
- Segment progress exists only as repeated `segment` events.
- Failed tracks cannot be retried individually.
- Pause and cancel are not modeled.
- File naming and album folder layout are hard-coded in `app/downloader.py`.
- Lyrics are embedded into FLAC tags only; no `.lrc` sidecar is written.

## Product Shape

The work should be split into two connected surfaces:

1. **Queue Workbench**
   - Left side: URL input, preview, options, start button.
   - Right side: queue table grouped by album/source URL.
   - Bottom or side drawer: compact logs and export button.

2. **Metadata Settings**
   - Output strategy: skip, overwrite, or keep both.
   - Album directory template.
   - Filename template.
   - Lyrics mode: embed only, `.lrc` only, both, or off.
   - Lyrics type preference: synced first, plain fallback.
   - Cover mode: embed cover, repair existing cover, or skip cover.

## Recommended Approach

### Approach A: In-Memory Queue First, SQLite Later

Implement queue rows in memory and keep history in a JSON file.

Pros:
- Fastest implementation.
- Less migration work.
- Good enough for a small personal app.

Cons:
- Harder to query, filter, and evolve.
- History can become messy.
- Pause/cancel state survives poorly across app restarts.

### Approach B: SQLite Queue and History

Add a small local SQLite database under the app data directory. Use it for queue items, run history, track status, output paths, error messages, and settings.

Pros:
- Clean state model.
- Real history.
- Easy retry and log export.
- Good base for future features.

Cons:
- Slightly more code.
- Needs schema and migration tests.

### Approach C: Keep Current Job Model, Add UI Polish Only

Only improve the frontend event display and add a few options.

Pros:
- Lowest risk.

Cons:
- Does not solve queue, retry, pause/cancel, or history properly.
- Likely to need a rewrite soon.

**Recommendation:** Approach B. This app is becoming a real desktop tool, and queue/history/settings are core product state. SQLite is the right amount of structure without adding a server dependency.

## Queue Data Model

Add `app/storage.py` with a local SQLite database:

```text
App data dir/
  tidal-max-flac-studio.db
```

Tables:

```sql
download_runs(
  id TEXT PRIMARY KEY,
  created_at REAL NOT NULL,
  completed_at REAL,
  status TEXT NOT NULL,
  output_dir TEXT NOT NULL,
  options_json TEXT NOT NULL
)

queue_items(
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  source_url TEXT NOT NULL,
  source_kind TEXT,
  source_id TEXT,
  track_id TEXT,
  title TEXT,
  artist TEXT,
  album_title TEXT,
  album_artist TEXT,
  album_year TEXT,
  track_number INTEGER,
  cover_id TEXT,
  output_path TEXT,
  status TEXT NOT NULL,
  progress_current INTEGER DEFAULT 0,
  progress_total INTEGER DEFAULT 0,
  attempts INTEGER DEFAULT 0,
  error TEXT,
  created_at REAL NOT NULL,
  updated_at REAL NOT NULL
)

settings(
  key TEXT PRIMARY KEY,
  value_json TEXT NOT NULL
)
```

Queue item statuses:

```text
queued
resolving
ready
downloading
postprocessing
complete
skipped
failed
cancelled
```

Run statuses:

```text
queued
running
paused
complete
failed
cancelled
```

## Preview Flow

Add an endpoint:

```text
POST /api/preview
```

Input:

```json
{
  "urls": ["https://tidal.com/album/523643849/u"]
}
```

Output:

```json
{
  "items": [
    {
      "source_url": "...",
      "kind": "album",
      "item_id": "523643849",
      "track_count": 13,
      "album_title": "...",
      "album_artist": "...",
      "tracks": [
        {
          "track_id": "...",
          "title": "...",
          "artist": "...",
          "track_number": 1,
          "cover_id": "..."
        }
      ]
    }
  ],
  "errors": []
}
```

The frontend should show a compact preview before enqueueing:

- Single track: title, artist, album.
- Album: album title, album artist, year, track count, first few tracks.
- Errors: invalid URL, auth failure, region unavailable.

## Download Queue Flow

Add endpoints:

```text
POST /api/queue
GET /api/queue
GET /api/queue/events
POST /api/queue/items/{item_id}/retry
POST /api/queue/runs/{run_id}/pause
POST /api/queue/runs/{run_id}/resume
POST /api/queue/runs/{run_id}/cancel
GET /api/history
GET /api/logs/{run_id}.txt
```

The worker should process queue items one at a time per run at first. Segment concurrency remains inside each track download. This keeps cancellation and retry understandable.

### Pause

Pause should stop before the next track begins. It should not interrupt an active ffmpeg process in the first implementation.

### Cancel

Cancel should:

- Mark the run as `cancelled`.
- Stop before starting the next track.
- If possible, signal the current download through a cancellation token checked between segment completions and before ffmpeg starts.

Hard-killing in-flight subprocesses can be a later enhancement.

### Retry

Retry should:

- Reset a failed item to `queued`.
- Increment `attempts`.
- Preserve the previous error in history/logs.

## Progress Model

`download_track_as_flac` already knows the segment count. Extend emitted events:

```json
{
  "stage": "progress",
  "track_id": "526130766",
  "current": 7,
  "total": 32
}
```

The queue row should show:

- Status pill.
- Progress bar.
- Current/total segments.
- Output path when done.
- Retry button for failed rows.

## Existing File Strategy

Replace boolean `skip_existing` with:

```text
existing_strategy = skip | overwrite | keep_both
```

Behavior:

- `skip`: current behavior, but record `skipped`.
- `overwrite`: replace the existing output file.
- `keep_both`: append ` (2)`, ` (3)`, etc.

The UI should default to `skip` for safety.

## Metadata Settings

Add `app/templates.py` for path templating.

Default album directory:

```text
{album_artist} - {album_title} ({year})
```

Default filename:

```text
{track_number:02}. {artist} - {title}
```

Supported fields:

```text
artist
album_artist
album_title
year
track_number
title
track_id
quality
sample_rate
bit_depth
```

Every rendered path segment must pass through `safe_name`.

## Lyrics Enhancement

Current `extract_lyrics_text` chooses `subtitles` first and falls back to `lyrics`, while rejecting placeholder hash lyrics.

Enhance it into:

```python
LyricsPayload(
    synced: str | None,
    plain: str | None,
    selected: str | None,
    selected_kind: Literal["synced", "plain", "none"],
)
```

Modes:

- `embed`: write selected lyrics into FLAC tag.
- `lrc`: write `.lrc` sidecar.
- `both`: embed and write `.lrc`.
- `off`: do not fetch lyrics.

Preference:

- `synced_first`: use synced lyrics, fallback to plain.
- `plain_first`: use plain lyrics, fallback to synced.

Sidecar path:

```text
same folder / same filename .lrc
```

For plain lyrics, write plain text to `.lrc`; do not fake timestamps.

## Cover Enhancement

Cover handling should remain optional and gated by `metaflac`.

Modes:

- `embed`: embed cover after download.
- `repair`: if output exists and cover embedding is enabled, re-download/re-embed cover.
- `off`: skip.

Auto repair should:

- Remove existing FLAC picture blocks before importing a new picture.
- Use cached cover images.
- Emit `cover_repaired` or `cover_failed`.

## UI Design

The UI should stay dense and tool-like, not become a marketing page.

Recommended layout:

- Top header remains.
- Left panel:
  - Tidal URLs textarea.
  - Preview button.
  - Output folder row.
  - Strategy/select controls.
  - Metadata template toggles in a collapsible “Advanced” section.
  - Start queue button.
- Right panel:
  - Queue table.
  - Album/source grouping.
  - Row actions: retry, reveal file, copy error.
  - Run actions: pause/resume, cancel, export log.
- Completed state:
  - Open output folder button remains top-right.

## Error Handling

All failures should be track-scoped where possible. One failed track should not fail the whole album.

Examples:

- Preview URL invalid: show preview error, do not enqueue that URL.
- No FLAC representation: mark item failed with the message.
- Lyrics unavailable: warn, continue.
- Cover tool missing: prompt only when cover embedding is enabled.
- Existing file skipped: mark skipped, do not show as failure.

## Testing Strategy

Add tests before implementation:

- Storage schema initializes.
- Queue item transitions are persisted.
- Preview resolves track and album URLs.
- Existing strategy renders skip/overwrite/keep-both behavior.
- Progress events update queue item counters.
- Retry resets failed items.
- Pause stops before next item.
- Cancel marks remaining queued items cancelled.
- Template rendering sanitizes invalid path characters.
- Lyrics sidecar writes `.lrc`.
- Cover repair calls remove/import picture operations.

## Release Strategy

This is a large feature. Ship in two releases:

### v0.3.0 Download Workbench

- Preview.
- Queue table.
- Per-track progress.
- Retry failed track.
- Pause/resume before next track.
- Cancel run.
- History.
- Log export.
- Open folder remains.
- Existing file strategy.

### v0.4.0 Metadata Studio

- Template settings.
- `.lrc` sidecars.
- Synced/plain lyrics preference.
- Cover repair.
- Metadata validation events.

