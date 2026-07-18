# OpenAI Build Week 2026

Window Swap is entered in **Apps for Your Life** as a small Windows productivity
utility built and hardened with Codex. It replaces repeated `Alt+Tab` searches
between stacked snapped windows with one deliberate spatial action.

## Existing project and eligible extension

Window Swap began as a private Windows prototype before the Build Week submission
period. That prototype already demonstrated the basic interaction: detect the
bottom-right corner of a visible window, show a Swap control, cycle matching
windows, and provide a tray menu.

The submission is the meaningfully extended `1.1.0-alpha.1` release created on
July 18, 2026. Judges should evaluate the work below, not the earlier prototype.

| Before the submission period | Added during the submission period |
| --- | --- |
| Basic Win32 window cycling | Deterministic geometry and ordering helpers with automated tests |
| Corner-triggered Swap control | Correct signed popup geometry on monitors left of or above the primary display |
| Tray toggle and Startup option | A per-session mutex that prevents competing duplicate instances |
| Local Windows executable | Reproducible CI and tag-driven release packaging on supported Python versions |
| Prototype-level error handling | Opt-in diagnostics that do not intentionally record window titles or contents |
| Private prototype history | Sanitized public root history, provenance notices, security policy, and privacy audit |

The focused hardening commit is
[`879e4e3`](https://github.com/jcomlabs/window-swap/commit/879e4e39d7c136a525296ff9e95bbe19b50bf868).
The final release commit is
[`7ad9b2d`](https://github.com/jcomlabs/window-swap/commit/7ad9b2d44a6235ffe0e2054de0872b5f4146538e).

## Collaboration with Codex and GPT-5.6

Codex was used as an implementation and verification partner throughout the
Build Week extension. It helped:

- inspect the existing Win32 behavior and preserve the useful interaction;
- separate pure geometry and ordering logic from Windows integration code;
- identify and fix negative-monitor coordinate handling;
- add duplicate-instance protection and privacy-conscious diagnostics;
- write deterministic unit and Windows integration tests;
- exercise the real executable with snapped desktop and UWP applications;
- diagnose a release-workflow interpreter bug from GitHub Actions logs;
- audit public history, tracked files, release assets, and documentation for
  secrets or private desktop material;
- download the published artifact, verify its SHA-256 digest, execute it, and
  replace the daily-use local installation.

The owner made the product decisions: preserve a tiny local-first utility, keep
the corner interaction intentional, add no telemetry or cloud dependency, retain
English and Portuguese UI, publish a clean history instead of unsafe legacy
history, and prioritize reliability over feature expansion.

Before submission, the owner will provide the required `/feedback` session ID
and confirm that the qualifying Codex session used GPT-5.6. This repository does
not claim that model provenance on its own.

## Reproduce and test

The fastest judge path is the prebuilt Windows executable:

1. Download `window-swap.exe` and `window-swap.exe.sha256` from the
   [`v1.1.0-alpha.1` release](https://github.com/jcomlabs/window-swap/releases/tag/v1.1.0-alpha.1).
2. Verify the SHA-256 digest.
3. Run the executable on Windows 11; no installer, account, administrator rights,
   or network connection is required.
4. Snap two applications into the same half or quarter of the display.
5. Move the pointer into the bottom-right corner and select **Swap**.

For source verification:

```powershell
py -m pip install -e ".[dev]"
py -m pytest
py -m compileall -q window_swapper.py window_swap_core.py
```

## Evidence

- Public repository: <https://github.com/jcomlabs/window-swap>
- Verified release: <https://github.com/jcomlabs/window-swap/releases/tag/v1.1.0-alpha.1>
- Green Windows CI: <https://github.com/jcomlabs/window-swap/actions/runs/29640461157>
- Release workflow: <https://github.com/jcomlabs/window-swap/actions/runs/29640495878>
- Published executable SHA-256:
  `9ba91d9847aefb76efd72b6b0d4384fea2e17c0383f8c424ef29ea62663668cf`

## Honest limitations

- Windows 11 is the supported platform.
- The release executable is unsigned and may trigger a SmartScreen warning.
- Desktop behavior can vary across applications, display scaling, and monitor
  layouts.
- A physical multi-monitor test was not available during the final pass; signed
  negative-coordinate behavior is covered deterministically, while the release
  was exercised on the available physical display.
- Window Swap contains no runtime AI and makes no network calls. GPT-5.6 and
  Codex were development tools for the Build Week extension, not product runtime
  dependencies.
