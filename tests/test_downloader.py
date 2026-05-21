import base64
import json

from pathlib import Path

import pytest

from app.downloader import (
    DownloadOptions,
    LossyAudioAvailable,
    NoFlacRepresentation,
    build_output_path,
    prepare_output_path,
    parse_flac_dash_manifest,
    safe_name,
)
from app.tidal_api import TrackItem


def encoded_mpd(codec="flac"):
    xml = f"""<?xml version='1.0' encoding='UTF-8'?>
<MPD xmlns="urn:mpeg:dash:schema:mpd:2011">
  <Period>
    <AdaptationSet>
      <Representation codecs="{codec}" audioSamplingRate="48000">
        <SegmentTemplate initialization="https://example.com/init.mp4" media="https://example.com/$Number$.mp4" startNumber="1">
          <SegmentTimeline>
            <S d="1" r="2" />
            <S d="1" />
          </SegmentTimeline>
        </SegmentTemplate>
      </Representation>
    </AdaptationSet>
  </Period>
</MPD>"""
    return base64.b64encode(xml.encode("utf-8")).decode("ascii")


def encoded_json_manifest(codec="flac", encryption_type="NONE"):
    payload = {
        "urls": ["https://example.com/audio.flac"],
        "codecs": codec,
        "encryptionType": encryption_type,
    }
    return base64.b64encode(json.dumps(payload).encode("utf-8")).decode("ascii")


def test_parse_flac_dash_manifest_extracts_segment_urls():
    manifest = parse_flac_dash_manifest(encoded_mpd())

    assert manifest.initialization_url == "https://example.com/init.mp4"
    assert manifest.segment_urls == [
        "https://example.com/1.mp4",
        "https://example.com/2.mp4",
        "https://example.com/3.mp4",
        "https://example.com/4.mp4",
    ]
    assert manifest.sample_rate == "48000"


def test_parse_flac_dash_manifest_rejects_non_flac_codec():
    with pytest.raises(NoFlacRepresentation, match="Expected FLAC"):
        parse_flac_dash_manifest(encoded_mpd("mp4a.40.2"))


def test_parse_flac_dash_manifest_extracts_tidal_json_url():
    manifest = parse_flac_dash_manifest(encoded_json_manifest())

    assert manifest.initialization_url == "https://example.com/audio.flac"
    assert manifest.segment_urls == []
    assert manifest.codec == "flac"


def test_parse_flac_dash_manifest_requires_confirmation_for_aac_json():
    with pytest.raises(LossyAudioAvailable, match="mp4a"):
        parse_flac_dash_manifest(encoded_json_manifest(codec="mp4a.40.2"))


def test_parse_flac_dash_manifest_accepts_confirmed_aac_json():
    manifest = parse_flac_dash_manifest(
        encoded_json_manifest(codec="mp4a.40.2"),
        allow_lossy_audio=True,
    )

    assert manifest.initialization_url == "https://example.com/audio.flac"
    assert manifest.codec == "mp4a.40.2"


def test_parse_flac_dash_manifest_rejects_encrypted_tidal_json():
    with pytest.raises(NoFlacRepresentation, match="Encrypted"):
        parse_flac_dash_manifest(encoded_json_manifest(encryption_type="OLD_AES"))


def test_safe_name_removes_path_separators_and_invalid_characters():
    assert safe_name('A/B:C*D?"E<>|') == "ABCDE"


def test_prepare_output_path_skips_existing_file(tmp_path):
    output = tmp_path / "song.flac"
    output.write_bytes(b"x" * 1024 * 1024 * 2)

    prepared, status = prepare_output_path(output, DownloadOptions(tmp_path, existing_strategy="skip"))

    assert prepared == output
    assert status == "skipped"


def test_prepare_output_path_overwrites_existing_file(tmp_path):
    output = tmp_path / "song.flac"
    output.write_text("old")

    prepared, status = prepare_output_path(output, DownloadOptions(tmp_path, existing_strategy="overwrite"))

    assert prepared == output
    assert status == "download"


def test_prepare_output_path_keeps_both_files(tmp_path):
    output = tmp_path / "song.flac"
    output.write_text("old")
    (tmp_path / "song (2).flac").write_text("old")

    prepared, status = prepare_output_path(output, DownloadOptions(tmp_path, existing_strategy="keep_both"))

    assert prepared == tmp_path / "song (3).flac"
    assert status == "download"


def test_build_output_path_uses_album_and_filename_templates(tmp_path):
    track = TrackItem(
        track_id="1",
        title="Bad/Name",
        artist="Artist",
        album_title="Album",
        album_artist="Album Artist",
        album_year="2026",
        cover_id=None,
        track_number=3,
    )

    output = build_output_path(track, DownloadOptions(output_dir=tmp_path))

    assert output == tmp_path / "Album Artist" / "Album (2026)" / "03. Artist - BadName.flac"


def test_build_output_path_uses_single_template_without_track_number(tmp_path):
    track = TrackItem(
        track_id="1",
        title="Song",
        artist="Artist",
        album_title="",
        album_artist="",
        album_year="",
        cover_id=None,
        track_number=None,
    )

    output = build_output_path(track, DownloadOptions(output_dir=tmp_path))

    assert output == tmp_path / "Artist - Song.flac"
