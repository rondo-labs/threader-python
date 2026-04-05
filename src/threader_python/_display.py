"""IPython display helpers for Threader bridge actions.

Handles environment detection and MIME type output for communicating
with the Threader Electron app via the Jupyter kernel protocol.
"""

from __future__ import annotations

import os
from typing import Any

MIME_TYPE = "application/x-threader+json"


def is_threader_env() -> bool:
    """Check if running inside a Threader embedded notebook."""
    return bool(os.environ.get("THREADER_PROJECT_PATH"))


def _get_ipython_display():
    """Try to import IPython.display.display. Returns None if unavailable."""
    try:
        from IPython.display import display  # type: ignore[import-untyped]

        return display
    except ImportError:
        return None


def emit_action(action: str, payload: dict[str, Any]) -> None:
    """Send a bridge action to Threader.

    Inside a Threader notebook (IPython + THREADER_PROJECT_PATH), this emits
    a ``display_data`` message with the custom MIME type that CellOutput.tsx
    picks up and dispatches to the bridge store.

    Outside Threader (standalone Jupyter, plain Python), this prints a
    human-readable summary so the call never errors.

    Args:
        action: Action name (e.g. "select", "play", "playlist").
        payload: Action-specific data dict.
    """
    message = {"action": action, **payload}
    display_fn = _get_ipython_display()

    if display_fn and is_threader_env():
        # Emit custom MIME type through the Jupyter kernel protocol.
        # CellOutput.tsx detects this and dispatches to notebook-bridge-store.
        display_fn({MIME_TYPE: message}, raw=True)
    else:
        # Fallback: print a summary for non-Threader environments.
        _print_fallback(action, payload)


def _print_fallback(action: str, payload: dict[str, Any]) -> None:
    """Print a human-readable summary of the bridge action."""
    if action == "select":
        ids = payload.get("eventIds", [])
        print(f"[threader] Selected {len(ids)} events: {ids[:5]}{'...' if len(ids) > 5 else ''}")
    elif action == "play":
        ids = payload.get("clipIds", [])
        print(f"[threader] Play {len(ids)} clips: {ids[:5]}{'...' if len(ids) > 5 else ''}")
    elif action == "playlist":
        title = payload.get("title", "Untitled")
        ids = payload.get("eventIds", [])
        print(f'[threader] Create playlist "{title}" from {len(ids)} events')
    else:
        print(f"[threader] {action}: {payload}")
