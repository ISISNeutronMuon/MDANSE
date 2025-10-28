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

from MDANSE.Framework.Configurators.RangeConfigurator import (
    RangeConfigurator,
)

from .IConfigurator import PredictionSettings


class QRangeConfigurator(RangeConfigurator):
    """Range configurator for Q vector generation."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prediction = PredictionSettings(
            key="value", label="Q vector shell centres", unit="1/nm"
        )
