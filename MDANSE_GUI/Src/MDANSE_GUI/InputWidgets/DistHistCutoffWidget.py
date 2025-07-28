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

from math import floor

from .RangeWidget import RangeWidget


class DistHistCutoffWidget(RangeWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setup_fields(self, *args, **kwargs):
        start = 0.0
        end = floor(self._configurator.get_largest_cutoff() * 100) / 100
        step = 0.01
        super().setup_fields(*args, default=(start, end, step), **kwargs)
