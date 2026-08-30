# Changelog

## 1.2.0-beta.1 - 2026-08-30

- Add a compact localized status and settings panel from the tray menu.
- Add configurable 0, 0.2, and 0.4 second trigger delays to reduce accidental activation.
- Show the matching-window count on the Swap button by default.
- Revalidate the target stack immediately before changing focus and add a short cooldown.
- Marshal tray actions onto the Tk UI thread instead of mutating Tk state from callbacks.
- Stop reading window titles and ignore DWM-cloaked and tool windows.
- Recognize and safely migrate the legacy `WindowSwapper.lnk` startup shortcut.
- Embed a W icon and Windows version metadata in packaged executables.

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
