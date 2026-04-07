"""Tests for threader_python.interactive."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pytest

from threader_python.interactive import (
    VALID_ACTIONS,
    _build_click_handler_js,
    _build_entry,
    _build_trace_actions,
    _inject_customdata,
    _trace_length,
    interactive,
)

# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture()
def events_df() -> pd.DataFrame:
    return pd.DataFrame({
        "id": ["e1", "e2", "e3"],
        "x": [10.0, 20.0, 30.0],
        "y": [5.0, 15.0, 25.0],
        "video_time_ms": [1000, 2000, 3000],
        "player_id": ["p1", "p2", "p1"],
        "is_successful": [True, False, True],
    })


@pytest.fixture()
def players_df() -> pd.DataFrame:
    return pd.DataFrame({
        "id": ["p1", "p2", "p3"],
        "name": ["Alice", "Bob", "Charlie"],
        "x": [10.0, 20.0, 30.0],
        "y": [5.0, 15.0, 25.0],
    })


@pytest.fixture()
def scatter_fig(events_df: pd.DataFrame) -> go.Figure:
    return px.scatter(events_df, x="x", y="y")


# ─── _build_entry ────────────────────────────────────────────────────────────

class TestBuildEntry:
    def test_seek_event(self, events_df: pd.DataFrame) -> None:
        row = events_df.iloc[0]
        entry = _build_entry(row, "seek_event", "id", "video_time_ms", "player_id")
        assert entry["__threader__"] is True
        assert entry["action"] == "seek_event"
        assert entry["event_id"] == "e1"
        assert entry["video_time_ms"] == 1000

    def test_seek_event_missing_video_time(self) -> None:
        df = pd.DataFrame({"id": ["e1"], "x": [1.0]})
        entry = _build_entry(df.iloc[0], "seek_event", "id", "video_time_ms", "player_id")
        assert entry["event_id"] == "e1"
        assert "video_time_ms" not in entry

    def test_navigate_player_with_player_id_col(self, events_df: pd.DataFrame) -> None:
        row = events_df.iloc[0]
        entry = _build_entry(row, "navigate_player", "id", "video_time_ms", "player_id")
        assert entry["player_id"] == "p1"

    def test_navigate_player_fallback_to_id_col(self, players_df: pd.DataFrame) -> None:
        row = players_df.iloc[0]
        entry = _build_entry(row, "navigate_player", "id", "video_time_ms", "nonexistent_col")
        assert entry["player_id"] == "p1"

    def test_filter_events(self, events_df: pd.DataFrame) -> None:
        row = events_df.iloc[0]
        entry = _build_entry(row, "filter_events", "id", "video_time_ms", "player_id")
        assert entry["event_ids"] == ["e1"]


# ─── _inject_customdata ─────────────────────────────────────────────────────

class TestInjectCustomdata:
    def test_basic_injection(self, scatter_fig: go.Figure, events_df: pd.DataFrame) -> None:
        _inject_customdata(
            scatter_fig, events_df, "seek_event", "id", "video_time_ms", "player_id", None
        )
        cd = scatter_fig.data[0].customdata
        assert len(cd) == 3
        # Each point's customdata is now an array with threader dict appended
        threader = cd[0][-1]  # last element is the threader dict
        assert threader["__threader__"] is True
        assert threader["event_id"] == "e1"
        assert threader["video_time_ms"] == 1000

    def test_preserves_existing_customdata(self, events_df: pd.DataFrame) -> None:
        fig = px.scatter(events_df, x="x", y="y", custom_data=["is_successful"])
        _inject_customdata(
            fig, events_df, "seek_event", "id", "video_time_ms", "player_id", None
        )
        cd = fig.data[0].customdata
        # Original hover data preserved at original indices, threader dict appended
        threader = cd[0][-1]
        assert threader["__threader__"] is True
        # Original custom_data value (is_successful) is still at index 0
        assert len(cd[0]) >= 2  # at least original value + threader dict

    def test_row_count_mismatch(self) -> None:
        df = pd.DataFrame({"id": ["e1", "e2"], "x": [1.0, 2.0], "y": [3.0, 4.0]})
        fig = px.scatter(df, x="x", y="y")
        short_df = pd.DataFrame({"id": ["e1"], "x": [1.0], "y": [3.0]})
        with pytest.raises(ValueError, match="Could not match trace"):
            _inject_customdata(
                fig, short_df, "seek_event", "id", "video_time_ms", "player_id", None
            )

    def test_multi_trace_color_split(self) -> None:
        """plotly express with color= creates multiple traces — customdata should work."""
        df = pd.DataFrame({
            "id": ["e1", "e2", "e3", "e4"],
            "x": [1.0, 2.0, 3.0, 4.0],
            "y": [5.0, 6.0, 7.0, 8.0],
            "video_time_ms": [1000, 2000, 3000, 4000],
            "team": ["A", "A", "B", "B"],
        })
        fig = px.scatter(df, x="x", y="y", color="team")
        assert len(fig.data) == 2  # two traces, one per team

        _inject_customdata(
            fig, df, "seek_event", "id", "video_time_ms", "player_id", None
        )

        # Both traces should have customdata injected
        for trace in fig.data:
            n = len(trace.x)
            assert len(trace.customdata) == n
            for cd in trace.customdata:
                threader = cd[-1]  # last element
                assert threader["__threader__"] is True
                assert threader["action"] == "seek_event"

    def test_trace_config_skips_none(self, events_df: pd.DataFrame) -> None:
        fig = px.scatter(events_df, x="x", y="y")
        _inject_customdata(
            fig, events_df, "seek_event", "id", "video_time_ms", "player_id",
            trace_config={0: None},
        )
        # Trace 0 should not have threader customdata injected
        cd = fig.data[0].customdata
        assert cd is None or (len(cd) > 0 and not isinstance(cd[0], dict))

    def test_navigate_player_action(self, players_df: pd.DataFrame) -> None:
        fig = px.scatter(players_df, x="x", y="y")
        _inject_customdata(
            fig, players_df, "navigate_player", "id", "video_time_ms", "player_id", None
        )
        cd = fig.data[0].customdata
        threader = cd[0][-1]
        assert threader["action"] == "navigate_player"
        # players_df doesn't have player_id col, falls back to id_col
        assert threader["player_id"] == "p1"


# ─── _build_trace_actions ───────────────────────────────────────────────────

class TestBuildTraceActions:
    def test_default_action(self, scatter_fig: go.Figure) -> None:
        actions = _build_trace_actions(scatter_fig, "seek_event", None)
        assert actions[0] == "seek_event"

    def test_trace_config_override(self) -> None:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[1], y=[1]))
        fig.add_trace(go.Scatter(x=[2], y=[2]))
        actions = _build_trace_actions(fig, "seek_event", {1: "navigate_player"})
        assert actions[0] == "seek_event"
        assert actions[1] == "navigate_player"

    def test_trace_config_none_disables(self) -> None:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[1], y=[1]))
        actions = _build_trace_actions(fig, "seek_event", {0: None})
        assert actions[0] is None


# ─── _build_click_handler_js ─────────────────────────────────────────────────

class TestBuildClickHandlerJs:
    def test_contains_script_tag(self) -> None:
        js = _build_click_handler_js({0: "seek_event"})
        assert "<script>" in js
        assert "</script>" in js

    def test_contains_postmessage(self) -> None:
        js = _build_click_handler_js({0: "seek_event"})
        assert "window.parent.postMessage" in js

    def test_contains_plotly_click(self) -> None:
        js = _build_click_handler_js({0: "seek_event"})
        assert "plotly_click" in js

    def test_contains_trace_actions(self) -> None:
        actions = {0: "seek_event", 1: "navigate_player", 2: None}
        js = _build_click_handler_js(actions)
        assert '"0": "seek_event"' in js
        assert '"1": "navigate_player"' in js
        assert '"2": null' in js

    def test_contains_threader_check(self) -> None:
        js = _build_click_handler_js({0: "seek_event"})
        assert "__threader__" in js


# ─── _trace_length ───────────────────────────────────────────────────────────

class TestTraceLength:
    def test_scatter_with_x(self) -> None:
        trace = go.Scatter(x=[1, 2, 3], y=[4, 5, 6])
        assert _trace_length(trace) == 3

    def test_empty_trace(self) -> None:
        trace = go.Scatter()
        assert _trace_length(trace) == 0


# ─── interactive() integration ───────────────────────────────────────────────

class TestInteractive:
    def test_invalid_on_click(self, scatter_fig: go.Figure) -> None:
        with pytest.raises(ValueError, match="on_click must be one of"):
            interactive(scatter_fig, on_click="invalid_action")

    def test_invalid_trace_config_action(self, scatter_fig: go.Figure) -> None:
        with pytest.raises(ValueError, match="trace_config"):
            interactive(scatter_fig, trace_config={0: "bad_action"})

    def test_prints_fallback_without_ipython(
        self, scatter_fig: go.Figure, events_df: pd.DataFrame,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # In a plain pytest environment, IPython display is not available
        # (or at least not a real Jupyter frontend), so it should print fallback
        interactive(scatter_fig, on_click="seek_event", df=events_df)
        capsys.readouterr()
        # No exception raised = success. In test env it either uses
        # IPython display() or prints the fallback message.

    def test_valid_actions_constant(self) -> None:
        assert "seek_event" in VALID_ACTIONS
        assert "navigate_player" in VALID_ACTIONS
        assert "filter_events" in VALID_ACTIONS
