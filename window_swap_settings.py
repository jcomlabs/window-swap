"""Small, privacy-preserving settings store for Window Swap."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

DEFAULT_TRIGGER_DELAY_MS = 0
ALLOWED_TRIGGER_DELAYS_MS = (0, 200, 400)
SETTINGS_SCHEMA_VERSION = 2


@dataclass(frozen=True, slots=True)
class AppSettings:
    """User preferences that never contain window or account information."""

    schema_version: int = SETTINGS_SCHEMA_VERSION
    trigger_delay_ms: int = DEFAULT_TRIGGER_DELAY_MS
    show_stack_count: bool = True

    @classmethod
    def from_mapping(cls, values: object) -> AppSettings:
        if not isinstance(values, dict):
            return cls()

        schema_version = values.get("schema_version", 1)
        delay = values.get("trigger_delay_ms", DEFAULT_TRIGGER_DELAY_MS)
        count = values.get("show_stack_count", True)
        if (
            isinstance(schema_version, bool)
            or not isinstance(schema_version, int)
            or schema_version < SETTINGS_SCHEMA_VERSION
        ):
            # The unreleased first beta wrote a 200 ms default that changed the
            # established instant gesture. Treat that file as pre-migration.
            delay = DEFAULT_TRIGGER_DELAY_MS
        if isinstance(delay, bool) or delay not in ALLOWED_TRIGGER_DELAYS_MS:
            delay = DEFAULT_TRIGGER_DELAY_MS
        if not isinstance(count, bool):
            count = True
        return cls(trigger_delay_ms=delay, show_stack_count=count)


def settings_path(local_app_data: str | None = None) -> Path:
    base = local_app_data or os.environ.get("LOCALAPPDATA")
    if not base:
        raise RuntimeError("LOCALAPPDATA is unavailable; cannot store settings")
    return Path(base) / "JCOM Labs" / "Window Swap" / "settings.json"


def load_settings(path: Path | None = None) -> AppSettings:
    try:
        target = path or settings_path()
        values = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, RuntimeError, UnicodeError, json.JSONDecodeError):
        return AppSettings()
    return AppSettings.from_mapping(values)


def save_settings(settings: AppSettings, path: Path | None = None) -> None:
    target = path or settings_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(asdict(settings), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)
