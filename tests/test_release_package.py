from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import pytest

from tools import package_release as release


def source_wheel() -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as wheel:
        wheel.writestr("pystray/__init__.py", "# Synthetic source; not executed.\n")
        wheel.writestr("pystray-0.19.5.dist-info/COPYING", "Synthetic GPL text")
        wheel.writestr("pystray-0.19.5.dist-info/COPYING.LGPL", "Synthetic LGPL text")
    return output.getvalue()


def source_spec(data: bytes) -> dict[str, str]:
    return {
        "version": "0.19.5",
        "filename": "pystray-0.19.5-py2.py3-none-any.whl",
        "url": "https://files.pythonhosted.org/packages/pystray-0.19.5-py2.py3-none-any.whl",
        "sha256": release.sha256(data),
    }


class FakeOpener:
    def __init__(self, data: bytes) -> None:
        self.data = data

    def open(self, _url: str, timeout: int) -> io.BytesIO:
        return io.BytesIO(self.data)


def test_source_tampering_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    original = source_wheel()
    monkeypatch.setattr(
        release.urllib.request,
        "build_opener",
        lambda _handler: FakeOpener(original + b"tampered"),
    )
    with pytest.raises(ValueError, match="locked SHA-256"):
        release.download_verified_source(source_spec(original))


def test_verified_wheel_contains_source_and_both_licenses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = source_wheel()
    monkeypatch.setattr(
        release.urllib.request, "build_opener", lambda _handler: FakeOpener(original)
    )
    assert release.download_verified_source(source_spec(original)) == original
    incomplete = io.BytesIO()
    with zipfile.ZipFile(incomplete, "w") as wheel:
        wheel.writestr("pystray/__init__.py", "# Missing licenses")
    data = incomplete.getvalue()
    monkeypatch.setattr(
        release.urllib.request, "build_opener", lambda _handler: FakeOpener(data)
    )
    with pytest.raises(ValueError, match="GPL/LGPL"):
        release.download_verified_source(source_spec(data))


def test_source_download_cannot_target_another_host() -> None:
    spec = source_spec(source_wheel())
    spec["url"] = "https://example.invalid/private-resource"
    with pytest.raises(ValueError, match="Source host"):
        release.download_verified_source(spec)


def test_source_redirects_are_rejected() -> None:
    with pytest.raises(ValueError, match="redirects"):
        release.NoRedirect().redirect_request(
            None, None, 302, "", {}, "https://example.invalid"
        )


def test_embedded_notices_require_complete_pinned_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    notice = (
        b"This software is copyrighted by the Regents of the University of\n"
        b"California, Sun Microsystems, Inc., Scriptics Corporation, ActiveState\n"
        b"Synthetic full license body; terms specified in this license.\n"
    )
    monkeypatch.setattr(
        release, "EMBEDDED_NOTICE_HASHES", {release.sha256(notice): "tcl"}
    )
    combined = b"Interpreter notice\r\n" + notice.replace(b"\n", b"\r\n")
    assert release.embedded_tcl_tk_licenses(combined) == {
        "licenses/tcl/license.terms": notice
    }
    assert release.embedded_tcl_tk_licenses(combined.replace(b"full", b"altered")) == {}
    assert release.embedded_tcl_tk_licenses(combined[:-12]) == {}


def test_pystray_installed_license_is_required(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class FakeDistribution:
        version = "0.19.5"
        files = (Path("pystray-0.19.5.dist-info/COPYING"),)

        def locate_file(self, path: Path) -> Path:
            return tmp_path / path

    license_file = tmp_path / FakeDistribution.files[0]
    license_file.parent.mkdir()
    license_file.write_text("Synthetic GPL")
    monkeypatch.setattr(
        release.metadata, "distribution", lambda _name: FakeDistribution()
    )
    with pytest.raises(ValueError, match="both complete GPL and LGPL"):
        release.distribution_licenses("pystray", "0.19.5")


@pytest.mark.parametrize(
    "name",
    [
        "../settings.json",
        "/absolute/LICENSE",
        "C:/Users/private.txt",
        "..\\private.txt",
    ],
)
def test_archive_rejects_host_paths(tmp_path: Path, name: str) -> None:
    with pytest.raises(ValueError, match="Unsafe release archive"):
        release.write_archive(tmp_path / "bad.zip", {name: b"synthetic"})


def test_packaging_excludes_local_data_and_records_verified_hashes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = source_wheel()
    source = source_spec(original)
    (tmp_path / "dist").mkdir()
    executable = tmp_path / "dist/window-swap.exe"
    executable.write_bytes(b"synthetic executable")
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "1.2.0b4"\n')
    (tmp_path / "LICENSE").write_text("Synthetic MIT")
    (tmp_path / "THIRD_PARTY_NOTICES.md").write_text("Synthetic notices")
    (tmp_path / "settings.json").write_text('{"private": "must never be packaged"}')
    (tmp_path / "debug.log").write_text("private log contents")
    lock_text = "\n".join(
        f'[[package]]\nname = "{name}"\nversion = "{version}"\n'
        for name, version in (
            ("pillow", "12.3.0"),
            ("pystray", "0.19.5"),
            ("pywin32", "312"),
            ("six", "1.17.0"),
            ("pyinstaller", "6.21.0"),
        )
    )
    (tmp_path / "uv.lock").write_text(lock_text)
    monkeypatch.setattr(
        release,
        "distribution_licenses",
        lambda name, _version: {f"licenses/{name}/LICENSE": b"synthetic"},
    )
    monkeypatch.setattr(release, "interpreter_licenses", lambda _prefix: ({}, ["Tcl"]))
    monkeypatch.setattr(release, "locked_pystray_source", lambda _lock: source)
    monkeypatch.setattr(
        release.urllib.request, "build_opener", lambda _handler: FakeOpener(original)
    )

    with pytest.raises(ValueError, match="interpreter notices are missing: Tcl"):
        release.package_release(tmp_path)
    monkeypatch.setattr(release, "interpreter_licenses", lambda _prefix: ({}, []))
    release.package_release(tmp_path)

    archive_file = tmp_path / "dist/window-swap-licenses.zip"
    with zipfile.ZipFile(archive_file) as archive:
        names = archive.namelist()
        manifest = json.loads(archive.read("manifest.json"))
        assert not any("settings" in name or "debug" in name for name in names)
        assert str(tmp_path) not in archive.read("manifest.json").decode()
        assert manifest["executable"]["sha256"] == release.sha256(
            executable.read_bytes()
        )
        assert manifest["pystray_source"]["sha256"] == release.sha256(original)
        assert manifest["interpreter_notices_unavailable"] == []
        for entry in manifest["files"]:
            assert release.sha256(archive.read(entry["name"])) == entry["sha256"]
    for artifact in (executable, archive_file):
        expected = f"{release.sha256(artifact.read_bytes())}  {artifact.name}\n"
        assert artifact.with_suffix(artifact.suffix + ".sha256").read_text() == expected
