from __future__ import annotations

import logging
from pathlib import Path

import pytest
from qtpy.QtCore import QMessageLogger
from qtpy.QtWidgets import QMainWindow

from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.Jobs.NeutronDynamicTotalStructureFactor import NeutronDynamicTotalStructureFactor
from MDANSE.Framework.Jobs.StructureFactorFromScatteringFunction import StructureFactorFromScatteringFunction
from MDANSE_GUI.Session.Session import LocalSession
from MDANSE_GUI.Session.Settings import LocalSettings
from MDANSE_GUI.Tabs.ConverterTab import ConverterTab
from MDANSE_GUI.Tabs.JobTab import JobTab
from MDANSE_GUI.Tabs.Models.JobTree import JobTree
from MDANSE_GUI.Tabs.Models.TrajectoryModel import TrajectoryModel

CONVERTER_SUBCLASSES = Converter.indirect_subclass_dictionary()
ENABLED_CONVERTERS = {
    key: val for key, val in CONVERTER_SUBCLASSES.items() if val.enabled
}
IJOB_SUBCLASSES = IJob.indirect_subclass_dictionary()
ENABLED_JOBS = {key: val for key, val in IJOB_SUBCLASSES.items() if val.enabled}


DATA_DIR = Path(__file__).parents[3] / "MDANSE/Tests/UnitTests/Converted"


NeutronDynamicTotalStructureFactor.settings["dcsf_input_file"][1]["default"] = Path(__file__).parent / "dcsf.mda"
NeutronDynamicTotalStructureFactor.settings["disf_input_file"][1]["default"] = Path(__file__).parent / "disf.mda"
StructureFactorFromScatteringFunction.settings["dcsf_input_file"][1]["default"] = Path(__file__).parent / "dcsf.mda"

@pytest.fixture
def trajectory():
    traj_path = DATA_DIR / "lammps_fakecell.mdt"
    yield traj_path, "dummy"


@pytest.mark.parametrize(
    "typ, exp",
    (
        [Converter, ENABLED_CONVERTERS],
        [IJob, ENABLED_JOBS],
    ),
    ids=["Converter", "IJob"],
)
def test_jobtree(typ, exp):
    """Test job tree contains all enabled jobs."""
    tree = JobTree(parent_class=typ)
    assert {item.text() for item in tree._nodes.values()} == set(exp)


@pytest.mark.parametrize(
    "index", enumerate(sorted(ENABLED_CONVERTERS), 1), ids=lambda x: x[1]
)
def test_converter_widgets_load(qapp, qtbot, caplog, index):
    """
    Test there are no major errors in constructing job widgets.

    This includes raises in the construction of widgets and missing widgets.
    """
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

    index, key = index

    view = widget._view

    model = widget._model

    item = model._nodes[index]
    ind = model.indexFromItem(item)
    view.on_select_action(ind)

    assert "Traceback" not in caplog.text, "Error raised with traceback."
    assert "WARNING" not in caplog.text, "Warning raised."
    assert "Could not find the right widget" not in caplog.text, "Missing widget."
    assert item.text() == key


@pytest.mark.parametrize(
    "index", enumerate(sorted(ENABLED_JOBS), 1), ids=lambda x: x[1]
)
def test_job_widgets_load(qapp, qtbot, caplog, trajectory, index):
    """
    Test there are no major errors in constructing job widgets.

    This includes raises in the construction of widgets and missing widgets.
    """
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

    index, key = index

    view = widget._view

    model = widget._model

    item = model._nodes[index]
    ind = model.indexFromItem(item)
    view.on_select_action(ind)

    print(caplog.text)

    assert "Traceback" not in caplog.text, "Error raised with traceback."
    assert "WARNING" not in caplog.text, "Warning raised."
    assert "Could not find the right widget" not in caplog.text, "Missing widget."
    assert item.text() == key
