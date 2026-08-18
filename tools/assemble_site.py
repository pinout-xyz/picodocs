#!/usr/bin/env python3
"""Assemble the picodocs site from per-version, per-platform Doxygen output.

Directories passed with --artifacts must be named either "<version>-<platform>"
or "pico-sdk-<version>-<platform>-docs", the name GitHub Actions gives the
uploaded artifacts. Local builds can be named on the command line instead.

    python3 tools/assemble_site.py --artifacts artifacts site
    python3 tools/assemble_site.py --build 2.3.0:rp2350:build/pico-sdk/docs/doxygen/html site
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

BUILD_NAME = re.compile(r"^(?:pico-sdk-)?(\d+\.\d+\.\d+)-([a-z0-9-]+?)(?:-docs)?$")

ASSETS = [
    ("nav.css", "picodocs-nav.css"),
    ("nav.js", "picodocs-nav.js"),
    ("search.css", "picodocs-search.css"),
    ("search.js", "picodocs-search.js"),
    ("theme.css", "picodocs-theme.css"),
    ("theme.js", "picodocs-theme.js"),
    ("pinout-logo.svg", "picodocs-logo.svg"),
]

TAGS = (
    '<link href="/picodocs-nav.css" rel="stylesheet" type="text/css"/>'
    '<link href="/picodocs-search.css" rel="stylesheet" type="text/css"/>'
    '<link href="/picodocs-theme.css" rel="stylesheet" type="text/css"/>'
    '<script src="/picodocs-nav.js" defer></script>'
    '<script src="/picodocs-search.js" defer></script>'
    '<script src="/picodocs-theme.js" defer></script>'
)


def version_key(version):
    return tuple(int(part) for part in version.split("."))


def find_builds(artifacts, named):
    builds = {}

    if artifacts:
        for path in sorted(artifacts.iterdir()):
            match = BUILD_NAME.match(path.name)
            if path.is_dir() and match:
                version, platform = match.groups()
                builds.setdefault(version, {})[platform] = path

    for spec in named:
        version, platform, path = spec.split(":", 2)
        builds.setdefault(version, {})[platform] = Path(path)

    for version, platforms in builds.items():
        for platform, path in platforms.items():
            if not path.is_dir():
                raise SystemExit(f"{version} {platform}: {path} is not a directory")

    return builds


def copy_builds(builds, site, latest, root_platform):
    root_build = builds[latest].get(root_platform)
    if root_build is None:
        raise SystemExit(f"no {root_platform} build of {latest} to serve at the site root")

    shutil.copytree(root_build, site, dirs_exist_ok=True)
    for version, platforms in builds.items():
        for platform, path in platforms.items():
            shutil.copytree(path, site / version / platform, dirs_exist_ok=True)


def write_assets(builds, site, assets, latest, root_platform):
    manifest = {
        "latest": latest,
        "rootPlatform": root_platform,
        "versions": [
            {"version": version, "platforms": sorted(builds[version])}
            for version in sorted(builds, key=version_key, reverse=True)
        ],
    }

    for source, published in ASSETS:
        text = (assets / source).read_text()
        if source == "nav.js":
            text = f"const PICODOCS = {json.dumps(manifest)};\n" + text
        (site / published).write_text(text)


def inject_tags(site):
    injected = 0
    for page in site.rglob("*.html"):
        if "search" in page.relative_to(site).parts:
            continue
        text = page.read_text(encoding="utf-8", errors="surrogateescape")
        if "picodocs-nav.js" in text or "</head>" not in text:
            continue
        page.write_text(text.replace("</head>", TAGS + "</head>", 1),
                        encoding="utf-8", errors="surrogateescape")
        injected += 1
    return injected


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("site", type=Path, help="directory to assemble the site into")
    parser.add_argument("--artifacts", type=Path, help="directory holding the build directories")
    parser.add_argument("--build", action="append", default=[], metavar="VERSION:PLATFORM:PATH",
                        help="name a build directly, repeatable")
    parser.add_argument("--assets", type=Path, default=Path(__file__).resolve().parent.parent / "web",
                        help="directory holding nav and search assets")
    parser.add_argument("--root-platform", default="rp2040",
                        help="platform whose latest build is served at the site root")
    args = parser.parse_args()

    builds = find_builds(args.artifacts, args.build)
    if not builds:
        raise SystemExit("no builds given, pass --artifacts or --build")

    latest = max(builds, key=version_key)
    args.site.mkdir(parents=True, exist_ok=True)

    copy_builds(builds, args.site, latest, args.root_platform)
    write_assets(builds, args.site, args.assets, latest, args.root_platform)
    injected = inject_tags(args.site)

    for version in sorted(builds, key=version_key, reverse=True):
        print(f"{version}: {' '.join(sorted(builds[version]))}")
    print(f"root: {latest} {args.root_platform}, {injected} pages injected", file=sys.stderr)


if __name__ == "__main__":
    main()
