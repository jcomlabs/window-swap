# Third-party notices

Window Swap is MIT-licensed, but its packaged executable includes third-party
Python libraries under their own licenses. Those licenses continue to govern
their respective components.

| Component | Purpose | License | Source |
|---|---|---|---|
| Pillow | Tray icon image creation | MIT-CMU | <https://github.com/python-pillow/Pillow> |
| pystray | Windows system-tray integration | GNU LGPL v3 | <https://github.com/moses-palmer/pystray> |
| pywin32 | Win32 and COM integration | Python Software Foundation License | <https://github.com/mhammond/pywin32> |
| six | Python compatibility dependency of pystray | MIT | <https://github.com/benjaminp/six> |

The exact resolved versions, package sources, and download hashes for a build
are recorded in `uv.lock`. Release builds install that lock without resolving
new versions. PyInstaller bundles the Python interpreter and may also include
Tcl/Tk and native libraries whose notices are supplied by their distributions.

Every new executable release is accompanied by `window-swap-licenses.zip` and
its SHA-256 digest. The archive contains the complete installed runtime-library
license texts, available CPython/Tcl/Tk notices, and a manifest of versions and
hashes. The Pillow license file also includes notices for its bundled native
libraries. Windows CPython's combined `LICENSE.txt` can contain the complete
Tcl/Tk texts: the packager recognizes these using pinned hashes and also includes
them separately. Packaging stops if any CPython/Tcl/Tk notice is unavailable;
it does not silently publish an incomplete license companion.

The archive includes the exact official pystray wheel named in `uv.lock`,
downloaded with its locked SHA-256 verified. This wheel contains pystray's
complete Python source and both `COPYING` (GNU GPL v3) and `COPYING.LGPL` (GNU
LGPL v3). Both license texts are also supplied separately under
`licenses/pystray/`. Packaging fails if either text is absent.

The archive's README explains how to modify that pystray source and rebuild
Window Swap with the modified library. Modification and reverse engineering
for debugging such modifications remain permitted under the LGPL. Window
Swap's application source and build scripts are available from the matching
release tag in this repository.

PyInstaller uses GPL terms with a bundling exception; this does not change the
license of Window Swap, but the licenses of included dependencies still apply.
See <https://pyinstaller.org/en/stable/license.html>.
