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
from MDANSE_GUI.InputWidgets.AseInputFileWidget import AseInputFileWidget
from MDANSE_GUI.InputWidgets.AtomMappingWidget import AtomMappingWidget
from MDANSE_GUI.InputWidgets.AtomSelectionWidget import AtomSelectionWidget
from MDANSE_GUI.InputWidgets.AtomTransmutationWidget import AtomTransmutationWidget
from MDANSE_GUI.InputWidgets.BackupWidget import BackupWidget
from MDANSE_GUI.InputWidgets.BooleanWidget import BooleanWidget
from MDANSE_GUI.InputWidgets.ComboWidget import ComboWidget
from MDANSE_GUI.InputWidgets.CorrelationFramesWidget import CorrelationFramesWidget
from MDANSE_GUI.InputWidgets.DerivativeOrderWidget import DerivativeOrderWidget
from MDANSE_GUI.InputWidgets.DistHistCutoffWidget import DistHistCutoffWidget
from MDANSE_GUI.InputWidgets.FloatWidget import FloatWidget
from MDANSE_GUI.InputWidgets.FramesWidget import FramesWidget
from MDANSE_GUI.InputWidgets.HDFTrajectoryWidget import HDFTrajectoryWidget
from MDANSE_GUI.InputWidgets.InputDirectoryWidget import InputDirectoryWidget
from MDANSE_GUI.InputWidgets.InputFileWidget import InputFileWidget, OptionalInputFileWidget
from MDANSE_GUI.InputWidgets.InstrumentResolutionWidget import InstrumentResolutionWidget
from MDANSE_GUI.InputWidgets.IntegerWidget import IntegerWidget
from MDANSE_GUI.InputWidgets.InterpolationOrderWidget import InterpolationOrderWidget
from MDANSE_GUI.InputWidgets.MDAnalysisCoordinateFileWidget import MDAnalysisCoordinateFileWidget
from MDANSE_GUI.InputWidgets.MDAnalysisMDTrajTimeStepWidget import MDAnalysisMDTrajTimeStepWidget
from MDANSE_GUI.InputWidgets.MDAnalysisTopologyFileWidget import MDAnalysisTopologyFileWidget
from MDANSE_GUI.InputWidgets.MDTrajTopologyFileWidget import MDTrajTopologyFileWidget
from MDANSE_GUI.InputWidgets.MoleculeWidget import MoleculeWidget
from MDANSE_GUI.InputWidgets.MultiInputFileWidget import MultiInputFileWidget
from MDANSE_GUI.InputWidgets.MultipleCombosWidget import MultipleCombosWidget
from MDANSE_GUI.InputWidgets.NewQVectorsWidget import NewQVectorsWidget
from MDANSE_GUI.InputWidgets.OptionalFloatWidget import OptionalFloatWidget
from MDANSE_GUI.InputWidgets.OutputDirectoryWidget import OutputDirectoryWidget
from MDANSE_GUI.InputWidgets.OutputFilesWidget import OutputFilesWidget
from MDANSE_GUI.InputWidgets.OutputStructureWidget import OutputStructureWidget
from MDANSE_GUI.InputWidgets.OutputTrajectoryWidget import OutputTrajectoryWidget
from MDANSE_GUI.InputWidgets.PartialChargeWidget import PartialChargeWidget
from MDANSE_GUI.InputWidgets.ProjectionWidget import ProjectionWidget
from MDANSE_GUI.InputWidgets.QVectorsWidget import QVectorsWidget
from MDANSE_GUI.InputWidgets.RangeWidget import RangeWidget
from MDANSE_GUI.InputWidgets.RunningModeWidget import RunningModeWidget
from MDANSE_GUI.InputWidgets.StringWidget import StringWidget
from MDANSE_GUI.InputWidgets.UnitCellWidget import UnitCellWidget
from MDANSE_GUI.InputWidgets.VectorWidget import VectorWidget


WIDGET_LOOKUP = {
    "FloatConfigurator": FloatWidget,
    "OptionalFloatConfigurator": OptionalFloatWidget,
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
    "MDAnalysisCoordinateFileConfigurator": MDAnalysisCoordinateFileWidget,
    "InputFileConfigurator": InputFileWidget,
    "MDAnalysisTopologyFileConfigurator": MDAnalysisTopologyFileWidget,
    "MDFileConfigurator": InputFileWidget,
    "FieldFileConfigurator": InputFileWidget,
    "XDATCARFileConfigurator": InputFileWidget,
    "XTDFileConfigurator": InputFileWidget,
    "XYZFileConfigurator": InputFileWidget,
    "OptionalXYZFileConfigurator": InputFileWidget,
    "RunningModeConfigurator": RunningModeWidget,
    "WeightsConfigurator": ComboWidget,
    "MultipleChoicesConfigurator": MultipleCombosWidget,
    "MoleculeSelectionConfigurator": MoleculeWidget,
    "GroupingLevelConfigurator": ComboWidget,
    "SingleChoiceConfigurator": ComboWidget,
    "QVectorsConfigurator": QVectorsWidget,
    "NewQVectorsConfigurator": NewQVectorsWidget,
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
    "UnitCellConfigurator": UnitCellWidget,
    "MDAnalysisTimeStepConfigurator": MDAnalysisMDTrajTimeStepWidget,
    "MDTrajTimeStepConfigurator": MDAnalysisMDTrajTimeStepWidget,
    "MDTrajTrajectoryFileConfigurator": MultiInputFileWidget,
    "MDTrajTopologyFileConfigurator": MDTrajTopologyFileWidget,
    "VectorInputFileConfigurator": OptionalInputFileWidget,
}
