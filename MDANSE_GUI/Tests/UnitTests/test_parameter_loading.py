from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pytest
from qtpy.QtCore import QMessageLogger
from qtpy.QtWidgets import QMainWindow

from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Formats.HDFFormat import get_input_params
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.Jobs.NeutronDynamicTotalStructureFactor import NeutronDynamicTotalStructureFactor
from MDANSE.Framework.Jobs.StructureFactorFromScatteringFunction import StructureFactorFromScatteringFunction
from MDANSE_GUI.Session.Session import LocalSession
from MDANSE_GUI.Session.Settings import LocalSettings
from MDANSE_GUI.Tabs.ConverterTab import ConverterTab
from MDANSE_GUI.Tabs.JobTab import JobTab
from MDANSE_GUI.Tabs.Models.JobTree import JobTree
from MDANSE_GUI.Tabs.Models.TrajectoryModel import TrajectoryModel

CONVERTER_SUBCLASSES = Converter.raw_dict()
ENABLED_CONVERTERS = {key: val for key, val in CONVERTER_SUBCLASSES.items() if val.visible}
IJOB_SUBCLASSES = IJob.raw_dict()
ENABLED_JOBS = {key: val for key, val in IJOB_SUBCLASSES.items() if val.visible}


DATA_DIR = Path(__file__).parents[3] / "MDANSE/Tests/UnitTests/Converted"
DATA_DIR_ANALYSIS = Path(__file__).parents[3] / "MDANSE/Tests/UnitTests/Results"


NeutronDynamicTotalStructureFactor.settings["dcsf_input_file"][1]["default"] = Path(__file__).parent / "dcsf.mda"
NeutronDynamicTotalStructureFactor.settings["disf_input_file"][1]["default"] = Path(__file__).parent / "disf.mda"
StructureFactorFromScatteringFunction.settings["dcsf_input_file"][1]["default"] = Path(__file__).parent / "dcsf.mda"

CONVERTER_OUTPUTS = {
                "LAMMPS": "lammps_cao.mdt",
                "VASP": "vasp.mdt",
                "CP2K": "cp2k_velocity.mdt",
                "CHARMM": "hem_cam.mdt",
                "ASE": "ase_janus.mdt",
                "DL_POLY": "dlp_with_grad.mdt",
                "NAMD": "namd.mdt",
                "CASTEP": "castep.mdt",
                "DFTB": "dftb.mdt",
                "FORCITE": "forcite.mdt",
                "GROMACS": "gromacs-nvt.mdt",
                "MDANALYSIS": "md.mdt",
                "MDTRAJ": "hem_cam.mdt",
}

ANALYSIS_OUTPUTS = {
    'AreaPerMolecule': "structure_analysis_AreaPerMolecule.mda",
    'VelocityCorrelationFunction': "dynamics_analysis_short_traj_VelocityCorrelationFunction.mda",
    'VanHoveFunctionDistinct': "dynamics_analysis_short_traj_VanHoveFunctionDistinct.mda",
    'CoordinationNumber': "structure_analysis_com_traj_CoordinationNumber.mda",
    'CurrentCorrelationFunction': "ccf_short_traj.mda",
    'Density': "density_short_traj.mda",
    'DensityOfStates': "dos_Gaussian.mda",
    'DipoleAutoCorrelationFunction': "dacf_analysis.mda",
    'DynamicCoherentStructureFactor': "dcsf_short_traj.mda",
    'DynamicIncoherentStructureFactor': "disf_short_traj.mda",
    'Eccentricity': "structure_analysis_com_traj_Eccentricity.mda",
    'ElasticIncoherentStructureFactor': "eisf_short_traj.mda",
    'GaussianDynamicIncoherentStructureFactor': "gdisf_short_traj.mda",
    'Infrared': "ir_analysis.mda",
    'MeanSquareDisplacement': "dynamics_analysis_short_traj_MeanSquareDisplacement.mda",
    'MolecularTrace': "structure_analysis_short_traj_MolecularTrace.mda",
    'NeutronDynamicTotalStructureFactor': "ndtsf.mda",
    'PairDistributionFunction': "structure_analysis_short_traj_PairDistributionFunction.mda",
    'PositionCorrelationFunction': "dynamics_analysis_short_traj_PositionCorrelationFunction.mda",
    'PositionPowerSpectrum': "dynamics_analysis_short_traj_PositionPowerSpectrum.mda",
    'RadiusOfGyration': "structure_analysis_short_traj_RadiusOfGyration.mda",
    'RootMeanSquareDeviation': "structure_analysis_short_traj_RootMeanSquareDeviation.mda",
    'RootMeanSquareFluctuation': "structure_analysis_short_traj_RootMeanSquareFluctuation.mda",
    'ScatteringLengthDensityProfile': "sldp_short_traj.mda",
    'SolventAccessibleSurface': "structure_analysis_short_traj_SolventAccessibleSurface.mda",
    'StaticStructureFactor': "structure_analysis_short_traj_StaticStructureFactor.mda",
    'StaticStructureFactor3D': "ssf3d_nonorthogonal_cell.mda",
    'StructureFactorFromScatteringFunction': "sffsf_short_traj.mda",
    'Temperature': "temperature_short_traj_1.mda",
    'VanHoveFunctionSelf': "dynamics_analysis_short_traj_VanHoveFunctionSelf.mda",
    'Voronoi': "structure_analysis_short_traj_Voronoi.mda",
    'XRayStaticStructureFactor': "structure_analysis_short_traj_XRayStaticStructureFactor.mda"
}


