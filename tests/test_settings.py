from __future__ import annotations

import json
from pathlib import Path

from window_swap_settings import (
    AppSettings,
    load_settings,
    save_settings,
    settings_path,
)


def test_settings_path_stays_in_product_directory() -> None:
    assert settings_path(r"C:\Local").as_posix().endswith(
        "JCOM Labs/Window Swap/settings.json"
    )


def test_invalid_settings_fall_back_to_safe_defaults() -> None:
    assert AppSettings.from_mapping({"trigger_delay_ms": 999, "show_stack_count": "yes"}) == AppSettings()
    assert AppSettings.from_mapping(["not", "a", "mapping"]) == AppSettings()


def test_settings_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    expected = AppSettings(trigger_delay_ms=400, show_stack_count=False)
    save_settings(expected, path)
    assert load_settings(path) == expected
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "show_stack_count": False,
        "trigger_delay_ms": 400,
    }


def test_corrupt_settings_are_ignored(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text("{broken", encoding="utf-8")
    assert load_settings(path) == AppSettings()
