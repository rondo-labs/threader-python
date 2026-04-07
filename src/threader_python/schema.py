"""SQLite schema definitions for .threader project files.

These mirror the migrations in the Threader Electron app (database.ts).
Only tables relevant to data analysis are included here.
"""

# -- Events ------------------------------------------------------------------

EVENTS_TABLE = "events"
EVENTS_COLUMNS = [
    "id",
    "video_id",
    "video_time_ms",
    "status",
    "time",
    "period",
    "type",
    "sub_type",
    "is_successful",
    "outcome_type",
    "player_id",
    "team_id",
    "receiver_id",
    "receiver_time",
    "receiver_video_time_ms",
    "x",
    "y",
    "x_end",
    "y_end",
    "body_part",
    "related_event_ids",
    "match_clock",
    "frame_id",
    "frame_id_end",
    "created_at",
    "updated_at",
]

# -- Imported Events (external data: StatsBomb, Opta, etc.) -------------------

IMPORTED_EVENTS_TABLE = "imported_events"
IMPORTED_EVENTS_COLUMNS = [
    "id",
    "import_session_id",
    "video_id",
    "provider_event_id",
    "video_time_ms",
    "period",
    "match_clock",
    "type",
    "sub_type",
    "provider_type",
    "provider_sub_type",
    "is_successful",
    "outcome_type",
    "player_id",
    "player_name",
    "team_id",
    "team_name",
    "x",
    "y",
    "x_end",
    "y_end",
    "body_part",
    "raw_data",
    "created_at",
    "resolved_player_id",
]

# -- Import Sessions ----------------------------------------------------------

IMPORT_SESSIONS_TABLE = "import_sessions"
IMPORT_SESSIONS_COLUMNS = [
    "id",
    "video_id",
    "provider",
    "file_name",
    "event_count",
    "frame_count",
    "visible",
    "color",
    "created_at",
]

# -- Players ------------------------------------------------------------------

PLAYERS_TABLE = "players"
PLAYERS_COLUMNS = [
    "id",
    "team_id",
    "name",
    "number",
    "position",
    "sort_order",
    "first_name",
    "last_name",
    "is_starter",
    "has_played",
    "is_captain",
    "position_group",
    "date_of_birth",
    "height",
    "preferred_foot",
]

# -- Teams --------------------------------------------------------------------

TEAMS_TABLE = "teams"
TEAMS_COLUMNS = [
    "id",
    "name",
    "short_name",
    "color_primary",
    "color_secondary",
    "side",
    "created_at",
]

# -- Clips --------------------------------------------------------------------

CLIPS_TABLE = "clips"
CLIPS_COLUMNS = [
    "id",
    "video_id",
    "title",
    "start_ms",
    "end_ms",
    "tags",
    "rating",
    "notes",
    "sort_order",
    "created_at",
    "updated_at",
]

CLIP_EVENTS_TABLE = "clip_events"

# -- Playlists ----------------------------------------------------------------

PLAYLISTS_TABLE = "playlists"
PLAYLISTS_COLUMNS = [
    "id",
    "title",
    "description",
    "created_at",
    "updated_at",
]

PLAYLIST_CLIPS_TABLE = "playlist_clips"

# -- Videos -------------------------------------------------------------------

VIDEOS_TABLE = "videos"
VIDEOS_COLUMNS = [
    "id",
    "path",
    "file_name",
    "fps",
    "width",
    "height",
    "duration_ms",
    "recording_type",
    "operation_type",
    "perspective",
    "start_time",
    "created_at",
]

# -- Matches ------------------------------------------------------------------

MATCHES_TABLE = "matches"
MATCHES_COLUMNS = [
    "id",
    "competition_id",
    "competition_name",
    "competition_format",
    "competition_type",
    "season_id",
    "season_name",
    "kickoff_time",
    "stadium_id",
    "stadium_name",
    "pitch_length",
    "pitch_width",
    "turf",
    "is_neutral",
    "has_extratime",
    "has_shootout",
    "result_final",
    "result_first_half",
    "result_second_half",
    "winning_team_id",
    "home_team_id",
    "away_team_id",
    "cdf_version",
    "created_at",
    "updated_at",
]

# -- Whistle Sync -------------------------------------------------------------

WHISTLE_SYNC_TABLE = "whistle_sync"
WHISTLE_SYNC_COLUMNS = [
    "id",
    "video_id",
    "period",
    "sub_type",
    "video_time_ms",
    "utc_time",
    "sort_order",
    "created_at",
]

# -- Boolean columns (stored as INTEGER 0/1 in SQLite) -----------------------

BOOLEAN_COLUMNS = frozenset({
    "is_successful",
    "is_starter",
    "has_played",
    "is_captain",
    "is_neutral",
    "has_extratime",
    "has_shootout",
})
