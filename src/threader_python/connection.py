"""Project connection management for Threader .threader SQLite files."""

from __future__ import annotations

import glob
import os
import sqlite3
from pathlib import Path


class Connection:
    """Manages a read-only connection to a .threader project SQLite database."""

    def __init__(self) -> None:
        self.db_path: str | None = None
        self._conn: sqlite3.Connection | None = None

    @property
    def is_connected(self) -> bool:
        return self._conn is not None

    def open(self, path: str) -> None:
        """Open a connection to the given .threader file.

        Args:
            path: Absolute or relative path to a .threader SQLite file.

        Raises:
            FileNotFoundError: If the file does not exist.
            sqlite3.Error: If the file is not a valid SQLite database.
        """
        self.close()
        resolved = str(Path(path).resolve())
        if not os.path.isfile(resolved):
            raise FileNotFoundError(f"Project file not found: {resolved}")
        conn = sqlite3.connect(f"file:{resolved}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        self._conn = conn
        self.db_path = resolved

    def close(self) -> None:
        """Close the current connection if open."""
        if self._conn is not None:
            try:
                self._conn.close()
            except sqlite3.Error:
                pass
            self._conn = None
            self.db_path = None

    def get_conn(self) -> sqlite3.Connection:
        """Return the active SQLite connection.

        Raises:
            RuntimeError: If no project is connected.
        """
        if self._conn is None:
            raise RuntimeError(
                "No project connected. "
                "Use threader_python.connect('/path/to/project.threader') first, "
                "or run inside a Threader notebook (auto-connects via THREADER_PROJECT_PATH)."
            )
        return self._conn


# Global singleton
_current = Connection()


def connect(path: str) -> None:
    """Connect to a .threader project file.

    Args:
        path: Path to a .threader SQLite file.
    """
    _current.open(path)


def auto_connect() -> None:
    """Auto-connect using the THREADER_PROJECT_PATH environment variable.

    Threader sets this variable when launching the Jupyter kernel.
    The project directory is scanned for a .threader file.
    """
    project_dir = os.environ.get("THREADER_PROJECT_PATH")
    if not project_dir:
        return

    # The .threader file lives in the parent of the project directory,
    # or could be found by scanning the project dir itself.
    candidates = glob.glob(os.path.join(project_dir, "*.threader"))
    if not candidates:
        # Try parent directory — THREADER_PROJECT_PATH is dirname of the .threader file
        parent = os.path.dirname(project_dir)
        candidates = glob.glob(os.path.join(parent, "*.threader"))

    if candidates:
        _current.open(candidates[0])


def disconnect() -> None:
    """Close the current project connection."""
    _current.close()


def get_connection() -> sqlite3.Connection:
    """Return the active SQLite connection.

    Raises:
        RuntimeError: If no project is connected.
    """
    return _current.get_conn()


def is_connected() -> bool:
    """Check whether a project is currently connected."""
    return _current.is_connected
