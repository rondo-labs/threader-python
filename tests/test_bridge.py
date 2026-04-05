"""Tests for threader_python.bridge and _display."""

from __future__ import annotations

import pandas as pd
import pytest

from threader_python._display import _print_fallback, is_threader_env
from threader_python.bridge import _extract_ids, play, playlist, select


class TestExtractIds:
    def test_from_list(self) -> None:
        assert _extract_ids(["a", "b", "c"]) == ["a", "b", "c"]

    def test_from_dataframe(self) -> None:
        df = pd.DataFrame({"id": ["e1", "e2", "e3"], "type": ["pass", "shot", "pass"]})
        assert _extract_ids(df) == ["e1", "e2", "e3"]

    def test_from_dataframe_missing_column(self) -> None:
        df = pd.DataFrame({"name": ["a"]})
        with pytest.raises(ValueError, match="'id' column"):
            _extract_ids(df)

    def test_from_integers(self) -> None:
        assert _extract_ids([1, 2, 3]) == ["1", "2", "3"]


class TestEnvironmentDetection:
    def test_not_threader_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("THREADER_PROJECT_PATH", raising=False)
        assert not is_threader_env()

    def test_is_threader_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("THREADER_PROJECT_PATH", "/some/path")
        assert is_threader_env()


class TestPrintFallback:
    def test_select_fallback(self, capsys: pytest.CaptureFixture[str]) -> None:
        _print_fallback("select", {"eventIds": ["e1", "e2"]})
        captured = capsys.readouterr()
        assert "Selected 2 events" in captured.out
        assert "e1" in captured.out

    def test_play_fallback(self, capsys: pytest.CaptureFixture[str]) -> None:
        _print_fallback("play", {"clipIds": ["c1"]})
        captured = capsys.readouterr()
        assert "Play 1 clips" in captured.out

    def test_playlist_fallback(self, capsys: pytest.CaptureFixture[str]) -> None:
        _print_fallback("playlist", {"eventIds": ["e1", "e2", "e3"], "title": "Test"})
        captured = capsys.readouterr()
        assert 'playlist "Test"' in captured.out
        assert "3 events" in captured.out

    def test_truncation(self, capsys: pytest.CaptureFixture[str]) -> None:
        ids = [f"e{i}" for i in range(20)]
        _print_fallback("select", {"eventIds": ids})
        captured = capsys.readouterr()
        assert "..." in captured.out


class TestBridgeFunctions:
    """Test that bridge functions emit correct fallback output in non-Threader env."""

    def setup_method(self) -> None:
        import os

        # Ensure we're not in a Threader env
        os.environ.pop("THREADER_PROJECT_PATH", None)

    def test_select_prints(self, capsys: pytest.CaptureFixture[str]) -> None:
        select(["e1", "e2"])
        captured = capsys.readouterr()
        assert "Selected 2 events" in captured.out

    def test_select_with_dataframe(self, capsys: pytest.CaptureFixture[str]) -> None:
        df = pd.DataFrame({"id": ["e1", "e2", "e3"]})
        select(df)
        captured = capsys.readouterr()
        assert "Selected 3 events" in captured.out

    def test_play_prints(self, capsys: pytest.CaptureFixture[str]) -> None:
        play(["c1"])
        captured = capsys.readouterr()
        assert "Play 1 clips" in captured.out

    def test_playlist_prints(self, capsys: pytest.CaptureFixture[str]) -> None:
        playlist(["e1", "e2"], title="My Playlist")
        captured = capsys.readouterr()
        assert 'playlist "My Playlist"' in captured.out
