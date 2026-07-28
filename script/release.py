import argparse
import logging
import re
import subprocess
from pathlib import Path

CHANGELOG_PATH = "./CHANGELOG.md"
PYPROJECT_PATH = "./pyproject.toml"

log = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s: %(message)s",
)


def _read_changelog(path: Path, ver: str) -> list[str]:
    """Verify that the top version in CHANGELOG.md coincides with that expected and reads the
    release description."""
    log.info("Reading CHANGELOG.md")
    ver_found = False
    desc: list[str] = []
    with open("./CHANGELOG.md", encoding="utf-8") as f:
        for line in f:
            m = re.search(r"## \[(?P<ver>[\w.-]+)\]", line)
            if m and ver_found:
                break
            if m:
                if m.group("ver") != ver:
                    log.error("Version %s not found", ver)
                    raise ValueError(f"Version {ver} not found at the top of CHANGELOG.md")
                ver_found = True
            if ver_found:
                desc.append(line)
    return desc


def _subprocess_run(input: list[str]) -> str:
    result = subprocess.run(
        input,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def _update_and_push(ver: str) -> None:
    # Read the CHANGELOG.md file
    _ = _read_changelog(Path(CHANGELOG_PATH), ver)

    # Update project.toml file
    log.info("Reading pyproject.toml")
    with open(PYPROJECT_PATH, encoding="utf-8") as f:
        lines = f.readlines()

    m = re.search(r"version = \"(?P<ver>[\w.-]+)\"", lines[2])
    if m:
        if m.group("ver") == ver:
            log.error("pyproject.toml version alrady up to date")
            raise ValueError("pyproject.toml version alrady up to date")
    else:
        log.error("Version not found in pyproject.toml")
        raise ValueError("Version not found in pyproject.toml")

    log.info("Editing pyproject.toml")
    lines[2] = f'version = "{ver}"\n'
    with open(PYPROJECT_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)

    # Verify that we are not on the main branch
    branch = _subprocess_run(["git", "branch", "--show-current"]).strip()
    if branch == "main":
        log.error("Update release not allowed on the main branch")
        raise ValueError("Update release not allowed on the main branch")
    log.info("Branch: %s", branch)

    # Commit & push the changes
    log.info("Commit changes")
    output = _subprocess_run(["git", "add", CHANGELOG_PATH, PYPROJECT_PATH])
    print(output)
    output = _subprocess_run(["git", "commit", "-m", f"New release {ver}"])
    print(output)
    log.info("Push changes remotely")
    output = _subprocess_run(["git", "push", "origin", branch])
    print(output)


def _tag_and_release(ver: str) -> None:
    description = _read_changelog(Path(CHANGELOG_PATH), ver)

    log.info("Tagging the commit")
    output = _subprocess_run(["git", "tag", "-a", f"v{ver}"])
    print(output)
    output = _subprocess_run(["git", "push", "origin", f"v{ver}"])
    print(output)

    log.info("New release")
    output = _subprocess_run(
        [
            "gh",
            "release",
            "create",
            f"v{ver}",
            "--title",
            f"v{ver}",
            "--notes",
            " ".join(description),
        ]
    )
    print(output)


def main() -> None:
    parser = argparse.ArgumentParser(description="Finlib release update script")
    parser.add_argument("ver", type=str, help="New version MAJOR.MINOR.PATCH")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--pr", action="store_true")
    group.add_argument("--tag", action="store_true")
    args = parser.parse_args()

    if not args.pr and not args.tag:
        log.error("Either --pr or --tag need to be selected")
        raise ValueError("Either --pr or --tag need to be selected")

    if args.pr:
        _update_and_push(args.ver)

    if args.tag:
        _tag_and_release(args.ver)


if __name__ == "__main__":
    main()
