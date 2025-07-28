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


class Error(Exception):
    """
    Base class for handling exception occurring in MDANSE.

    Any exception defined in MDANSE should derive from it in order to be properly handled
    in the GUI application.
    """

    def __init__(self, msg=None):
        self._msg = msg

    def __str__(self):
        return repr(self._msg)
