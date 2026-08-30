# Window Swap

Window Swap is a small, local Windows tray utility for people who stack multiple
snapped windows in the same screen region. Move the pointer into that region's
bottom-right corner and Window Swap offers a compact **Swap** button that brings
the next matching window forward.

It replaces repeated `Alt+Tab` searches with one spatial action while leaving the
Windows taskbar and Snap layouts unchanged.

> **Status:** `1.2.0-beta.1` is a test-ready beta. Windows 11 is the supported
> platform. Geometry and settings rules are tested, but desktop behavior can still
> vary with applications, display scaling, and multi-monitor layouts.

## Features

- cycles through visible top-level windows occupying the same screen region;
- per-monitor DPI awareness for consistent physical-pixel geometry;
- tray toggle and click-to-enable/disable action;
- optional current-user Startup-folder shortcut;
- a small status/settings panel with an accidental-trigger delay;
- an optional stack count on the Swap button;
- English UI by default and Portuguese UI on Portuguese Windows;
- no network client, telemetry, account, administrator rights, or background service.

Set `WINDOW_SWAP_LANGUAGE=en` or `WINDOW_SWAP_LANGUAGE=pt` before launch to override
the detected UI language.

For opt-in troubleshooting, set `WINDOW_SWAP_LOG` to a writable file path before
launch. Diagnostics contain internal errors but never intentionally log window
titles or contents.

## Install from source

```powershell
git clone https://github.com/jcomlabs/window-swap.git
cd window-swap
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -e .
window-swap
```

For a release executable, download the asset and matching SHA-256 digest from the
[Releases page](https://github.com/jcomlabs/window-swap/releases). Release
executables are never stored in the source tree.

## Use

1. Open two applications and snap both into the same half or quarter of the screen.
2. Move the pointer into the bottom-right corner of the visible window.
3. Select **Swap** to bring the next matching window forward.
4. Click the tray icon to pause or resume Window Swap.

Right-click the **W** tray icon for startup control, status/settings, and exit.
The balanced 0.2-second trigger delay is the default; choose instant or deliberate
behavior in **Status and settings**. Preferences are stored locally under
`%LOCALAPPDATA%\JCOM Labs\Window Swap` and contain no window titles or contents.

The startup option creates or removes only
`%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\WindowSwap.lnk`.

## Development

```powershell
py -m pip install -e ".[dev]"
py -m pytest
py -m compileall -q window_swapper.py window_swap_core.py
```

Build a local executable:

```powershell
py -m pip install -e ".[build]"
python build_release.py
```

Pure geometry and ordering rules live in `window_swap_core.py`; preference
validation lives in `window_swap_settings.py`. Win32 enumeration, focus changes,
Tk, and tray integration remain in `window_swapper.py`.

For a safe manual check without using personal application windows, run
`python tools/manual_smoke.py`. It opens two disposable windows in the same region
so the corner trigger and focus cycle can be tested without exposing desktop data.
See [ROADMAP.md](ROADMAP.md) for the deliberately small next-feature set.

## Security and privacy

Window Swap inspects visible window handles and rectangles and asks Windows to
activate an existing window. It does not read window titles or contents. No software
can honestly claim to have no vulnerabilities;
see [SECURITY.md](SECURITY.md) for the supported disclosure process and trust boundary.

## Portuguese summary

O Window Swap é um pequeno utilitário local para Windows. Quando duas ou mais janelas
ocupam a mesma zona do ecrã, coloca o ponteiro no canto inferior direito e seleciona
**Trocar** para trazer a janela seguinte para a frente. A interface fica automaticamente
em português num Windows configurado em português e pode ser forçada com
`WINDOW_SWAP_LANGUAGE=pt`.

## License

[MIT](LICENSE) © 2026 JC-OM

Packaged builds include third-party libraries under their own licenses; see
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
