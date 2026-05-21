import base64

from pathlib import Path

import pytest

from app.downloader import (
    DownloadOptions,
    NoFlacRepresentation,
    prepare_output_path,
    parse_flac_dash_manifest,
    safe_name,
)


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
