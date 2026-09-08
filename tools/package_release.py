"""Prepare release checksums and licenses; never read user app settings or logs."""

from __future__ import annotations

import hashlib
import io
import json
import platform
import re
import sys
import tomllib
import urllib.request
import zipfile
from importlib import metadata
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PACKAGES = ("pillow", "pystray", "pywin32", "six")
MAX_SOURCE_BYTES = 2 * 1024 * 1024
# Official Tcl/Tk core-8-6-12 license.terms, normalized to LF with one final LF.
# CPython's Windows PCbuild/regen.targets appends these to LICENSE.txt.
EMBEDDED_NOTICE_HASHES = {
    "c0a69a2bfd757361ec7e6143973b103c90409316b49e9c88db26ad6388e79f16": "tcl",
    "2cde822b93ca16ae535c954b7dfe658b4ad10df2a193628d1b358f1765e8b198": "tk",
}

REBUILD_README = """# Window Swap: licenses and corresponding library source

Window Swap's own code is MIT-licensed. Components keep their own licenses.
This archive includes the installed libraries' complete license texts, available
CPython/Tcl/Tk notices, and the exact unmodified pystray wheel from uv.lock.
The pystray wheel is a ZIP containing its complete Python source (.py files),
including both GNU GPL v3 and GNU LGPL v3 license texts. Its download was checked
against the SHA-256 in uv.lock; the same URL and digest are in manifest.json.
Packaging requires all CPython, Tcl, and Tk notices. On Windows the Tcl/Tk
texts may be embedded in CPython's combined LICENSE.txt; the packager recognizes
their complete text by pinned hashes and also supplies them as separate files.

## Rebuild with a modified pystray library

1. Obtain Window Swap source for this release tag from:
   https://github.com/jcomlabs/window-swap
   The repository includes the application code, build_release.py, and uv.lock.
2. Install a supported Python 3.13 build on Windows, and uv 0.11.17. From that
   source directory run: uv sync --frozen --extra dev --extra build
3. Unzip sources/pystray-*.whl from this archive into a separate working folder.
   Edit the .py files in its pystray/ folder as needed. Copy that folder over
   .venv/Lib/site-packages/pystray/ in your Window Swap source checkout.
4. Run: uv run --no-sync python -m pytest
   Then: uv run --no-sync python build_release.py
   --no-sync preserves your modified library while building the executable.
5. Close the running Window Swap using its tray menu and run your new
   dist/window-swap.exe. Administrator access is not required.

Modification of pystray and reverse engineering for debugging those
modifications are permitted under its LGPL terms. This archive does not change
those terms. The complete license texts are under licenses/pystray/.
"""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def locked_pystray_source(lock: dict) -> dict[str, str]:
    """Select only the official, hash-pinned source-bearing pystray wheel."""

    packages = [item for item in lock["package"] if item["name"] == "pystray"]
    if len(packages) != 1:
        raise ValueError("Expected exactly one pystray version in uv.lock")
    package = packages[0]
    if package.get("source", {}).get("registry") != "https://pypi.org/simple":
        raise ValueError("pystray must originate from the public PyPI registry")
    wheels = package.get("wheels", [])
    if len(wheels) != 1:
        raise ValueError("Expected one platform-independent pystray source wheel")
    wheel = wheels[0]
    address = urlsplit(wheel["url"])
    expected_filename = f"pystray-{package['version']}-py2.py3-none-any.whl"
    if (
        address.scheme != "https"
        or address.netloc != "files.pythonhosted.org"
        or address.query
        or address.fragment
        or PurePosixPath(address.path).name != expected_filename
    ):
        raise ValueError("Unexpected pystray source URL in uv.lock")
    digest = wheel.get("hash", "")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        raise ValueError("pystray source requires a SHA-256 digest")
    return {
        "version": package["version"],
        "filename": expected_filename,
        "url": wheel["url"],
        "sha256": digest.removeprefix("sha256:"),
    }


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Source download redirects are not permitted")


def download_verified_source(source: dict[str, str]) -> bytes:
    """Download only an allowlisted HTTPS URL and verify the locked bytes."""

    address = urlsplit(source["url"])
    if address.scheme != "https" or address.netloc != "files.pythonhosted.org":
        raise ValueError("Source host must be files.pythonhosted.org over HTTPS")
    opener = urllib.request.build_opener(NoRedirect())
    with opener.open(source["url"], timeout=30) as response:
        data = response.read(MAX_SOURCE_BYTES + 1)
    if len(data) > MAX_SOURCE_BYTES:
        raise ValueError("pystray source download exceeds the expected size limit")
    if sha256(data) != source["sha256"]:
        raise ValueError("pystray source does not match its locked SHA-256")
    with zipfile.ZipFile(io.BytesIO(data)) as wheel:
        names = set(wheel.namelist())
        prefix = f"pystray-{source['version']}.dist-info/"
        required = {"pystray/__init__.py", prefix + "COPYING", prefix + "COPYING.LGPL"}
        if not required <= names:
            raise ValueError("pystray source or complete GPL/LGPL texts are missing")
    return data


