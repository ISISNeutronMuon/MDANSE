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

from collections.abc import Iterable

import MDAnalysis as mda

from MDANSE.Framework.AtomMapping import AtomLabel

from .FileWithAtomDataConfigurator import FileWithAtomDataConfigurator


class MDAnalysisTopologyFileConfigurator(FileWithAtomDataConfigurator):
    """Constructs and MDAnalysis.Universe from the input file.

    The format of the input file can be specified manually, or
    set to AUTO. The automatic format determination typically
    fails for filenames without an extension.
    """

    _default = ("", "AUTO")

    def configure(self, setting: str) -> None:
        """
        Parameters
        ----------
        setting : tuple
            A tuple containing the topology filepath and format.
        """
        filepath, format = setting
        if format == "AUTO":
            self["format"] = None
        elif format in mda._PARSERS:
            self["format"] = format
        else:
            self.error_status = "MDAnalysis topology file format not recognised."
            return

        super().configure(filepath)

    def parse(self) -> None:
        # TODO currently MDAnalysis guesses the atom types and masses.
        #  There is a PR https://github.com/MDAnalysis/mdanalysis/pull/3753
        #  which will give us more control over what is guessed. We may
        #  want to change the MDAnalysis guessing options in the future
        #  so that it works better with the MDANSE atom mapping.
        self.atoms = mda.Universe(
            self["filename"], topology_format=self["format"]
        ).atoms

    def atom_labels(self) -> Iterable[AtomLabel]:
        """
        Yields
        ------
        AtomLabel
            An atom label.
        """
        args = []
        for arg in ["element", "name", "type", "resname", "mass"]:
            if hasattr(self.atoms[0], arg):
                args.append(arg)
        if len(args) == 0:
            yield from []
            return

        for at in self.atoms:
            kwargs = {}
            for arg in args:
                kwargs[arg] = getattr(at, arg)
            # the first out of the list above will be the main label
            (k, main_label) = next(iter(kwargs.items()))
            kwargs.pop(k)
            yield AtomLabel(main_label, **kwargs)
