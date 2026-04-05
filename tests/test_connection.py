"""Tests for threader_python.connection."""

from __future__ import annotations

from pathlib import Path

import pytest

from threader_python.connection import (
    Connection,
    auto_connect,
    connect,
    disconnect,
    get_connection,
    is_connected,
)


class TestConnection:
    def test_open_and_close(self, threader_db: Path) -> None:
        conn = Connection()
        assert not conn.is_connected

        conn.open(str(threader_db))
        assert conn.is_connected
        assert conn.db_path == str(threader_db)

        conn.close()
        assert not conn.is_connected
        assert conn.db_path is None

    def test_open_nonexistent_file(self, tmp_path: Path) -> None:
        conn = Connection()
        with pytest.raises(FileNotFoundError, match="not found"):
            conn.open(str(tmp_path / "nonexistent.threader"))

    def test_get_conn_when_closed(self) -> None:
        conn = Connection()
        with pytest.raises(RuntimeError, match="No project connected"):
            conn.get_conn()

    def test_get_conn_returns_sqlite(self, threader_db: Path) -> None:
        conn = Connection()
        conn.open(str(threader_db))
        sqlite_conn = conn.get_conn()
        # Verify we can query
        cursor = sqlite_conn.execute("SELECT COUNT(*) FROM events")
        assert cursor.fetchone()[0] == 4
        conn.close()

    def test_read_only(self, threader_db: Path) -> None:
        conn = Connection()
        conn.open(str(threader_db))
        with pytest.raises(Exception):
            conn.get_conn().execute(
                "INSERT INTO teams (id, name, side) VALUES ('t3', 'Test', 'home')"
            )
        conn.close()


class TestModuleFunctions:
    def setup_method(self) -> None:
        disconnect()

    def teardown_method(self) -> None:
        disconnect()

    def test_connect_and_query(self, threader_db: Path) -> None:
        connect(str(threader_db))
        assert is_connected()

        conn = get_connection()
        cursor = conn.execute("SELECT COUNT(*) FROM players")
        assert cursor.fetchone()[0] == 3

    def test_disconnect(self, threader_db: Path) -> None:
        connect(str(threader_db))
        disconnect()
        assert not is_connected()

    def test_auto_connect(self, threader_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("THREADER_PROJECT_PATH", str(threader_db.parent))
        auto_connect()
        assert is_connected()

    def test_auto_connect_no_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("THREADER_PROJECT_PATH", raising=False)
        auto_connect()
        assert not is_connected()
