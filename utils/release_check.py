#    This file is part of MDANSE_GUI.
#
#    MDANSE_GUI is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
from __future__ import annotations

import argparse
import re
import tomllib
from pathlib import Path

import yaml

ROOT_DIR = Path(__file__).parents[1]

MDANSE_DIR = ROOT_DIR / "MDANSE"
MDANSE_GUI_DIR = ROOT_DIR / "MDANSE_GUI"


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    parser.add_argument("version", help="Version to check.")

    return parser


def assert_version(path: Path, f_version: str, version: str):
    assert f_version == version, (
        f"version mismatch in {path.relative_to(ROOT_DIR)}\nGiven: {f_version!r}\nExpected: {version!r}"
    )


def check_pyproject(version: str) -> None:
    """Check pyprojects contain correct version."""

    current = ROOT_DIR / "pyproject.toml"

    with current.open("rb") as infile:
        dat = tomllib.load(infile)

    f_version = dat.get("project", {}).get("version", "")
    assert_version(current, f_version, version)

    for pth in (MDANSE_DIR, MDANSE_GUI_DIR):
        current = pth / "pyproject.toml"
        with current.open("rb") as infile:
            dat = tomllib.load(infile)

            f_version = (
                dat.get("tool", {})
                .get("setuptools-git-versioning", {})
                .get("starting_version", "")
            )
            assert_version(current, f_version, version)


def check_citation_cff(version: str) -> None:
    """Check citation contain correct version."""
    for pth in (ROOT_DIR, MDANSE_DIR, MDANSE_GUI_DIR):
        current = pth / "CITATION.cff"
        with current.open("r", encoding="utf-8") as infile:
            dat = yaml.safe_load(infile)
            f_version = dat.get("version", "")
            assert_version(current, f_version, version)


def check_issue_template(version: str) -> None:
    pth = ROOT_DIR / ".github/ISSUE_TEMPLATE/bug_report.md"
    text = pth.read_text()

    for match in re.finditer(r"MDANSE(?:_GUI)? version: \(e.g. ([^);]+)[);]", text):
        assert_version(pth, match[1], version)


def main(version: str) -> None:
    check_pyproject(version)
    check_citation_cff(version)
    check_issue_template(version)


if __name__ == "__main__":
    args = get_parser().parse_args()

    main(args.version)
