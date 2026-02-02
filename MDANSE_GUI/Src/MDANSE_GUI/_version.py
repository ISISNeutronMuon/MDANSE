#    This file is part of MDANSE.
#
#    MDANSE is free software: you can redistribute it and/or modify
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

import os


def get_version():
    """Get MDANSE version.

    If not in git, return static version.
    """
    if version := os.getenv("MDANSE_GUI_VERSION"):
        return version

    try:
        from setuptools_git_versioning import version_from_git

        return version_from_git()
    except Exception:
        from importlib.metadata import version

        return version("MDANSE_GUI")