def distribution_licenses(name: str, expected_version: str) -> dict[str, bytes]:
    """Collect notice files only, omitting environment-specific package metadata."""

    distribution = metadata.distribution(name)
    if distribution.version != expected_version:
        raise ValueError(f"Installed {name} differs from uv.lock; run uv sync --frozen")
    entries: dict[str, bytes] = {}
    for item in distribution.files or ():
        parts = PurePosixPath(str(item).replace("\\", "/")).parts
        if not parts or not parts[0].endswith(".dist-info"):
            continue
        relative = PurePosixPath(*parts[1:])
        if ".." in relative.parts or relative.is_absolute():
            raise ValueError("A package license contains an unsafe archive path")
        if "licenses" not in relative.parts and not relative.name.lower().startswith(
            ("license", "copying", "notice", "authors")
        ):
            continue
        entries[f"licenses/{name}/{relative.as_posix()}"] = Path(
            distribution.locate_file(item)
        ).read_bytes()
    if not entries:
        raise ValueError(f"Complete license files are missing for {name}")
    if name == "pystray":
        for required in ("COPYING", "COPYING.LGPL"):
            if not any(PurePosixPath(path).name == required for path in entries):
                raise ValueError("pystray requires both complete GPL and LGPL texts")
    return entries


def embedded_tcl_tk_licenses(combined: bytes) -> dict[str, bytes]:
    """Recognize complete upstream license texts inside the Windows Python notice."""

    entries: dict[str, bytes] = {}
    text = combined.decode("utf-8").replace("\r\n", "\n")
    blocks = re.findall(
        r"This software is copyrighted by the Regents of the University of\n"
        r"California, Sun Microsystems, Inc\., Scriptics Corporation, ActiveState"
        r".*?terms specified in this license\.",
        text,
        flags=re.DOTALL,
    )
    for block in blocks:
        notice = (block.strip() + "\n").encode("utf-8")
        component = EMBEDDED_NOTICE_HASHES.get(sha256(notice))
        if component:
            entries[f"licenses/{component}/license.terms"] = notice
    return entries


def interpreter_licenses(prefix: Path) -> tuple[dict[str, bytes], list[str]]:
    """Use only well-known interpreter notice locations; record unavailable ones."""

    entries: dict[str, bytes] = {}
    for filename in ("LICENSE.txt", "LICENSE", "LICENSE.rst"):
        candidate = prefix / filename
        if candidate.is_file():
            notice = candidate.read_bytes()
            entries[f"licenses/cpython/{filename}"] = notice
            entries.update(embedded_tcl_tk_licenses(notice))
            break
    tcl_root = prefix / "tcl"
    if tcl_root.is_dir():
        for directory in sorted(tcl_root.iterdir()):
            if not directory.is_dir() or not re.fullmatch(
                r"(?:tcl|tk)[0-9.]+", directory.name
            ):
                continue
            for filename in ("license.terms", "license.txt", "LICENSE", "COPYING"):
                candidate = directory / filename
                if candidate.is_file():
                    entries[f"licenses/{directory.name}/{filename}"] = (
                        candidate.read_bytes()
                    )
    missing = [
        component
        for component, pattern in (
            ("CPython", r"licenses/cpython/"),
            ("Tcl", r"licenses/tcl[0-9.]*/"),
            ("Tk", r"licenses/tk[0-9.]*/"),
        )
        if not any(re.match(pattern, name) for name in entries)
    ]
    return entries, missing


def write_archive(path: Path, entries: dict[str, bytes]) -> None:
    """Store fixed relative names and timestamps, never host paths or settings."""

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(entries.items()):
            relative = PurePosixPath(name)
            if (
                relative.is_absolute()
                or ".." in relative.parts
                or "\\" in name
                or ":" in name
            ):
                raise ValueError("Unsafe release archive member name")
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, data)


def package_release(root: Path = ROOT) -> None:
    dist = root / "dist"
    executable = dist / "window-swap.exe"
    if not executable.is_file():
        raise ValueError("Build dist/window-swap.exe before packaging release notices")
    lock_bytes = (root / "uv.lock").read_bytes()
    lock = tomllib.loads(lock_bytes.decode("utf-8"))
    packages = {item["name"]: item["version"] for item in lock["package"]}
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    entries = {
        "LICENSE": (root / "LICENSE").read_bytes(),
        "THIRD_PARTY_NOTICES.md": (root / "THIRD_PARTY_NOTICES.md").read_bytes(),
        "README.md": REBUILD_README.encode("utf-8"),
    }
    for name in (*RUNTIME_PACKAGES, "pyinstaller"):
        entries.update(distribution_licenses(name, packages[name]))
    interpreter_entries, missing = interpreter_licenses(Path(sys.base_prefix))
    if missing:
        raise ValueError(
            "Complete interpreter notices are missing: " + ", ".join(missing)
        )
    entries.update(interpreter_entries)
    source = locked_pystray_source(lock)
    entries[f"sources/{source['filename']}"] = download_verified_source(source)
    executable_digest = sha256(executable.read_bytes())
    manifest = {
        "schema_version": 1,
        "application": {
            "name": "window-swap",
            "version": project["project"]["version"],
        },
        "executable": {"name": executable.name, "sha256": executable_digest},
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
        },
        "uv_lock_sha256": sha256(lock_bytes),
        "runtime_packages": [
            {"name": name, "version": packages[name]} for name in RUNTIME_PACKAGES
        ],
        "build_packages": [{"name": "pyinstaller", "version": packages["pyinstaller"]}],
        "pystray_source": source,
        "interpreter_notices_unavailable": missing,
        "files": [
            {"name": name, "sha256": sha256(data)}
            for name, data in sorted(entries.items())
        ],
    }
    entries["manifest.json"] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    archive = dist / "window-swap-licenses.zip"
    write_archive(archive, entries)
    for artifact, digest in (
        (executable, executable_digest),
        (archive, sha256(archive.read_bytes())),
    ):
        artifact.with_suffix(artifact.suffix + ".sha256").write_text(
            f"{digest}  {artifact.name}\n", encoding="ascii", newline="\n"
        )
    print("Release checksums and license/source companion prepared for review.")


if __name__ == "__main__":
    package_release()
