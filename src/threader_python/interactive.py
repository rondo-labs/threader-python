"""Make Plotly figures interactive with Threader click-to-navigate.

Injects click handlers into Plotly HTML output so that clicking data points
triggers Threader actions (video seek, player navigation, event filtering)
via the iframe postMessage bridge.
"""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pandas as pd

# Action types that map to Electron-side dispatcher routes
VALID_ACTIONS = frozenset({"seek_event", "navigate_player", "filter_events"})

# Columns needed per action type
_ACTION_COLUMNS: dict[str, list[str]] = {
    "seek_event": ["id", "video_time_ms"],
    "navigate_player": ["id"],
    "filter_events": ["id"],
}


def interactive(
    fig: Any,
    on_click: str = "seek_event",
    *,
    id_col: str = "id",
    video_time_col: str = "video_time_ms",
    player_id_col: str = "player_id",
    df: pd.DataFrame | None = None,
    trace_config: dict[int, str | None] | None = None,
) -> None:
    """Display a Plotly figure with Threader click-to-navigate support.

    This replaces ``fig.show()`` — it renders the figure with an injected
    click handler that sends ``postMessage`` events to the Threader app.

    Args:
        fig: A Plotly Figure object (``plotly.graph_objects.Figure``).
        on_click: Default click action for all traces. One of:
            - ``"seek_event"``: click seeks video to the event's timestamp
            - ``"navigate_player"``: click opens player detail panel
            - ``"filter_events"``: click filters clips panel by event IDs
        id_col: Column name for the primary ID in ``df``.
        video_time_col: Column name for video timestamp (ms) in ``df``.
            Used when ``on_click="seek_event"``.
        player_id_col: Column name for player ID in ``df``.
            Used when ``on_click="navigate_player"`` and ``id_col`` doesn't
            point to the player ID directly.
        df: Source DataFrame. When provided, customdata is automatically
            injected into each trace. When omitted, existing trace customdata
            must already contain ``__threader__``-tagged dicts.
        trace_config: Per-trace action override. Maps trace index to an action
            string or ``None`` (disable clicks for that trace). Traces not
            listed use ``on_click`` as the default.

    Raises:
        ImportError: If plotly is not installed.
        ValueError: If ``on_click`` is not a valid action type, or if
            ``df`` row count doesn't match trace data point count.

    Example::

        import threader_python as tp
        import plotly.express as px

        events = tp.events(type="pass")
        fig = px.scatter(events, x="x", y="y", color="is_successful")
        tp.interactive(fig, on_click="seek_event", df=events)
    """
    try:
        import plotly.io as pio
    except ImportError:
        raise ImportError(
            "plotly is required for interactive charts. "
            "Install it with: pip install plotly"
        ) from None

    if on_click not in VALID_ACTIONS:
        raise ValueError(f"on_click must be one of {sorted(VALID_ACTIONS)}, got {on_click!r}")

    if trace_config:
        for idx, action in trace_config.items():
            if action is not None and action not in VALID_ACTIONS:
                raise ValueError(
                    f"trace_config[{idx}] must be one of {sorted(VALID_ACTIONS)} or None, "
                    f"got {action!r}"
                )

    # Inject customdata into traces
    if df is not None:
        _inject_customdata(fig, df, on_click, id_col, video_time_col, player_id_col, trace_config)

    # Build per-trace action map for the JS handler
    trace_actions = _build_trace_actions(fig, on_click, trace_config)

    # Generate HTML with click handler.
    # Use "cdn" so plotly embeds the version-matched CDN URL, then swap the
    # full bundle for plotly-basic (no WebGL modules) to avoid WebGL context
    # errors in Electron iframe environments. Also strip the SRI integrity
    # hash (it's for the full bundle, not basic) and crossorigin attribute.
    html = pio.to_html(fig, include_plotlyjs="cdn", full_html=False)
    html = html.replace("/plotly-", "/plotly-basic-", 1)
    html = re.sub(r'\s+integrity="[^"]*"', "", html, count=1)
    html = re.sub(r'\s+crossorigin="[^"]*"', "", html, count=1)
    handler_js = _build_click_handler_js(trace_actions)
    html += handler_js

    # Display via IPython
    display_fn = _get_display()
    if display_fn:
        display_fn({"text/html": html}, raw=True)
    else:
        print("[threader] interactive() requires an IPython/Jupyter environment to display.")


def _inject_customdata(
    fig: Any,
    df: Any,
    on_click: str,
    id_col: str,
    video_time_col: str,
    player_id_col: str,
    trace_config: dict[int, str | None] | None,
) -> None:
    """Inject __threader__-tagged customdata into each trace.

    Handles multi-trace figures (e.g. when plotly express splits by color)
    by matching each trace's data back to the correct DataFrame subset.
    """
    import numpy as np

    for i, trace in enumerate(fig.data):
        action = on_click
        if trace_config and i in trace_config:
            action = trace_config[i]
        if action is None:
            continue

        n_points = _trace_length(trace)
        if n_points == 0:
            continue

        # Determine which DataFrame rows correspond to this trace
        trace_df = _match_trace_to_df(df, trace, n_points)

        # Preserve existing customdata
        existing = trace.customdata

        # Build threader customdata for each point.
        # Keep the original customdata array intact (plotly hover templates
        # reference items by index) and append the threader dict at the end.
        new_customdata = []
        for j in range(n_points):
            row = trace_df.iloc[j]
            entry = _build_entry(row, action, id_col, video_time_col, player_id_col)

            if existing is not None and j < len(existing):
                user_val = existing[j]
                if isinstance(user_val, np.ndarray):
                    user_val = user_val.tolist()
                # Keep original array elements, append threader dict
                if isinstance(user_val, list):
                    new_customdata.append(user_val + [entry])
                else:
                    new_customdata.append([user_val, entry])
            else:
                new_customdata.append([entry])

        trace.customdata = new_customdata


