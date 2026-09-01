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

import os
import sys

from MDANSE_GUI.main import mdanse_icon_path


def main():
    try:
        from pyshortcuts import make_shortcut
    except ImportError:
        print(  # noqa: T201
            "To create a shortcut and menu entry for MDANSE_GUI, "
            "this script needs the 'pyshortcuts' package.\n"
            "You can install it by running\n"
            "pip install MDANSE_GUI[extras]"
        )
    else:
        script_path = Path(__file__).parent
        make_shortcut(
            script_path / "mdanse_gui.py",
            name="MDANSE_GUI",
            working_dir=script_path,
            description=f"MDANSE {MDANSE_GUI.__version__}, software for molecular dynamics trajectory analysis",
            icon=mdanse_icon_path,
        )


if __name__ == "__main__":
    main()
