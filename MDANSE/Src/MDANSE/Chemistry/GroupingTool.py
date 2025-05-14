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
from typing import List, Tuple, Dict, Any, Set
from enum import Enum, auto
from functools import reduce

import numpy as np

from MDANSE.MLogging import LOG
from MDANSE.Framework.OutputVariables.IOutputVariable import OutputData
from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem


class GroupingLevel(Enum):

    ATOM = auto()
    MOL_EACH = auto()
    MOL_AVERAGE = auto()


GROUPING_LABELS = {
    "atom": GroupingLevel.ATOM,
    "individual molecules" : GroupingLevel.MOL_EACH,
    "average over molecules" : GroupingLevel.MOL_AVERAGE,
}

BACKUP_DATA_PARAMETERS ={
            "axis": "index",
            "units": "au",
            "main_result": False,
            "partial_result": True,
            "dtype": np.float64
}


class GroupingTool:
    """This object will handle the analysis results and assign the
    correct results to different datasets based on the grouping
    setting"""

    def __init__(self, chemical_system: ChemicalSystem, output_data: OutputData):
        self._cs = chemical_system
        self._output_data = output_data
        self._grouping = None
        self._data_parameters = {}
        self._mandatory_keys = ["output_type", "dimensions"]
        self._extra_keys = ["axis", "unit", "main_result", "partial_result", "dtype"]
    
    def set_grouping(self, text_key: str):
        self._grouping = GROUPING_LABELS.get(text_key, GroupingLevel.ATOM)
    
    def set_dataset_parameters(self, parameters: dict[str, Any]):
        for key in self._mandatory_keys:
            if key not in parameters:
                raise KeyError(f"Setting {key} is missing from data parameters.")
        for key in self._mandatory_keys:
            self._data_parameters[key] = parameters[key]
        for key in self._extra_keys:
            value = parameters.get(key)
            if value is None:
                value = BACKUP_DATA_PARAMETERS[key]
            self._data_parameters[key] = value
    
    def add_dataset(self, name):
        self._output_data.add(name,
                              self._data_parameters["output_type"],
                              self._data_parameters["dimensions"],
                              **{key: self._data_parameters[key] for key in self._extra_keys})

    def create_result_groups(self, name: str):
        if self._data_parameters is None:
            raise RuntimeError("Creating output data groups without parameters.")
        self.create_atom_groups(name)
        if self._grouping == GroupingLevel.MOL_AVERAGE:
            self.create_averaged_molecule_groups(name)
        elif self._grouping == GroupingLevel.MOL_EACH:
            self.create_individual_molecule_groups(name)
    
    def create_atom_groups(self, name: str):
        for atom in self._cs._unique_elements:
            self.add_dataset("_".join([name, str(atom)]))

