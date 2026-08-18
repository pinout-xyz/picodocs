#!/usr/bin/env python3
"""Build the Pico SDK's Doxygen docs for every released version and platform.

Versions come from the tags of a pico-sdk checkout.

Each build lands in "<output>/<version>-<platform>", ready for assemble_site.py.

    git clone https://github.com/raspberrypi/pico-sdk
    python3 tools/build_docs.py --sdk pico-sdk --output builds
"""

import argparse
import concurrent.futures
import re
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent

RELEASE_TAG = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")

RP2350_SINCE = (2, 0, 0)

EXAMPLES_REPO = "https://github.com/raspberrypi/pico-examples"


def run(command, **kwargs):
    return subprocess.run(command, check=True, text=True, **kwargs)


def released_versions(sdk, minimum):
    tags = run(["git", "-C", str(sdk), "tag", "--list"], capture_output=True).stdout.split()
    versions = [tag for tag in tags if RELEASE_TAG.match(tag)]
    return sorted((v for v in versions if version_key(v) >= version_key(minimum)), key=version_key)


def version_key(version):
    return tuple(int(part) for part in version.split("."))


def platforms_for(version, platforms):
    if version_key(version) < RP2350_SINCE:
        return [platform for platform in platforms if platform == "rp2040"]
    return platforms


def prepare_worktree(sdk, work, version):
    worktree = work / "sdk" / version
    if not worktree.exists():
        run(["git", "-C", str(sdk), "worktree", "add", "--detach", str(worktree.resolve()), version],
            capture_output=True)
    return worktree


def prepare_examples(work):
    examples = work / "pico-examples"
    if not examples.exists():
        run(["git", "clone", "--depth", "1", EXAMPLES_REPO, str(examples)], capture_output=True)
    return examples


def build(worktree, examples, work, output, version, platform):
    name = f"{version}-{platform}"
    build_dir = work / "build" / name
    log = work / "log" / f"{name}.log"
    log.parent.mkdir(parents=True, exist_ok=True)

    with log.open("w") as log_file:
        run(["cmake", "-S", str(PROJECT), "-B", str(build_dir),
             f"-DPICO_SDK_PATH={worktree.resolve()}",
             f"-DPICO_EXAMPLES_PATH={examples.resolve()}",
             f"-DPICO_PLATFORM={platform}"], stdout=log_file, stderr=subprocess.STDOUT)

        doxyfile = build_dir / "pico-sdk" / "docs" / "Doxyfile"
        with doxyfile.open("a") as handle:
            handle.write("HTML_COLORSTYLE = LIGHT\n")

        run(["cmake", "--build", str(build_dir), "--target", "docs"],
            stdout=log_file, stderr=subprocess.STDOUT)

    html = build_dir / "pico-sdk" / "docs" / "doxygen" / "html"
    if not html.is_dir():
        raise RuntimeError(f"{name}: doxygen produced no html, see {log}")

    destination = output / name
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(html, destination)
    return name


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sdk", type=Path, required=True, help="pico-sdk checkout, tags and all")
    parser.add_argument("--output", type=Path, default=Path("builds"), help="where the html trees land")
    parser.add_argument("--work", type=Path, help="scratch directory (default <output>/../.picodocs)")
    parser.add_argument("--versions", nargs="+", help="build these versions instead of every released tag")
    parser.add_argument("--min-version", default="1.5.1", help="oldest tag to build")
    parser.add_argument("--platforms", nargs="+", default=["rp2040", "rp2350"])
    parser.add_argument("--jobs", type=int, default=4, help="builds to run at once")
    parser.add_argument("--keep-going", action="store_true", help="report failures at the end")
    args = parser.parse_args()

    versions = args.versions or released_versions(args.sdk, args.min_version)
    if not versions:
        raise SystemExit(f"no release tags at or after {args.min_version} in {args.sdk}")

    work = args.work or args.output.parent / ".picodocs"
    work.mkdir(parents=True, exist_ok=True)
    args.output.mkdir(parents=True, exist_ok=True)

    examples = prepare_examples(work)
    targets = []
    for version in versions:
        worktree = prepare_worktree(args.sdk, work, version)
        for platform in platforms_for(version, args.platforms):
            targets.append((worktree, version, platform))

    print(f"building {len(targets)} docs trees from {len(versions)} versions", file=sys.stderr)

    failures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = {
            pool.submit(build, worktree, examples, work, args.output, version, platform):
                f"{version}-{platform}"
            for worktree, version, platform in targets
        }
        for future in concurrent.futures.as_completed(futures):
            name = futures[future]
            try:
                future.result()
                print(f"built {name}", file=sys.stderr)
            except Exception as error:
                failures.append((name, error))
                print(f"FAILED {name}: {error}", file=sys.stderr)
                if not args.keep_going:
                    raise SystemExit(1)

    if failures:
        raise SystemExit(f"{len(failures)} of {len(targets)} builds failed")


if __name__ == "__main__":
    main()
