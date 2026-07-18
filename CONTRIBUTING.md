# Contributing

Window Swap intentionally stays small, local, and Windows-specific.

1. Create a focused branch.
2. Install the development dependencies with `py -m pip install -e ".[dev]"`.
3. Run `py -m pytest` and `py -m compileall -q window_swapper.py window_swap_core.py`.
4. Keep geometry and ordering decisions in `window_swap_core.py` so they remain
   deterministic and testable without controlling a real desktop.
5. Avoid network access, telemetry, privilege elevation, arbitrary command
   execution, or logging window titles.

Bug reports should include the Windows version, display scaling, monitor layout,
and reproduction steps, but never private window titles or screenshots containing
sensitive information.