def fix_paths(temp_params: dict[str, Any]) -> dict[str, Any]:
    new_params = {}
    for key, value in temp_params.items():
        if isinstance(value, str):
            if value.split('/')[-1] == "output_dcsf.mda":
                new_params[key] = str(DATA_DIR_ANALYSIS / "dcsf_short_traj.mda")
            elif value.endswith(".mda"):
                new_params[key] = str(DATA_DIR_ANALYSIS / value.split('/')[-1])
            elif value.endswith(".mdt"):
                new_params[key] = str(DATA_DIR / value.split('/')[-1])
            else:
                new_params[key] = value
        else:
            new_params[key] = value
    return new_params


@pytest.fixture
def trajectory():
    traj_path = DATA_DIR / "lammps_fakecell.mdt"
    yield traj_path, "dummy"


@pytest.mark.parametrize(
    "index", enumerate(sorted(ENABLED_CONVERTERS), 1), ids=lambda x: x[1]
)
def test_converter_parameters_load(qapp, qtbot, caplog, index):
    """
    Test there are no major errors in constructing job widgets.

    This includes raises in the construction of widgets and missing widgets.
    """
    index, key = index
    if key not in CONVERTER_OUTPUTS:
        return
    window = QMainWindow()

    widget = ConverterTab.gui_instance(
        parent=window,
        name="Converter",
        session=LocalSession(),
        settings=LocalSettings(),
        logger=QMessageLogger(),
    )
    widget._core.setParent(window)
    window.show()
    qtbot.addWidget(window)

    view = widget._view

    model = widget._model

    item = model._nodes[index]
    ind = model.indexFromItem(item)
    view.on_select_action(ind)

    traj_file = DATA_DIR / CONVERTER_OUTPUTS[key]
    parameters = get_input_params(traj_file)
    parameters = fix_paths(parameters)
    widget.action.apply_parameters(parameters)

    assert "Traceback" not in caplog.text, "Error raised with traceback."
    assert "ERROR" not in caplog.text, "Error raised."
    assert item.text() == key


@pytest.mark.parametrize(
    "index", enumerate(sorted(ENABLED_JOBS), 1), ids=lambda x: x[1]
)
def test_job_widgets_load(qapp, qtbot, caplog, trajectory, index):
    """
    Test there are no major errors in constructing job widgets.

    This includes raises in the construction of widgets and missing widgets.
    """

    index, key = index
    if key not in ANALYSIS_OUTPUTS:
        return
    window = QMainWindow()

    widget = JobTab.gui_instance(
        parent=window,
        name="Job",
        session=LocalSession(),
        settings=LocalSettings(),
        logger=QMessageLogger(),
        model=JobTree(parent_class=IJob),
        combo_model=TrajectoryModel(),
    )
    widget._core.setParent(window)

    traj_model = widget._trajectory_combo.model()

    with qtbot.waitSignal(traj_model.finished_loading):
        traj_model.append_object(trajectory)

    widget._trajectory_combo.setCurrentIndex(0)

    # Clear warnings from loading trajectory
    caplog.clear()

    window.show()
    qtbot.addWidget(window)

    view = widget._view

    model = widget._model

    item = model._nodes[index]
    ind = model.indexFromItem(item)
    view.on_select_action(ind)

    mda_file = DATA_DIR_ANALYSIS / ANALYSIS_OUTPUTS[key]
    parameters = get_input_params(mda_file)
    parameters = fix_paths(parameters)
    widget.action.apply_parameters(parameters)

    print(caplog.text)

    assert "Traceback" not in caplog.text, "Error raised with traceback."
    assert "ERROR" not in caplog.text, "Error raised."
    assert item.text() == key
