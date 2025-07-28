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

from MDANSE.NeutronInstruments.Coverage.Coverage import Coverage
from MDANSE.NeutronInstruments.NeutronInstrument import NeutronInstrument
from MDANSE.NeutronInstruments.Resolution.Resolution import Resolution
from MDANSE.NeutronInstruments.Spectrum.Spectrum import Spectrum


class IdealInstrument(NeutronInstrument):
    def __init__(self, *args, **kwargs):
        self.coverage = Coverage.create("TotalCoverage")
        self.spectrum = Spectrum.create("FlatSpectrum")
        self.resolution = Resolution.create("IdealResolution")
