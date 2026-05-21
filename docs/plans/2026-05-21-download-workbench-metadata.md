# Download Workbench and Metadata Enhancement Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a real download workbench with preview, queue, progress, retry, pause/cancel, history, log export, and richer metadata controls.

**Architecture:** Add a small SQLite-backed queue/history layer, then refactor the current batch job runner into a queue worker that persists track-level state and emits structured events. Keep streamrip/Tidal/ffmpeg behavior intact, but move path rendering, existing-file strategy, lyrics sidecars, and cover repair into dedicated helpers with focused tests.

**Tech Stack:** Python 3.12+, FastAPI, SQLite standard library, Server-Sent Events, vanilla HTML/CSS/JS, pytest.

---

## Phase 1: Download Workbench v0.3.0

### Task 1: Add Storage Layer

**Files:**
- Create: `app/storage.py`
- Test: `tests/test_storage.py`

**Step 1: Write failing tests**

Create tests for:

- Database file path under app data directory.
- Schema initialization creates `download_runs`, `queue_items`, and `settings`.
- Inserting and reading a run.
- Inserting and updating a queue item.

Example:

```python
def test_storage_initializes_schema(tmp_path):
    db = AppDatabase(tmp_path / "app.db")
    db.initialize()

    tables = db.table_names()

    assert {"download_runs", "queue_items", "settings"}.issubset(tables)
```

**Step 2: Run failing tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_storage.py -v
```

Expected: fails because `app.storage` does not exist.

**Step 3: Implement minimal storage**

Use `sqlite3` from the standard library. Add:

- `AppDatabase`
- `initialize()`
- `create_run(...)`
- `get_run(...)`
- `create_queue_item(...)`
- `update_queue_item(...)`
- `list_queue_items(run_id=None)`

Use dictionaries for row output to keep API code simple.

**Step 4: Run tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_storage.py -v
```

Expected: pass.

**Step 5: Commit**

```bash
git add app/storage.py tests/test_storage.py
git commit -m "feat: add queue storage"
```

### Task 2: Add Preview API

**Files:**
- Modify: `app/main.py`
- Modify: `app/tidal_api.py`
- Test: `tests/test_preview_api.py`

**Step 1: Write failing API tests**

Mock `read_tidal_auth` and `TidalApi.resolve`. Test:

- Track URL returns one preview item.
- Album URL returns album metadata and tracks.
- Invalid URL returns an error entry without crashing the whole request.

**Step 2: Run failing tests**

```bash
.venv/bin/python -m pytest tests/test_preview_api.py -v
```

Expected: `/api/preview` missing.

**Step 3: Implement endpoint**

Add:

```text
POST /api/preview
```

Input:

```json
{"urls": ["https://tidal.com/track/1"]}
```

Output:

```json
{"items": [...], "errors": [...]}
```

Keep this read-only; do not create queue rows yet.

**Step 4: Run tests**

```bash
.venv/bin/python -m pytest tests/test_preview_api.py tests/test_tidal_api.py -v
```

Expected: pass.

**Step 5: Commit**

```bash
git add app/main.py app/tidal_api.py tests/test_preview_api.py
git commit -m "feat: add tidal url preview"
```

### Task 3: Add Queue Models and API

**Files:**
- Modify: `app/jobs.py`
- Modify: `app/main.py`
- Modify: `app/storage.py`
- Test: `tests/test_queue_api.py`

**Step 1: Write failing tests**

Test:

- `POST /api/queue` creates a run and queue items from previewed tracks.
- `GET /api/queue` returns active queue rows.
- Queue item rows include title, artist, album, status, progress, attempts, output path, and error.

**Step 2: Run failing tests**

```bash
.venv/bin/python -m pytest tests/test_queue_api.py -v
```

Expected: endpoints missing.

**Step 3: Implement queue creation**

Use `parse_tidal_url` and `TidalApi.resolve` to create `queue_items` with status `ready`.

Do not start downloads in this task.

**Step 4: Run tests**

```bash
.venv/bin/python -m pytest tests/test_queue_api.py tests/test_storage.py -v
```

Expected: pass.

**Step 5: Commit**

```bash
git add app/jobs.py app/main.py app/storage.py tests/test_queue_api.py
git commit -m "feat: add persistent download queue"
```

### Task 4: Refactor Worker to Process Queue Items

**Files:**
- Modify: `app/jobs.py`
- Modify: `app/downloader.py`
- Test: `tests/test_jobs.py`
- Test: `tests/test_downloader.py`

**Step 1: Write failing tests**

Test:

- Worker marks item `downloading`, then `complete`.
- Failed track marks only that item `failed`; run can continue.
- `segment` events update `progress_current`.
- Run becomes `complete` when every item is complete, skipped, failed, or cancelled.

**Step 2: Run failing tests**

