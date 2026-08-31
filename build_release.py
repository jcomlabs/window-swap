"""Build the Windows executable with product icon and version metadata."""

from __future__ import annotations

from pathlib import Path

import PyInstaller.__main__

from window_swapper import create_icon_image

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build"
DIST = ROOT / "dist"
ICON = BUILD / "window-swap.ico"
VERSION = BUILD / "window-swap-version.txt"

VERSION_INFO = """VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 2, 0, 3),
    prodvers=(1, 2, 0, 3),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable('040904B0', [
        StringStruct('CompanyName', 'JCOM Labs'),
        StringStruct('FileDescription', 'Window Swap'),
        StringStruct('FileVersion', '1.2.0-beta.3'),
        StringStruct('InternalName', 'WindowSwap'),
        StringStruct('LegalCopyright', 'Copyright 2026 JC-OM'),
        StringStruct('OriginalFilename', 'window-swap.exe'),
        StringStruct('ProductName', 'Window Swap'),
        StringStruct('ProductVersion', '1.2.0-beta.3')
      ])
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""


def main() -> None:
    BUILD.mkdir(exist_ok=True)
    create_icon_image(True).save(
        ICON,
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64)],
    )
    VERSION.write_text(VERSION_INFO, encoding="utf-8", newline="\n")
    PyInstaller.__main__.run(
        [
            "--noconsole",
            "--onefile",
            "--clean",
            "--distpath",
            str(DIST),
            "--workpath",
            str(BUILD / "pyinstaller"),
            "--specpath",
            str(BUILD),
            "--name",
            "window-swap",
            "--icon",
            str(ICON),
            "--version-file",
            str(VERSION),
            str(ROOT / "window_swapper.py"),
        ]
    )
    if not (DIST / "window-swap.exe").is_file():
        raise RuntimeError("PyInstaller did not create dist/window-swap.exe")


if __name__ == "__main__":
    main()
