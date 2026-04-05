# threader-python

Python SDK for [Threader](https://github.com/rondo-labs/threader) — read football video annotation data and bridge notebook analysis back to the Threader desktop app.

## Installation

```bash
pip install threader-python
```

Or with visualization extras:

```bash
pip install "threader-python[viz]"
```

## Quick Start

### Inside a Threader Notebook

When running inside Threader's built-in notebook, the connection is automatic:

```python
import threader_python as tp

# Query data — returns pandas DataFrames
events = tp.events(type="pass")
players = tp.players()
teams = tp.teams()

# Filter passes between two players
pair = events[(events.player_id == "p1") & (events.receiver_id == "p2")]

# Send selection to Threader — Clips panel filters automatically
tp.select(pair)

# Or create a playlist directly
tp.playlist(pair, title="Messi → Alba passes")
```

### Standalone (Jupyter Lab, VS Code, etc.)

Point to a `.threader` project file manually:

```python
import threader_python as tp

tp.connect("/path/to/match.threader")

events = tp.events(type="shot")
print(events[["player_id", "x", "y", "is_successful"]])
```

Data access works fully in standalone mode. Bridge actions (`select`, `play`, `playlist`) print a summary instead of triggering UI interactions.

## API Reference

### Connection

| Function | Description |
|----------|-------------|
| `tp.connect(path)` | Connect to a `.threader` project file |
| `tp.disconnect()` | Close the current connection |
| `tp.is_connected()` | Check connection status |

### Data Access

All data functions return a `pandas.DataFrame` (except `match()` which returns a `dict`).

| Function | Description | Filters |
|----------|-------------|---------|
| `tp.events()` | Annotated events | `type`, `sub_type`, `player_id`, `team_id`, `period`, `is_successful` |
| `tp.players()` | Player roster | `team_id` |
| `tp.teams()` | Teams | — |
| `tp.clips()` | Video clips (includes linked `event_ids`) | `video_id` |
| `tp.match()` | Match metadata (returns `dict`) | — |
| `tp.videos()` | Video file info | — |
| `tp.whistle_sync()` | Whistle sync points | `video_id` |

### Bridge Actions (Threader Integration)

These functions communicate with the Threader desktop app when running inside a Threader notebook:

| Function | Description |
|----------|-------------|
| `tp.select(events_or_ids)` | Highlight events in Threader, filter Clips panel |
| `tp.play(clips_or_ids)` | Play clips in the video player |
| `tp.playlist(events_or_ids, title=...)` | Create a playlist from events |

All bridge functions accept either a DataFrame (with an `id` column) or a list of ID strings.

## How It Works

- **Data access**: Reads directly from the `.threader` SQLite file (read-only, WAL-safe for concurrent access)
- **Bridge actions**: Emit a custom MIME type (`application/x-threader+json`) via IPython's `display()`, which the Threader app's notebook renderer picks up and dispatches to the UI

## Development

```bash
# Clone and install
git clone https://github.com/rondo-labs/threader-python.git
cd threader-python
uv sync

# Run tests
uv run pytest

# Lint
uv run ruff check src/ tests/
```

## License

MIT
