"""Data access layer — read-only queries against .threader SQLite databases."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

from threader_python.connection import get_connection
from threader_python.schema import (
    BOOLEAN_COLUMNS,
    CLIP_EVENTS_TABLE,
    CLIPS_COLUMNS,
    CLIPS_TABLE,
    EVENTS_COLUMNS,
    EVENTS_TABLE,
    IMPORT_SESSIONS_COLUMNS,
    IMPORT_SESSIONS_TABLE,
    IMPORTED_EVENTS_COLUMNS,
    IMPORTED_EVENTS_TABLE,
    MATCHES_COLUMNS,
    MATCHES_TABLE,
    PLAYERS_COLUMNS,
    PLAYERS_TABLE,
    TEAMS_COLUMNS,
    TEAMS_TABLE,
    VIDEOS_COLUMNS,
    VIDEOS_TABLE,
    WHISTLE_SYNC_COLUMNS,
    WHISTLE_SYNC_TABLE,
)


def _query(
    table: str,
    columns: list[str],
    filters: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Execute a filtered SELECT and return a DataFrame.

    Args:
        table: Table name.
        columns: Columns to select.
        filters: Optional column-value pairs for WHERE clauses.
                 None values are skipped.
    """
    conn = get_connection()
    col_list = ", ".join(columns)
    sql = f"SELECT {col_list} FROM {table}"  # noqa: S608 — table/cols are from schema constants

    params: list[Any] = []
    where_parts: list[str] = []

    if filters:
        for col, val in filters.items():
            if val is None:
                continue
            # Convert Python booleans to SQLite integers
            if col in BOOLEAN_COLUMNS and isinstance(val, bool):
                val = int(val)
            where_parts.append(f"{col} = ?")
            params.append(val)

    if where_parts:
        sql += " WHERE " + " AND ".join(where_parts)

    df = pd.read_sql_query(sql, conn, params=params)

    # Convert SQLite integer booleans back to Python booleans
    for col in BOOLEAN_COLUMNS:
        if col in df.columns:
            df[col] = df[col].astype(bool)

    # Parse JSON columns
    if "tags" in df.columns:
        df["tags"] = df["tags"].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
    if "related_event_ids" in df.columns:
        df["related_event_ids"] = df["related_event_ids"].apply(
            lambda x: json.loads(x) if isinstance(x, str) else x
        )

    return df


def events(
    *,
    type: str | None = None,
    sub_type: str | None = None,
    player_id: str | None = None,
    team_id: str | None = None,
    period: str | None = None,
    is_successful: bool | None = None,
) -> pd.DataFrame:
    """Query annotated events.

    All filter parameters are optional. When omitted, no filtering is applied
    for that dimension.

    Returns:
        DataFrame with one row per event.
    """
    return _query(
        EVENTS_TABLE,
        EVENTS_COLUMNS,
        filters={
            "type": type,
            "sub_type": sub_type,
            "player_id": player_id,
            "team_id": team_id,
            "period": period,
            "is_successful": is_successful,
        },
    )


def players(*, team_id: str | None = None) -> pd.DataFrame:
    """Query players, optionally filtered by team.

    Returns:
        DataFrame with one row per player.
    """
    return _query(PLAYERS_TABLE, PLAYERS_COLUMNS, filters={"team_id": team_id})


def teams() -> pd.DataFrame:
    """Query all teams in the project.

    Returns:
        DataFrame with one row per team.
    """
    return _query(TEAMS_TABLE, TEAMS_COLUMNS)


def clips(*, video_id: str | None = None) -> pd.DataFrame:
    """Query clips with their linked event IDs.

    Each clip row includes an ``event_ids`` column containing a list of
    event IDs linked via the clip_events join table.

    Returns:
        DataFrame with one row per clip.
    """
    conn = get_connection()
    col_list = ", ".join(f"c.{col}" for col in CLIPS_COLUMNS)
    sql = f"""
        SELECT {col_list},
               GROUP_CONCAT(ce.event_id) AS _event_ids_csv
        FROM {CLIPS_TABLE} c
        LEFT JOIN {CLIP_EVENTS_TABLE} ce ON ce.clip_id = c.id
    """
    params: list[Any] = []
    if video_id is not None:
        sql += " WHERE c.video_id = ?"
        params.append(video_id)
    sql += " GROUP BY c.id"

    df = pd.read_sql_query(sql, conn, params=params)

    # Convert CSV of event IDs to a list
    df["event_ids"] = df["_event_ids_csv"].apply(
        lambda x: x.split(",") if isinstance(x, str) and x else []
    )
    df = df.drop(columns=["_event_ids_csv"])

    # Parse JSON tags
    if "tags" in df.columns:
        df["tags"] = df["tags"].apply(lambda x: json.loads(x) if isinstance(x, str) else x)

    return df


def match() -> dict[str, Any]:
    """Return match metadata as a dictionary.

    Returns the first (and typically only) match record. Returns an empty
    dict if no match has been configured.
    """
    df = _query(MATCHES_TABLE, MATCHES_COLUMNS)
    if df.empty:
        return {}
    return df.iloc[0].to_dict()


def videos() -> pd.DataFrame:
    """Query video file metadata.

    Returns:
        DataFrame with one row per video.
    """
    return _query(VIDEOS_TABLE, VIDEOS_COLUMNS)


def whistle_sync(*, video_id: str | None = None) -> pd.DataFrame:
    """Query whistle synchronization points.

    Returns:
        DataFrame with one row per whistle event, ordered by sort_order.
    """
    return _query(WHISTLE_SYNC_TABLE, WHISTLE_SYNC_COLUMNS, filters={"video_id": video_id})


def imported_events(
    *,
    type: str | None = None,
    sub_type: str | None = None,
    player_id: str | None = None,
    team_id: str | None = None,
    period: str | None = None,
    is_successful: bool | None = None,
    session_id: str | None = None,
) -> pd.DataFrame:
    """Query externally imported events (StatsBomb, Opta, etc.).

    These are events imported from third-party data providers, as opposed
    to manually annotated events from ``events()``. Imported events include
    inline ``player_name`` and ``team_name`` columns.

    Args:
        type: Filter by CDF event type (e.g. ``"pass"``, ``"shot"``).
        sub_type: Filter by CDF event sub-type.
        player_id: Filter by player ID.
        team_id: Filter by team ID.
        period: Filter by match period (e.g. ``"1H"``, ``"2H"``).
        is_successful: Filter by success flag.
        session_id: Filter by import session ID.

    Returns:
        DataFrame with one row per imported event.
    """
    return _query(
        IMPORTED_EVENTS_TABLE,
        IMPORTED_EVENTS_COLUMNS,
        filters={
            "type": type,
            "sub_type": sub_type,
            "player_id": player_id,
            "team_id": team_id,
            "period": period,
            "is_successful": is_successful,
            "import_session_id": session_id,
        },
    )


def import_sessions() -> pd.DataFrame:
    """Query import sessions (one per imported data file).

    Returns:
        DataFrame with one row per import session.
    """
    return _query(IMPORT_SESSIONS_TABLE, IMPORT_SESSIONS_COLUMNS)
