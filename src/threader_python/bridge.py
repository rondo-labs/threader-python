"""Threader UI bridge actions.

These functions communicate with the Threader Electron app to trigger
UI interactions such as filtering the clips panel, playing clips,
or creating playlists from notebook analysis results.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from threader_python._display import emit_action

if TYPE_CHECKING:
    import pandas as pd


def _extract_ids(events_or_ids, id_column: str = "id") -> list[str]:
    """Extract a list of string IDs from a DataFrame or iterable.

    Args:
        events_or_ids: A pandas DataFrame with an ``id_column``, or an
            iterable of string IDs.
        id_column: Column name to extract IDs from when given a DataFrame.

    Returns:
        List of string IDs.

    Raises:
        ValueError: If the DataFrame does not have the expected column.
    """
    try:
        import pandas as pd

        if isinstance(events_or_ids, pd.DataFrame):
            if id_column not in events_or_ids.columns:
                raise ValueError(
                    f"DataFrame must have an '{id_column}' column. "
                    f"Available columns: {list(events_or_ids.columns)}"
                )
            return events_or_ids[id_column].astype(str).tolist()
    except ImportError:
        pass

    return [str(x) for x in events_or_ids]


def select(events_or_ids: pd.DataFrame | list[str]) -> None:
    """Select events in the Threader UI.

    Inside Threader: highlights the specified events and filters the
    Clips panel to show only clips linked to these events.

    Outside Threader: prints the selected event IDs.

    Args:
        events_or_ids: A DataFrame with an ``id`` column, or a list of
            event ID strings.
    """
    ids = _extract_ids(events_or_ids)
    emit_action("select", {"eventIds": ids})


def play(clips_or_ids: pd.DataFrame | list[str]) -> None:
    """Play clips in the Threader video player.

    Inside Threader: starts playback of the specified clips in sequence.

    Outside Threader: prints the clip IDs.

    Args:
        clips_or_ids: A DataFrame with an ``id`` column, or a list of
            clip ID strings.
    """
    ids = _extract_ids(clips_or_ids)
    emit_action("play", {"clipIds": ids})


def playlist(
    events_or_ids: pd.DataFrame | list[str],
    *,
    title: str = "Notebook Playlist",
) -> None:
    """Create a playlist from events in Threader.

    Inside Threader: auto-creates a clip for each event (using the standard
    ±3s/2s padding) and assembles them into a named playlist.

    Outside Threader: prints a summary of what would be created.

    Args:
        events_or_ids: A DataFrame with an ``id`` column, or a list of
            event ID strings.
        title: Name for the new playlist.
    """
    ids = _extract_ids(events_or_ids)
    emit_action("playlist", {"eventIds": ids, "title": title})
