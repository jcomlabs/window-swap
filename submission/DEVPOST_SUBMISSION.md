# Devpost submission copy

## Project name

Window Swap

## Tagline

One spatial action to cycle stacked Windows apps.

## Category

Apps for Your Life

## Short description

Window Swap is a tiny local Windows tray utility for people who stack snapped
windows in the same screen region. Move the pointer into that region's
bottom-right corner and select Swap to bring the next matching window forward.
It replaces repeated Alt+Tab searches without changing Windows Snap layouts.

## Inspiration

Windows Snap is excellent until two or more applications occupy the same half or
quarter of the screen. At that point, switching becomes a search through Alt+Tab
or the taskbar. Window Swap keeps the user's spatial context: the corner of the
region becomes the switch point for the windows already stacked there.

## What it does

Window Swap runs in the Windows notification area. It inspects only visible
top-level window geometry. When the pointer reaches the bottom-right corner of a
window region, a compact Swap control appears. Selecting it brings the next
window with matching bounds to the foreground.

The tray icon pauses or resumes the behavior, and its menu can add or remove a
current-user Startup shortcut. The utility supports English and Portuguese,
requires no account or administrator rights, and contains no telemetry, network
client, or background service.

## How we built it

The project combines Python, Win32 APIs, Tk, and a Windows tray integration.
Pure geometry and ordering rules are separated from operating-system effects so
they can be tested deterministically. GitHub Actions validates Python 3.11,
3.12, and 3.13 on Windows and builds tagged one-file releases with a published
SHA-256 digest.

During Build Week, Codex helped turn an earlier prototype into a testable public
release. The qualifying work includes signed popup geometry for monitors left of
or above the primary display, duplicate-instance protection, privacy-conscious
diagnostics, expanded automated tests, release-workflow repairs, live Windows
testing, and a sanitized publication and release process.

I made the key product decisions: keep the utility local and focused, add no
runtime AI or telemetry, preserve the deliberate corner interaction, publish a
clean history, and favor daily reliability over additional features.

## Challenges

Desktop software crosses boundaries that unit tests cannot fully simulate. The
hardest parts were foreground activation across desktop and UWP applications,
physical-pixel geometry under Windows scaling, signed coordinates on monitors
positioned left of the primary display, and ensuring a packaged executable never
runs two competing tray instances.

The release pipeline exposed another subtle problem: the Windows Python launcher
could ignore the interpreter installed by the CI matrix. The workflow was changed
to invoke the setup-python interpreter directly and was revalidated across all
claimed versions.

## Accomplishments

- A working downloadable Windows utility, not only a source-code prototype.
- Fifteen passing deterministic and Windows integration tests.
- Real visual testing with desktop and UWP applications at 150% scaling.
- Correct negative-coordinate popup placement and duplicate-instance prevention.
- Public MIT-licensed source with pinned Actions, security guidance, provenance,
  secret scanning, push protection, and Dependabot security updates.
- A public release whose downloaded executable was digest-verified and executed
  after upload.

## What we learned

For a tiny desktop utility, product quality is mostly boundary quality: monitor
coordinates, DPI, foreground rules, process lifecycle, packaging, and privacy.
Codex was most useful when paired with evidence from the real machine and CI logs,
not when treated as a substitute for those checks.

## What's next

The immediate goal is feedback from more physical multi-monitor arrangements and
a second Windows machine. After that, the project can consider an optional dwell
delay and code signing without changing its local-first design.

## Built with

Python, pywin32, Tkinter, pystray, Pillow, pytest, PyInstaller, GitHub Actions,
Codex, and GPT-5.6.

## Links

- Repository: https://github.com/jcomlabs/window-swap
- Release: https://github.com/jcomlabs/window-swap/releases/tag/v1.1.0-alpha.1
- Build Week evidence: https://github.com/jcomlabs/window-swap/blob/submission/openai-build-week/BUILD_WEEK.md
- Demo video: `OWNER_TO_ADD_PUBLIC_YOUTUBE_URL`
- Prepared upload: `Downloads\Window-Swap-Build-Week-2026.mp4`
  (98 seconds, H.264/AAC, 1920×1080)
- `/feedback` session ID: `OWNER_TO_ADD_SESSION_ID`
