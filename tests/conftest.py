"""Shared test fixtures for threader-python tests."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest


def _run_migrations(db: sqlite3.Connection) -> None:
    """Apply the core Threader schema migrations to a test database."""
    db.executescript("""
        -- Migration 001: Core schema
        CREATE TABLE IF NOT EXISTS project_meta (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS videos (
            id          TEXT PRIMARY KEY,
            path        TEXT NOT NULL,
            file_name   TEXT NOT NULL,
            fps         REAL,
            width       INTEGER,
            height      INTEGER,
            duration_ms INTEGER,
            recording_type TEXT,
            operation_type TEXT,
            perspective    TEXT,
            start_time     TEXT,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS whistle_sync (
            id            TEXT PRIMARY KEY,
            video_id      TEXT NOT NULL REFERENCES videos(id),
            period        TEXT NOT NULL,
            sub_type      TEXT NOT NULL,
            video_time_ms INTEGER NOT NULL,
            utc_time      TEXT,
            sort_order    INTEGER NOT NULL,
            created_at    TEXT NOT NULL DEFAULT (datetime('now'))
        );

        -- Migration 002: Events + Players
        CREATE TABLE IF NOT EXISTS players (
            id              TEXT PRIMARY KEY,
            team_id         TEXT NOT NULL DEFAULT '',
            name            TEXT NOT NULL,
            number          INTEGER,
            position        TEXT,
            sort_order      INTEGER NOT NULL DEFAULT 0,
            first_name      TEXT,
            last_name       TEXT,
            is_starter      INTEGER NOT NULL DEFAULT 0,
            has_played      INTEGER NOT NULL DEFAULT 0,
            is_captain      INTEGER NOT NULL DEFAULT 0,
            position_group  TEXT,
            date_of_birth   TEXT,
            height          REAL,
            preferred_foot  TEXT
        );

        CREATE TABLE IF NOT EXISTS events (
            id                      TEXT PRIMARY KEY,
            video_id                TEXT NOT NULL REFERENCES videos(id),
            video_time_ms           INTEGER NOT NULL,
            status                  TEXT NOT NULL DEFAULT 'CONFIRMED',
            time                    TEXT,
            period                  TEXT,
            type                    TEXT NOT NULL,
            sub_type                TEXT,
            is_successful           INTEGER NOT NULL DEFAULT 1,
            outcome_type            TEXT NOT NULL DEFAULT '',
            player_id               TEXT NOT NULL DEFAULT '',
            team_id                 TEXT NOT NULL DEFAULT '',
            receiver_id             TEXT,
            receiver_time           TEXT,
            receiver_video_time_ms  INTEGER,
            x                       REAL NOT NULL DEFAULT 0,
            y                       REAL NOT NULL DEFAULT 0,
            x_end                   REAL NOT NULL DEFAULT 0,
            y_end                   REAL NOT NULL DEFAULT 0,
            body_part               TEXT NOT NULL DEFAULT 'right_foot',
            related_event_ids       TEXT NOT NULL DEFAULT '[]',
            match_clock             TEXT,
            frame_id                INTEGER,
            frame_id_end            INTEGER,
            created_at              TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at              TEXT NOT NULL DEFAULT (datetime('now'))
        );

        -- Migration 003: Match Context
        CREATE TABLE IF NOT EXISTS teams (
            id               TEXT PRIMARY KEY,
            name             TEXT NOT NULL,
            short_name       TEXT,
            color_primary    TEXT,
            color_secondary  TEXT,
            side             TEXT NOT NULL,
            created_at       TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS matches (
            id                  TEXT PRIMARY KEY,
            competition_id      TEXT,
            competition_name    TEXT,
            competition_format  TEXT,
            competition_type    TEXT,
            season_id           TEXT,
            season_name         TEXT,
            kickoff_time        TEXT,
            stadium_id          TEXT,
            stadium_name        TEXT,
            pitch_length        REAL NOT NULL DEFAULT 105,
            pitch_width         REAL NOT NULL DEFAULT 68,
            turf                TEXT DEFAULT 'grass',
            is_neutral          INTEGER NOT NULL DEFAULT 0,
            has_extratime       INTEGER NOT NULL DEFAULT 0,
            has_shootout        INTEGER NOT NULL DEFAULT 0,
            result_final        TEXT,
            result_first_half   TEXT,
            result_second_half  TEXT,
            winning_team_id     TEXT,
            home_team_id        TEXT,
            away_team_id        TEXT,
            cdf_version         TEXT NOT NULL DEFAULT '0.2.3',
            created_at          TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
        );

        -- Migration 004: Clips
        CREATE TABLE IF NOT EXISTS clips (
            id          TEXT PRIMARY KEY,
            video_id    TEXT NOT NULL REFERENCES videos(id),
            title       TEXT NOT NULL DEFAULT '',
            start_ms    INTEGER NOT NULL,
            end_ms      INTEGER NOT NULL,
            tags        TEXT NOT NULL DEFAULT '[]',
            rating      INTEGER,
            notes       TEXT,
            sort_order  INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS clip_events (
            clip_id   TEXT NOT NULL REFERENCES clips(id),
            event_id  TEXT NOT NULL REFERENCES events(id),
            PRIMARY KEY (clip_id, event_id)
        );

        CREATE TABLE IF NOT EXISTS playlists (
            id          TEXT PRIMARY KEY,
            title       TEXT NOT NULL,
            description TEXT,
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS playlist_clips (
            playlist_id TEXT NOT NULL REFERENCES playlists(id),
            clip_id     TEXT NOT NULL REFERENCES clips(id),
            sort_order  INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (playlist_id, clip_id)
        );

        -- Migration 008: Import sessions + imported events
        CREATE TABLE IF NOT EXISTS import_sessions (
            id          TEXT PRIMARY KEY,
            video_id    TEXT NOT NULL REFERENCES videos(id),
            provider    TEXT NOT NULL,
            file_name   TEXT NOT NULL,
            event_count INTEGER NOT NULL DEFAULT 0,
            frame_count INTEGER NOT NULL DEFAULT 0,
            visible     INTEGER NOT NULL DEFAULT 1,
            color       TEXT NOT NULL DEFAULT '#58A6FF',
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS imported_events (
            id                  TEXT PRIMARY KEY,
            import_session_id   TEXT NOT NULL REFERENCES import_sessions(id) ON DELETE CASCADE,
            video_id            TEXT NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
            provider_event_id   TEXT,
            video_time_ms       INTEGER NOT NULL,
            period              TEXT,
            match_clock         TEXT,
            type                TEXT NOT NULL,
            sub_type            TEXT,
            provider_type       TEXT NOT NULL,
            provider_sub_type   TEXT,
            is_successful       INTEGER NOT NULL DEFAULT 1,
            outcome_type        TEXT NOT NULL DEFAULT '',
            player_id           TEXT NOT NULL DEFAULT '',
            player_name         TEXT,
            team_id             TEXT NOT NULL DEFAULT '',
            team_name           TEXT,
            x                   REAL NOT NULL DEFAULT 0,
            y                   REAL NOT NULL DEFAULT 0,
            x_end               REAL NOT NULL DEFAULT 0,
            y_end               REAL NOT NULL DEFAULT 0,
            body_part           TEXT NOT NULL DEFAULT 'right_foot',
            raw_data            TEXT,
            created_at          TEXT NOT NULL DEFAULT (datetime('now')),
            resolved_player_id  TEXT
        );
    """)


def _seed_data(db: sqlite3.Connection) -> None:
    """Insert sample football data into the test database."""
    db.executescript("""
        INSERT INTO videos (id, path, file_name, fps, width, height, duration_ms)
        VALUES ('v1', '/videos/match.mp4', 'match.mp4', 25.0, 1920, 1080, 5400000);

        INSERT INTO teams (id, name, short_name, side)
        VALUES ('t1', 'FC Barcelona', 'BAR', 'home'),
               ('t2', 'Real Madrid', 'RMA', 'away');

        INSERT INTO matches (id, competition_name, home_team_id, away_team_id, pitch_length, pitch_width)
        VALUES ('m1', 'La Liga', 't1', 't2', 105.0, 68.0);

        INSERT INTO players (id, team_id, name, number, position, is_starter, has_played)
        VALUES ('p1', 't1', 'Lionel Messi', 10, 'RW', 1, 1),
               ('p2', 't1', 'Jordi Alba', 18, 'LB', 1, 1),
               ('p3', 't2', 'Karim Benzema', 9, 'CF', 1, 1);

        INSERT INTO events (id, video_id, video_time_ms, period, type, sub_type, is_successful, player_id, team_id, receiver_id, x, y, x_end, y_end)
        VALUES ('e1', 'v1', 10000, '1H', 'pass', 'open_play', 1, 'p1', 't1', 'p2', 30.0, 10.0, 40.0, -20.0),
               ('e2', 'v1', 25000, '1H', 'pass', 'open_play', 1, 'p2', 't1', 'p1', 40.0, -20.0, 35.0, 5.0),
               ('e3', 'v1', 50000, '1H', 'shot', 'open_play', 0, 'p1', 't1', NULL, 45.0, 2.0, 52.5, 0.0),
               ('e4', 'v1', 80000, '2H', 'pass', 'open_play', 1, 'p3', 't2', NULL, -10.0, 5.0, 0.0, 15.0);

        INSERT INTO clips (id, video_id, title, start_ms, end_ms, tags, rating)
        VALUES ('c1', 'v1', 'Messi pass to Alba', 7000, 12000, '["pass", "attack"]', 4),
               ('c2', 'v1', 'Messi shot', 47000, 52000, '["shot"]', 3);

        INSERT INTO clip_events (clip_id, event_id)
        VALUES ('c1', 'e1'),
               ('c2', 'e3');

        INSERT INTO whistle_sync (id, video_id, period, sub_type, video_time_ms, sort_order)
        VALUES ('w1', 'v1', '1H', 'start', 0, 0),
               ('w2', 'v1', '1H', 'end', 2700000, 1);

        INSERT INTO import_sessions (id, video_id, provider, file_name, event_count)
        VALUES ('is1', 'v1', 'statsbomb', 'match_events.csv', 3);

        INSERT INTO imported_events (id, import_session_id, video_id, video_time_ms, period, match_clock, type, sub_type, provider_type, provider_sub_type, is_successful, outcome_type, player_id, player_name, team_id, team_name, x, y, x_end, y_end, body_part)
        VALUES ('ie1', 'is1', 'v1', 12000, '1H', '00:12', 'pass', 'open_play', 'Pass', 'Open Play', 1, 'complete', 'p1', 'Lionel Messi', 't1', 'FC Barcelona', 30.0, 10.0, 40.0, -20.0, 'right_foot'),
               ('ie2', 'is1', 'v1', 28000, '1H', '00:28', 'pass', 'open_play', 'Pass', 'Open Play', 1, 'complete', 'p2', 'Jordi Alba', 't1', 'FC Barcelona', 40.0, -20.0, 35.0, 5.0, 'left_foot'),
               ('ie3', 'is1', 'v1', 55000, '1H', '00:55', 'shot', 'open_play', 'Shot', 'Open Play', 0, 'saved', 'p1', 'Lionel Messi', 't1', 'FC Barcelona', 45.0, 2.0, 52.5, 0.0, 'left_foot');
    """)


@pytest.fixture
def threader_db(tmp_path: Path) -> Path:
    """Create a temporary .threader SQLite file with sample data.

    Returns the path to the .threader file.
    """
    db_path = tmp_path / "test_match.threader"
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    _run_migrations(conn)
    _seed_data(conn)
    conn.commit()
    conn.close()
    return db_path
