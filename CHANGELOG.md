# Changelog

## 1.2.0-beta.2 - 2026-08-31

- Add a compact localized status and settings panel from the tray menu.
- Add optional 0.2 and 0.4 second trigger delays while preserving instant activation by default.
- Show the matching-window count on the Swap button by default.
- Preserve repeated-click cycling while using the live window z-order for each click.
- Marshal tray actions onto the Tk UI thread instead of mutating Tk state from callbacks.
- Keep window titles local and never log or persist them.
- Recognize and safely migrate the legacy `WindowSwapper.lnk` startup shortcut.
- Embed a W icon and Windows version metadata in packaged executables.
- Restore the established instant, repeated-click cycle after an internal beta candidate changed that gesture.

## 1.1.0-alpha.1 - 2026-07-18

- Add an explicit enabled/disabled tray state and icon-click toggle.
- Use a Startup-folder shortcut instead of the registry.
- Extract deterministic geometry rules and add automated tests.
- Add package metadata, an MIT license, security guidance, and Windows CI.
- Publish tagged executables only through GitHub Releases with a SHA-256 digest.
- Make the published source and contributor documentation English-first.
- Prevent duplicate instances from competing for the tray icon and hot corner.
- Keep the Swap overlay correctly positioned on monitors left of or above the primary display.
- Add opt-in diagnostics that do not intentionally record window titles or contents.

## 1.0.0 - 2026-06-02

- Initial Windows tray prototype and executable.