def _build_entry(
    row: Any,
    action: str,
    id_col: str,
    video_time_col: str,
    player_id_col: str,
) -> dict[str, Any]:
    """Build a single __threader__-tagged customdata dict for one data point."""
    entry: dict[str, Any] = {"__threader__": True, "action": action}

    if action == "seek_event":
        entry["event_id"] = str(row[id_col])
        if video_time_col in row.index:
            val = row[video_time_col]
            if val is not None and not _is_nan(val):
                entry["video_time_ms"] = int(val)

    elif action == "navigate_player":
        # Prefer resolved_player_id (Threader UUID) over provider's numeric ID
        if "resolved_player_id" in row.index and row["resolved_player_id"]:
            entry["player_id"] = str(row["resolved_player_id"])
        else:
            col = player_id_col if player_id_col in row.index else id_col
            entry["player_id"] = str(row[col])

    elif action == "filter_events":
        entry["event_ids"] = [str(row[id_col])]

    return entry


def _match_trace_to_df(df: Any, trace: Any, n_points: int) -> Any:
    """Find the DataFrame rows that correspond to a plotly trace.

    When plotly express splits data by color/symbol/etc., each trace
    contains a subset of the original DataFrame. This function finds
    the matching subset by checking trace.name against string columns.
    """
    if len(df) == n_points:
        return df

    # plotly express sets trace.name to the group value (e.g. "Real Madrid")
    trace_name = getattr(trace, "name", None)
    if trace_name is not None:
        # Search string/object columns for a match
        for col in df.select_dtypes(include=["object", "string", "category", "bool"]).columns:
            group = df[df[col].astype(str) == str(trace_name)]
            if len(group) == n_points:
                return group.reset_index(drop=True)

    raise ValueError(
        f"DataFrame has {len(df)} rows but trace has {n_points} data points. "
        f"Could not match trace '{trace_name}' to a DataFrame subset. "
        f"Ensure the DataFrame passed to interactive() is the same one used to create the figure."
    )


def _build_trace_actions(
    fig: Any,
    on_click: str,
    trace_config: dict[int, str | None] | None,
) -> dict[int, str | None]:
    """Build a mapping of trace index → action for the JS handler."""
    actions: dict[int, str | None] = {}
    for i in range(len(fig.data)):
        if trace_config and i in trace_config:
            actions[i] = trace_config[i]
        else:
            actions[i] = on_click
    return actions


def _build_click_handler_js(trace_actions: dict[int, str | None]) -> str:
    """Generate the <script> tag that handles plotly_click events."""
    actions_json = json.dumps(trace_actions)

    return f"""
<script>
(function(){{
  var traceActions = {actions_json};

  function attach() {{
    var plot = document.querySelector('.plotly-graph-div');
    if (!plot || !plot.on) {{
      // Plotly.newPlot() is async in v3 — retry until the plot is ready
      setTimeout(attach, 100);
      return;
    }}
    plot.style.cursor = 'pointer';

    plot.on('plotly_click', function(data) {{
      if (!data || !data.points || !data.points.length) return;
      var pt = data.points[0];
      var cd = pt.customdata;

      // customdata is an array — find the __threader__ dict (appended at the end)
      if (Array.isArray(cd)) {{
        for (var i = cd.length - 1; i >= 0; i--) {{
          if (cd[i] && typeof cd[i] === 'object' && !Array.isArray(cd[i]) && cd[i].__threader__) {{
            cd = cd[i];
            break;
          }}
        }}
      }}

      if (!cd || typeof cd !== 'object' || !cd.__threader__) return;

      // Check if this trace has clicks enabled
      var traceIdx = String(pt.curveNumber);
      if (traceActions.hasOwnProperty(traceIdx) && traceActions[traceIdx] === null) return;

      var msg = {{ type: 'threader-chart-click', action: cd.action }};
      if (cd.event_id) msg.eventId = cd.event_id;
      if (cd.video_time_ms != null) msg.videoTimeMs = Number(cd.video_time_ms);
      if (cd.player_id) msg.playerId = cd.player_id;
      if (cd.event_ids) msg.eventIds = cd.event_ids;

      console.log('[threader-iframe] posting chart-click:', JSON.stringify(msg));
      window.parent.postMessage(msg, '*');
    }});
  }}
  attach();
}})();
</script>"""


def _trace_length(trace: Any) -> int:
    """Get the number of data points in a plotly trace."""
    for attr in ("x", "y", "lat", "lon", "values", "labels"):
        data = getattr(trace, attr, None)
        if data is not None:
            return len(data)
    return 0


def _is_nan(val: Any) -> bool:
    """Check if a value is NaN (works with numpy and plain floats)."""
    try:
        import math
        return math.isnan(float(val))
    except (TypeError, ValueError):
        return False


def _get_display():
    """Try to import IPython.display.display. Returns None if unavailable."""
    try:
        from IPython.display import display
        return display
    except ImportError:
        return None
