#!/usr/bin/env python3
"""Fetch a pinned Doxygen release, so builds do not depend on the distro's.

Prints the path to the binary, downloading and unpacking it on first use.

    python3 tools/fetch_doxygen.py --dest .doxygen
"""

import argparse
import hashlib
import os
import platform as platform_module
import stat
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path

VERSION = "1.9.8"

RELEASES = "https://github.com/doxygen/doxygen/releases/download"

ASSETS = {
    "linux": "doxygen-{version}.linux.bin.tar.gz",
    "windows": "doxygen-{version}.windows.x64.bin.zip",
}

CHECKSUMS = {
    "doxygen-1.9.8.linux.bin.tar.gz":
        "dda773bdc62384b7d796fe8b6c5029daad72483e4c8ad4abf6ee9fb98b649388",
}


def detect_platform():
    if sys.platform.startswith("linux") and platform_module.machine() in ("x86_64", "AMD64"):
        return "linux"
    if sys.platform.startswith("win"):
        return "windows"
    return None


def asset_name(version, target):
    if target not in ASSETS:
        raise SystemExit(
            f"no Doxygen binary release for {sys.platform}/{platform_module.machine()}, "
            "install one and pass --doxygen instead"
        )
    return ASSETS[target].format(version=version)


def download(version, asset, into):
    url = f"{RELEASES}/Release_{version.replace('.', '_')}/{asset}"
    print(f"fetching {url}", file=sys.stderr)
    path = into / asset
    urllib.request.urlretrieve(url, path)

    expected = CHECKSUMS.get(asset)
    if expected:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != expected:
            raise SystemExit(f"{asset}: expected sha256 {expected}, got {digest}")

    return path


def unpack(archive, dest):
    if archive.name.endswith(".zip"):
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(dest)
    else:
        with tarfile.open(archive) as bundle:
            bundle.extractall(dest)


def binary(dest, version):
    for candidate in [dest / f"doxygen-{version}" / "bin" / "doxygen",
                      dest / f"doxygen-{version}" / "doxygen.exe",
                      dest / "doxygen.exe"]:
        if candidate.exists():
            return candidate
    return None


def ensure(version=VERSION, dest=Path(".doxygen"), target=None):
    dest = Path(dest)
    found = binary(dest, version)
    if found:
        return found

    target = target or detect_platform()
    asset = asset_name(version, target)
    dest.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as scratch:
        archive = download(version, asset, Path(scratch))
        unpack(archive, dest)

    found = binary(dest, version)
    if not found:
        raise SystemExit(f"{asset} did not contain a doxygen binary")

    found.chmod(found.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--version", default=VERSION, help="Doxygen release to fetch")
    parser.add_argument("--dest", type=Path, default=Path(".doxygen"), help="where to unpack it")
    parser.add_argument("--target", choices=sorted(ASSETS), help="override the detected platform")
    args = parser.parse_args()

    print(ensure(args.version, args.dest, args.target))


if __name__ == "__main__":
    main()
