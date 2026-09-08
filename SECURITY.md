# Security policy

Window Swap is a local Windows desktop utility. It enumerates visible windows,
reads their geometry, changes foreground-window ordering, and can create or
remove a shortcut in the current user's Startup folder. It does not need
administrator privileges or network access.

## Data handled by the app

- Window handles, styles, rectangles and titles are read in memory to identify
  eligible windows. Window contents and the clipboard are not captured.
- Preferences contain only a schema version, trigger delay and stack-count
  setting. They are stored in the current user's local app-data directory.
- The app has no account, telemetry, network client, automatic updater or
  credential store. It neither scans personal files nor uploads desktop data.
- File diagnostics are off by default. If `WINDOW_SWAP_LOG` is explicitly set,
  logs contain internal errors, version and counts, not window titles. Python
  tracebacks can contain local paths; review diagnostic logs before sharing them.

## Distribution

Executables are currently unsigned. Windows may display a reputation warning;
the published SHA-256 checks file integrity, not a publisher signature. Obtain
downloads from the canonical GitHub repository and check the matching digest.
Dependency versions and hashes are locked for releases. A known-vulnerability
scan and code review cannot establish the absence of unknown vulnerabilities.

## Reporting

Please report a suspected vulnerability privately through GitHub's security
advisory flow. Do not include passwords, tokens, personal window titles, or
other sensitive desktop data in a public issue.

Only the latest release receives security fixes. Release executables should be
downloaded from this repository's GitHub Releases page and verified against the
published SHA-256 digest.
