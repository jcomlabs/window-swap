# Judge testing instructions

## Supported platform

Windows 11, x64.

## Fast path: test the release without rebuilding

1. Open the
   [v1.1.0-alpha.1 release](https://github.com/jcomlabs/window-swap/releases/tag/v1.1.0-alpha.1).
2. Download `window-swap.exe` and `window-swap.exe.sha256`.
3. In PowerShell, from the download directory, run:

   ```powershell
   (Get-FileHash .\window-swap.exe -Algorithm SHA256).Hash.ToLower()
   Get-Content .\window-swap.exe.sha256
   ```

   Both values should contain:

   ```text
   9ba91d9847aefb76efd72b6b0d4384fea2e17c0383f8c424ef29ea62663668cf
   ```

4. Run `window-swap.exe`. It is unsigned, so Windows may show a SmartScreen
   warning. No installation, account, administrator rights, or network access is
   required.
5. Snap two ordinary applications to the same half or quarter of the screen.
6. Move the pointer into the bottom-right corner of that region.
7. Select **Swap**. The next window with the same bounds should come forward.

## Tray behavior

- Click the `W` notification-area icon to pause or resume the corner trigger.
- Right-click it to toggle **Active**, toggle **Start with Windows**, or exit.
- The Startup option affects only the current user's Startup-folder shortcut.

## Expected limitations

- The executable is unsigned.
- Windows 11 is the supported platform.
- Some elevated or protected applications may reject foreground activation.
- Geometry can vary with unusual application chrome or monitor arrangements.

## Source verification

```powershell
git clone https://github.com/jcomlabs/window-swap.git
cd window-swap
git switch submission/openai-build-week
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -e ".[dev]"
py -m pytest
py -m compileall -q window_swapper.py window_swap_core.py
```

The project intentionally has no test account, API key, server, cloud dependency,
or sample user data.
