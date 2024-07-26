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
from typing import Optional

import numpy as np
from qtpy.QtWidgets import (
    QPushButton,
    QFileDialog,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QCheckBox,
    QTextEdit,
)
from qtpy.QtCore import Signal, Slot

from MDANSE.MLogging import LOG
from MDANSE.Framework.Jobs.IJob import IJob

from MDANSE_GUI.InputWidgets import *


widget_lookup = {  # these all come from MDANSE_GUI.InputWidgets
    "FloatConfigurator": FloatWidget,
    "BooleanConfigurator": BooleanWidget,
    "StringConfigurator": StringWidget,
    "IntegerConfigurator": IntegerWidget,
    "CorrelationFramesConfigurator": CorrelationFramesWidget,
    "FramesConfigurator": FramesWidget,
    "RangeConfigurator": RangeWidget,
    "DistHistCutoffConfigurator": DistHistCutoffWidget,
    "VectorConfigurator": VectorWidget,
    "HDFInputFileConfigurator": InputFileWidget,
    "HDFTrajectoryConfigurator": HDFTrajectoryWidget,
    "DerivativeOrderConfigurator": DerivativeOrderWidget,
    "InterpolationOrderConfigurator": InterpolationOrderWidget,
    "OutputFilesConfigurator": OutputFilesWidget,
    "ASEFileConfigurator": InputFileWidget,
    "AseInputFileConfigurator": AseInputFileWidget,
    "ConfigFileConfigurator": InputFileWidget,
    "InputFileConfigurator": InputFileWidget,
    "MDFileConfigurator": InputFileWidget,
    "FieldFileConfigurator": InputFileWidget,
    "XDATCARFileConfigurator": InputFileWidget,
    "XTDFileConfigurator": InputFileWidget,
    "XYZFileConfigurator": InputFileWidget,
    "RunningModeConfigurator": RunningModeWidget,
    "WeightsConfigurator": ComboWidget,
    "MultipleChoicesConfigurator": MultipleCombosWidget,
    "MoleculeSelectionConfigurator": MoleculeWidget,
    "GroupingLevelConfigurator": ComboWidget,
    "SingleChoiceConfigurator": ComboWidget,
    "QVectorsConfigurator": QVectorsWidget,
    "InputDirectoryConfigurator": InputDirectoryWidget,
    "OutputDirectoryConfigurator": OutputDirectoryWidget,
    "OutputStructureConfigurator": OutputStructureWidget,
    "OutputTrajectoryConfigurator": OutputTrajectoryWidget,
    "ProjectionConfigurator": ProjectionWidget,
    "AtomSelectionConfigurator": AtomSelectionWidget,
    "AtomMappingConfigurator": AtomMappingWidget,
    "AtomTransmutationConfigurator": AtomTransmutationWidget,
    "InstrumentResolutionConfigurator": InstrumentResolutionWidget,
    "PartialChargeConfigurator": PartialChargeWidget,
}


class SimpleInstrument:

    def __init__(self) -> None:
        self._sample = "isotropic"
        self._technique = "QENS"
        self._resolution_type = "Gaussian"
        self._resolution_fwhm = 0.1
        self._resolution_unit = "meV"
        self._q_min = 0.1
        self._q_max = 10.0
        self._q_unit = "1/ang"

    def create_resolution_params(self):
        pass


class InstrumentDetails(QWidget):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        