```bash
.venv/bin/python -m pytest tests/test_jobs.py -v
```

Expected: fail with old batch-only behavior.

**Step 3: Implement queue worker**

Add a worker method that accepts `run_id`, loads ready queue items, and processes them one at a time.

Preserve existing `/api/jobs` temporarily by having it call into the queue path, or keep both endpoints until the frontend migrates.

**Step 4: Run tests**

```bash
.venv/bin/python -m pytest tests/test_jobs.py tests/test_downloader.py -v
```

Expected: pass.

**Step 5: Commit**

```bash
git add app/jobs.py app/downloader.py tests/test_jobs.py tests/test_downloader.py
git commit -m "feat: process downloads as queue items"
```

### Task 5: Add Existing File Strategy

**Files:**
- Modify: `app/downloader.py`
- Modify: `app/jobs.py`
- Modify: `app/main.py`
- Test: `tests/test_downloader.py`

**Step 1: Write failing tests**

Test:

- `skip` returns `skipped` when file exists.
- `overwrite` replaces existing file.
- `keep_both` picks `filename (2).flac`.

**Step 2: Run failing tests**

```bash
.venv/bin/python -m pytest tests/test_downloader.py -v
```

Expected: fail because only boolean `skip_existing` exists.

**Step 3: Implement**

Replace `skip_existing` internally with:

```python
existing_strategy: Literal["skip", "overwrite", "keep_both"] = "skip"
```

Keep `skip_existing` request compatibility by mapping `True -> skip`, `False -> overwrite`.

**Step 4: Run tests**

```bash
.venv/bin/python -m pytest tests/test_downloader.py tests/test_jobs.py -v
```

Expected: pass.

**Step 5: Commit**

```bash
git add app/downloader.py app/jobs.py app/main.py tests/test_downloader.py
git commit -m "feat: add existing file strategies"
```

### Task 6: Add Retry, Pause, Resume, and Cancel APIs

**Files:**
- Modify: `app/jobs.py`
- Modify: `app/main.py`
- Modify: `app/storage.py`
- Test: `tests/test_queue_controls.py`

**Step 1: Write failing tests**

Test:

- Retry failed item resets status to `queued` and increments attempts.
- Pause sets run status `paused` and worker stops before next item.
- Resume restarts queued items.
- Cancel marks queued items cancelled and active run cancelled.

**Step 2: Run failing tests**

```bash
.venv/bin/python -m pytest tests/test_queue_controls.py -v
```

Expected: endpoints missing.

**Step 3: Implement controls**

Endpoints:

```text
POST /api/queue/items/{item_id}/retry
POST /api/queue/runs/{run_id}/pause
POST /api/queue/runs/{run_id}/resume
POST /api/queue/runs/{run_id}/cancel
```

Pause and cancel should be cooperative in v0.3.0: check between tracks and before ffmpeg.

**Step 4: Run tests**

```bash
.venv/bin/python -m pytest tests/test_queue_controls.py tests/test_jobs.py -v
```

Expected: pass.

**Step 5: Commit**

```bash
git add app/jobs.py app/main.py app/storage.py tests/test_queue_controls.py
git commit -m "feat: add queue controls"
```

### Task 7: Add History and Log Export

**Files:**
- Modify: `app/main.py`
- Modify: `app/storage.py`
- Test: `tests/test_history_api.py`

**Step 1: Write failing tests**

Test:

- `GET /api/history` returns recent runs.
- `GET /api/logs/{run_id}.txt` returns text/plain.
- Log includes run status, options, queue items, errors, and output paths.

**Step 2: Run failing tests**

```bash
.venv/bin/python -m pytest tests/test_history_api.py -v
```

Expected: endpoints missing.

**Step 3: Implement**

Add history list and text log formatter. Keep the log human-readable and copy-friendly.

**Step 4: Run tests**

```bash
.venv/bin/python -m pytest tests/test_history_api.py -v
```

Expected: pass.

**Step 5: Commit**

```bash
git add app/main.py app/storage.py tests/test_history_api.py
git commit -m "feat: add download history and logs"
```

### Task 8: Update Workbench UI

**Files:**
- Modify: `app/static/index.html`
- Modify: `app/static/app.js`
- Modify: `app/static/styles.css`
- Test: existing backend tests plus manual browser verification

**Step 1: Add static structure**

Add:

- Preview button.
- Preview result area.
- Queue table.
- Run action buttons: pause/resume, cancel, export log.
- Row retry buttons.
- Existing strategy selector.

**Step 2: Wire APIs**

In `app/static/app.js`, add:

- `previewUrls()`
- `enqueueDownloads()`
- `refreshQueue()`
- `retryQueueItem(itemId)`
- `pauseRun(runId)`
- `resumeRun(runId)`
- `cancelRun(runId)`
- `exportLog(runId)`

**Step 3: Manual verification**

