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
from .DoublePanel import DoublePanel


class TriplePanel(DoublePanel):
    """The triple panel layout which adds an extra visualiser panel to
    the left side of the layout"""

    def __init__(self, *args, **kwargs):
        left_panel = kwargs.pop("left_panel", None)
        super().__init__(*args, **kwargs)

        if left_panel is not None:
            self._leftlayout.addWidget(left_panel)
            if self._view is not None:
                self._view.connect_to_visualiser(left_panel)
