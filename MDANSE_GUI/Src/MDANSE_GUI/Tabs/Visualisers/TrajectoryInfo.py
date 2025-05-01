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

from typing import TYPE_CHECKING
import json

from MDANSE.MLogging import LOG

import numpy as np
from qtpy.QtCore import Slot, Signal
from qtpy.QtWidgets import QTextBrowser

if TYPE_CHECKING:
    from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
    from MDANSE.MolecularDynamics.Trajectory import Trajectory

json_decoder = json.decoder.JSONDecoder()


class TrajectoryInfo(QTextBrowser):
    error = Signal(str)

    def __init__(self, *args, **kwargs):
        self._header = kwargs.pop("header", "")
        self._footer = kwargs.pop("footer", "")
        super().__init__(*args, **kwargs)
        self.setOpenExternalLinks(True)

    @Slot(object)
    def update_panel(self, data: "Trajectory"):
        incoming = data
        if incoming is None:
            text = "Trajectory is still being loaded."
            self.setHtml(text)
            return
        try:
            text = self.summarise_trajectory(
                incoming
            )  # this is from a trajectory object
        except AttributeError:
            self.error.emit(f"Trajectory info received {incoming}")
            self.clear()
            return
        try:
            cs = incoming.chemical_system
        except AttributeError:
            self.error.emit(f"Trajectory {incoming} has no chemical system")
        else:
            text += self.summarise_chemical_system(cs)
        filtered = self.filter(text)
        self.setHtml(filtered)

    def check_trajectory_metadata(self, trajectory: "Trajectory"):
        meta_dict = {}

        def put_into_dict(name, obj):
            try:
                string = obj[:][0].decode()
            except Exception:
                LOG.debug(f"Decode failed for {name}: {obj}")
            else:
                try:
                    meta_dict[name] = json_decoder.decode(string)
                except ValueError:
                    meta_dict[name] = string

        try:
            meta = trajectory.file["metadata"]
        except KeyError:
            return
        else:
            meta.visititems(put_into_dict)
        return meta_dict

    def summarise_trajectory(self, trajectory: "Trajectory"):
        val = []
        try:
            time_axis = trajectory.time()
        except Exception:
            timeline = "No time information!\n"
        else:
            if len(time_axis) < 1:
                timeline = "N/A\n"
            elif len(time_axis) < 5:
                timeline = f"{time_axis}\n"
            else:
                timeline = f"[{time_axis[0]}, {time_axis[1]}, ..., {time_axis[-1]}]\n"

        val.append("Path:")
        val.append(f"{trajectory.filename}\n")
        val.append("Number of steps:")
        val.append(f"{trajectory}\n")
        val.append("Configuration:")
        val.append(f"\tIs periodic: {trajectory.unit_cell(0) is not None}\n")
        try:
            val.append(f"First unit cell (nm):\n{trajectory.unit_cell(0)._unit_cell}\n")
        except Exception:
            val.append("No unit cell information\n")
        val.append("Frame times (1st, 2nd, ..., last) in ps:")
        val.append(timeline)
        val.append("Variables:")
        for k in trajectory.variables():
            v = trajectory.variable(k)
            try:
                val.append(f"\t- {k}: {v.shape}")
            except AttributeError:
                try:
                    val.append(f"\t- {k}: {v['value'].shape}")
                except KeyError:
                    continue

        val.append("\nConversion history:")
        for k, v in self.check_trajectory_metadata(trajectory).items():
            val.append(f"{k}: {v}")

        mol_types = {}
        val.append("\nMolecular types found:")
        for molname, mollist in trajectory.chemical_system._clusters.items():
            val.append(f"Molecule: {molname}; Count: {len(mollist)}")

        for k, v in mol_types.items():
            val.append(f"\t- {v:d} {k}")

        val = "\n".join(val)

        return val

    def summarise_chemical_system(self, cs: "ChemicalSystem"):
        text = "\n ==== Chemical System summary ==== \n"
        atoms, counts = np.unique(cs.atom_list, return_counts=True)
        for ind in range(len(atoms)):
            text += f"Element: {atoms[ind]}; Count: {counts[ind]}\n"
        for molname, mollist in cs._clusters.items():
            text += f"Molecule: {molname}; Count: {len(mollist)}\n"
        text += " ===== \n"
        return text

    def filter(self, some_text: str, line_break="<br />"):
        new_text = ""
        if self._header:
            new_text += self._header + line_break
        if some_text is not None:
            new_text += line_break.join([x.strip() for x in some_text.split("\n")])
        if self._footer:
            new_text += line_break + self._footer
        return new_text