Run:

```bash
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8021
```

Verify in browser:

- Preview renders track/album info.
- Queue rows appear.
- Progress updates per track.
- Failed row has retry.
- Pause/resume buttons change state.
- Cancel stops remaining queued items.
- Download complete shows open folder.

**Step 4: Run full tests**

```bash
.venv/bin/python -m pytest
```

Expected: pass.

**Step 5: Commit**

```bash
git add app/static/index.html app/static/app.js app/static/styles.css
git commit -m "feat: add download workbench UI"
```

## Phase 2: Metadata Studio v0.4.0

### Task 9: Add Path Template Renderer

**Files:**
- Create: `app/templates.py`
- Modify: `app/downloader.py`
- Test: `tests/test_templates.py`
- Test: `tests/test_downloader.py`

**Step 1: Write failing tests**

Test:

- Default album directory renders `{album_artist} - {album_title} ({year})`.
- Default filename renders `{track_number:02}. {artist} - {title}`.
- Invalid filesystem characters are removed.
- Missing values fall back to safe placeholders.

**Step 2: Run failing tests**

```bash
.venv/bin/python -m pytest tests/test_templates.py -v
```

Expected: `app.templates` missing.

**Step 3: Implement**

Add:

```python
render_album_dir(track, template: str) -> str
render_filename(track, template: str) -> str
render_output_path(track, output_dir, album_template, filename_template) -> Path
```

**Step 4: Run tests**

```bash
.venv/bin/python -m pytest tests/test_templates.py tests/test_downloader.py -v
```

Expected: pass.

**Step 5: Commit**

```bash
git add app/templates.py app/downloader.py tests/test_templates.py tests/test_downloader.py
git commit -m "feat: add output path templates"
```

### Task 10: Add Metadata Settings Storage and API

**Files:**
- Modify: `app/storage.py`
- Modify: `app/main.py`
- Test: `tests/test_settings_api.py`

**Step 1: Write failing tests**

Test:

- `GET /api/settings` returns defaults.
- `POST /api/settings` persists template and lyrics options.
- Invalid template fields return 400.

**Step 2: Run failing tests**

```bash
.venv/bin/python -m pytest tests/test_settings_api.py -v
```

Expected: settings endpoint missing.

**Step 3: Implement**

Settings:

```json
{
  "album_dir_template": "{album_artist} - {album_title} ({year})",
  "filename_template": "{track_number:02}. {artist} - {title}",
  "lyrics_mode": "both",
  "lyrics_preference": "synced_first",
  "cover_mode": "embed"
}
```

**Step 4: Run tests**

```bash
.venv/bin/python -m pytest tests/test_settings_api.py tests/test_storage.py -v
```

Expected: pass.

**Step 5: Commit**

```bash
git add app/main.py app/storage.py tests/test_settings_api.py
git commit -m "feat: persist metadata settings"
```

### Task 11: Refactor Lyrics Into Synced/Plain Payload

**Files:**
- Modify: `app/lyrics.py`
- Modify: `app/tidal_api.py`
- Modify: `app/jobs.py`
- Test: `tests/test_lyrics.py`
- Test: `tests/test_tidal_api.py`

**Step 1: Write failing tests**

Test:

- Payload returns synced and plain lyrics separately.
- Hash placeholder lyrics are rejected.
- `synced_first` selects synced when available.
- `plain_first` selects plain when available.

**Step 2: Run failing tests**

```bash
.venv/bin/python -m pytest tests/test_lyrics.py -v
```

Expected: fail with old string-only API.

**Step 3: Implement**

Add:

```python
LyricsPayload
extract_lyrics_payload(payload: dict) -> LyricsPayload
select_lyrics(payload, preference) -> str
```

Keep `extract_lyrics_text` as a compatibility wrapper during migration.

**Step 4: Run tests**

```bash
.venv/bin/python -m pytest tests/test_lyrics.py tests/test_tidal_api.py -v
```

Expected: pass.

**Step 5: Commit**

```bash
git add app/lyrics.py app/tidal_api.py app/jobs.py tests/test_lyrics.py tests/test_tidal_api.py
git commit -m "feat: model synced and plain lyrics"
```

### Task 12: Add `.lrc` Sidecar Writing

**Files:**
- Modify: `app/lyrics.py`
- Modify: `app/jobs.py`
- Test: `tests/test_lyrics.py`
- Test: `tests/test_jobs.py`

**Step 1: Write failing tests**

Test:

- `.lrc` sidecar is written next to FLAC.
- Plain lyrics are written without fake timestamps.
- `lyrics_mode=embed` does not write sidecar.
- `lyrics_mode=both` embeds and writes sidecar.

**Step 2: Run failing tests**

```bash
.venv/bin/python -m pytest tests/test_lyrics.py tests/test_jobs.py -v
```

