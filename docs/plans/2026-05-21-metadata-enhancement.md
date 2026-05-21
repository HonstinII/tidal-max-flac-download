# Metadata Enhancement Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add template-based output paths, `.lrc` sidecars, lyrics mode selection, cover repair, and FLAC metadata validation.

**Architecture:** Keep downloading focused on media assembly. Add metadata helpers for path templates and FLAC tag repair, extend lyrics helpers for mode-specific extraction and sidecar writing, then orchestrate post-processing from the queue worker.

**Tech Stack:** Python 3, FastAPI, mutagen, pytest, vanilla HTML/CSS/JS.

---

### Task 1: Template Paths

**Files:**
- Modify: `app/downloader.py`
- Test: `tests/test_downloader.py`

**Steps:**
1. Write failing tests for `{album_artist}/{album} ({year})` and `{track_number}. {artist} - {title}`.
2. Add `album_template`, `filename_template`, and `single_filename_template` to `DownloadOptions`.
3. Render tokens from `TrackItem`, sanitize each path segment, and keep the existing skip/overwrite/keep-both behavior.
4. Run `pytest tests/test_downloader.py`.

### Task 2: Lyrics Modes and LRC

**Files:**
- Modify: `app/lyrics.py`
- Test: `tests/test_lyrics.py`

**Steps:**
1. Write failing tests for `auto`, `synced`, `plain`, placeholder rejection, and `.lrc` sidecar output.
2. Add `extract_lyrics_text(payload, mode="auto")`.
3. Add `write_lrc(flac_path, lyrics)`.
4. Run `pytest tests/test_lyrics.py`.

### Task 3: Metadata Finalizer

**Files:**
- Create: `app/metadata.py`
- Test: `tests/test_metadata.py`

**Steps:**
1. Write failing tests for tag repair and cover presence detection.
2. Add `repair_flac_tags(flac_path, track)` using `mutagen.flac.FLAC`.
3. Add `has_cover(flac_path)` using FLAC pictures.
4. Run `pytest tests/test_metadata.py`.

### Task 4: Queue Options and Worker Integration

**Files:**
- Modify: `app/jobs.py`
- Modify: `app/main.py`
- Test: `tests/test_queue_api.py`
- Test: `tests/test_jobs.py`

**Steps:**
1. Write failing API tests proving new options are persisted.
2. Write failing worker test proving `.lrc`, metadata repair, and warning behavior are called.
3. Extend `QueueRequest` and `JobOptions`.
4. Fetch raw lyrics payload in the worker, extract by mode, pass templates to `DownloadOptions`, and run post-processing warnings safely.
5. Run affected tests.

### Task 5: UI Controls

**Files:**
- Modify: `app/static/index.html`
- Modify: `app/static/app.js`
- Modify: `app/static/styles.css`

**Steps:**
1. Add lyrics mode, write LRC, album template, filename template, and single filename template controls.
2. Add English/Chinese copy.
3. Include new fields in `queuePayload`.
4. Run full test suite.
