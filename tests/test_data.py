"""Tests for threader_python.data."""

from __future__ import annotations

from pathlib import Path

from threader_python.connection import connect, disconnect
from threader_python.data import clips, events, match, players, teams, videos, whistle_sync


class TestDataAccess:
    def setup_method(self) -> None:
        disconnect()

    def teardown_method(self) -> None:
        disconnect()

    def _connect(self, threader_db: Path) -> None:
        connect(str(threader_db))

    # -- events() -------------------------------------------------------------

    def test_events_all(self, threader_db: Path) -> None:
        self._connect(threader_db)
        df = events()
        assert len(df) == 4
        assert "id" in df.columns
        assert "type" in df.columns

    def test_events_filter_type(self, threader_db: Path) -> None:
        self._connect(threader_db)
        df = events(type="pass")
        assert len(df) == 3
        assert all(df["type"] == "pass")

    def test_events_filter_player(self, threader_db: Path) -> None:
        self._connect(threader_db)
        df = events(player_id="p1")
        assert len(df) == 2

    def test_events_filter_team(self, threader_db: Path) -> None:
        self._connect(threader_db)
        df = events(team_id="t2")
        assert len(df) == 1
        assert df.iloc[0]["player_id"] == "p3"

    def test_events_filter_period(self, threader_db: Path) -> None:
        self._connect(threader_db)
        df = events(period="1H")
        assert len(df) == 3

    def test_events_filter_is_successful(self, threader_db: Path) -> None:
        self._connect(threader_db)
        df = events(is_successful=False)
        assert len(df) == 1
        assert df.iloc[0]["type"] == "shot"

    def test_events_combined_filters(self, threader_db: Path) -> None:
        self._connect(threader_db)
        df = events(type="pass", team_id="t1")
        assert len(df) == 2

    def test_events_boolean_conversion(self, threader_db: Path) -> None:
        self._connect(threader_db)
        df = events()
        assert df["is_successful"].dtype == bool

    def test_events_json_columns(self, threader_db: Path) -> None:
        self._connect(threader_db)
        df = events()
        # related_event_ids should be parsed from JSON string to list
        assert isinstance(df.iloc[0]["related_event_ids"], list)

    # -- players() ------------------------------------------------------------

    def test_players_all(self, threader_db: Path) -> None:
        self._connect(threader_db)
        df = players()
        assert len(df) == 3

    def test_players_filter_team(self, threader_db: Path) -> None:
        self._connect(threader_db)
        df = players(team_id="t1")
        assert len(df) == 2

    def test_players_boolean_fields(self, threader_db: Path) -> None:
        self._connect(threader_db)
        df = players()
        messi = df[df["name"] == "Lionel Messi"].iloc[0]
        assert messi["is_starter"] == True  # noqa: E712
        assert messi["has_played"] == True  # noqa: E712

    # -- teams() --------------------------------------------------------------

    def test_teams(self, threader_db: Path) -> None:
        self._connect(threader_db)
        df = teams()
        assert len(df) == 2
        sides = set(df["side"])
        assert sides == {"home", "away"}

    # -- clips() --------------------------------------------------------------

    def test_clips_all(self, threader_db: Path) -> None:
        self._connect(threader_db)
        df = clips()
        assert len(df) == 2
        assert "event_ids" in df.columns

    def test_clips_event_ids(self, threader_db: Path) -> None:
        self._connect(threader_db)
        df = clips()
        c1 = df[df["id"] == "c1"].iloc[0]
        assert c1["event_ids"] == ["e1"]

    def test_clips_tags_parsed(self, threader_db: Path) -> None:
        self._connect(threader_db)
        df = clips()
        c1 = df[df["id"] == "c1"].iloc[0]
        assert c1["tags"] == ["pass", "attack"]

    def test_clips_filter_video(self, threader_db: Path) -> None:
        self._connect(threader_db)
        df = clips(video_id="v1")
        assert len(df) == 2

        df_none = clips(video_id="nonexistent")
        assert len(df_none) == 0

    # -- match() --------------------------------------------------------------

    def test_match(self, threader_db: Path) -> None:
        self._connect(threader_db)
        m = match()
        assert m["competition_name"] == "La Liga"
        assert m["pitch_length"] == 105.0
        assert m["home_team_id"] == "t1"

    # -- videos() -------------------------------------------------------------

    def test_videos(self, threader_db: Path) -> None:
        self._connect(threader_db)
        df = videos()
        assert len(df) == 1
        assert df.iloc[0]["file_name"] == "match.mp4"

    # -- whistle_sync() -------------------------------------------------------

    def test_whistle_sync(self, threader_db: Path) -> None:
        self._connect(threader_db)
        df = whistle_sync()
        assert len(df) == 2

    def test_whistle_sync_filter_video(self, threader_db: Path) -> None:
        self._connect(threader_db)
        df = whistle_sync(video_id="v1")
        assert len(df) == 2

        df_none = whistle_sync(video_id="nonexistent")
        assert len(df_none) == 0