Expected: sidecar functions missing.

**Step 3: Implement**

Add:

```python
write_lrc_sidecar(flac_path: Path, lyrics: str) -> Path | None
```

Emit:

```json
{"stage": "lyrics_sidecar", "track_id": "...", "path": "..."}
```

**Step 4: Run tests**

```bash
.venv/bin/python -m pytest tests/test_lyrics.py tests/test_jobs.py -v
```

Expected: pass.

**Step 5: Commit**

```bash
git add app/lyrics.py app/jobs.py tests/test_lyrics.py tests/test_jobs.py
git commit -m "feat: write lrc sidecar files"
```

### Task 13: Add Cover Repair Mode

**Files:**
- Modify: `app/covers.py`
- Modify: `app/jobs.py`
- Test: `tests/test_covers.py`
- Test: `tests/test_jobs.py`

**Step 1: Write failing tests**

Test:

- Repair removes existing picture block before importing.
- Missing `cover_id` skips repair.
- Cover failure emits warning but does not fail download.

**Step 2: Run failing tests**

```bash
.venv/bin/python -m pytest tests/test_covers.py tests/test_jobs.py -v
```

Expected: repair behavior incomplete.

**Step 3: Implement**

Add:

```python
repair_cover(flac_path, cover_id, cache_dir) -> bool
```

Use existing remove/import `metaflac` commands.

**Step 4: Run tests**

```bash
.venv/bin/python -m pytest tests/test_covers.py tests/test_jobs.py -v
```

Expected: pass.

**Step 5: Commit**

```bash
git add app/covers.py app/jobs.py tests/test_covers.py tests/test_jobs.py
git commit -m "feat: add cover repair mode"
```

### Task 14: Add Metadata Validation Events

**Files:**
- Modify: `app/jobs.py`
- Modify: `app/downloader.py`
- Test: `tests/test_metadata_validation.py`

**Step 1: Write failing tests**

Test:

- Missing album artist emits `metadata_warning`.
- Missing year emits `metadata_warning`.
- Track number is stored in output metadata when present.
- Album artist is stored when available.

**Step 2: Run failing tests**

```bash
.venv/bin/python -m pytest tests/test_metadata_validation.py -v
```

Expected: warnings not emitted.

**Step 3: Implement**

Add validation helper:

```python
validate_track_metadata(track) -> list[str]
```

Emit warnings before download. Add ffmpeg metadata for `album_artist` if present.

**Step 4: Run tests**

```bash
.venv/bin/python -m pytest tests/test_metadata_validation.py tests/test_downloader.py -v
```

Expected: pass.

**Step 5: Commit**

```bash
git add app/jobs.py app/downloader.py tests/test_metadata_validation.py
git commit -m "feat: add metadata validation warnings"
```

### Task 15: Add Metadata Settings UI

**Files:**
- Modify: `app/static/index.html`
- Modify: `app/static/app.js`
- Modify: `app/static/styles.css`
- Test: manual browser verification

**Step 1: Add UI controls**

Add an “Advanced metadata” disclosure with:

- Existing file strategy.
- Album directory template.
- Filename template.
- Lyrics mode.
- Lyrics preference.
- Cover mode.

**Step 2: Wire settings API**

Load settings on startup and save changes on blur/change.

**Step 3: Manual verification**

Run:

```bash
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8021
```

Verify:

- Settings load.
- Changes persist after reload.
- Invalid template shows an error.
- Start download sends settings to queue creation.

**Step 4: Run full tests**

```bash
.venv/bin/python -m pytest
```

Expected: pass.

**Step 5: Commit**

```bash
git add app/static/index.html app/static/app.js app/static/styles.css
git commit -m "feat: add metadata settings UI"
```

## Final Verification

Run:

```bash
.venv/bin/python -m pytest
./scripts/package_macos.sh
```

Manual app smoke:

```bash
dist/Tidal\ Max\ FLAC\ Studio.app/Contents/MacOS/Tidal\ Max\ FLAC\ Studio
```

Verify:

- App launches.
- Existing Tidal binding is detected.
- Preview works.
- Queue works.
- Progress updates.
- Retry works.
- Pause/resume works between tracks.
- Cancel stops queued tracks.
- History persists after app restart.
- Log export downloads or opens a `.txt` file.
- `.lrc` files are written when enabled.
- Cover repair prompts for `metaflac` only when needed.

## Release Notes Draft

```text
v0.3.0
- Added download preview for Tidal track and album URLs.
- Added persistent download queue with per-track progress.
- Added retry, pause/resume, cancel, history, and log export.
- Added skip/overwrite/keep-both handling for existing files.

v0.4.0
- Added album directory and filename templates.
- Added .lrc sidecar lyrics export.
- Added synced/plain lyrics preference.
- Added cover repair mode.
- Added metadata validation warnings.
```

