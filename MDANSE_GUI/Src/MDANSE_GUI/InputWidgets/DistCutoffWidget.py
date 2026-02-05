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

from .FloatWidget import FloatWidget


class DistCutoffWidget(FloatWidget):
    def setup_field(self, *args, **kwargs):
        mini = 0.0
        default = round(self._configurator.get_max_cutoff(), 2)
        maxi = default
        super().setup_field(mini=mini, default=default, maxi=maxi)
