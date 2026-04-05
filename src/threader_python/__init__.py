"""threader-python — Football video annotation data access and Threader bridge.

Quick start inside a Threader notebook::

    import threader_python as tp

    events = tp.events(type="pass")
    tp.select(events.head(10))

Quick start in standalone Python / Jupyter::

    import threader_python as tp

    tp.connect("/path/to/match.threader")
    events = tp.events(type="pass")
"""

from __future__ import annotations

import os as _os

from threader_python.bridge import play, playlist, select
from threader_python.connection import connect, disconnect, is_connected
from threader_python.data import clips, events, match, players, teams, videos, whistle_sync

__all__ = [
    # Connection
    "connect",
    "disconnect",
    "is_connected",
    # Data access
    "events",
    "players",
    "teams",
    "clips",
    "match",
    "videos",
    "whistle_sync",
    # Bridge actions
    "select",
    "play",
    "playlist",
]

# Auto-connect when running inside a Threader embedded notebook.
if _os.environ.get("THREADER_PROJECT_PATH"):
    from threader_python.connection import auto_connect

    auto_connect()
