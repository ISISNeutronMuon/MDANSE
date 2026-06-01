from __future__ import annotations

import logging
from pathlib import Path

import pytest
from qtpy.QtCore import QMessageLogger
from qtpy.QtWidgets import QMainWindow

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.QVectors.IQVectors import IQVectors
from MDANSE_GUI.Session.Session import LocalSession
from MDANSE_GUI.Session.Settings import LocalSettings
from MDANSE_GUI.Tabs.JobTab import JobTab
from MDANSE_GUI.Tabs.Models.JobTree import JobTree
from MDANSE_GUI.Tabs.Models.TrajectoryModel import TrajectoryModel


IJOB_SUBCLASSES = IJob.indirect_subclass_dictionary()
ENABLED_JOBS = {key: val for key, val in IJOB_SUBCLASSES.items() if val.enabled}
ENABLED_QVECTORS = set(IQVectors.indirect_subclasses()) - {
    "IQVectors",
    "LatticeQVectors",
}

DATA_DIR = Path(__file__).parents[3] / "MDANSE/Tests/UnitTests/Converted"


@pytest.fixture
def trajectory():
    traj_path = DATA_DIR / "lammps.mdt"
    yield traj_path, "dummy"


@pytest.mark.parametrize("qvector_type", ENABLED_QVECTORS)
def test_job_widgets_load(qapp, qtbot, caplog, trajectory, qvector_type):
    """
    Test there are no major errors in constructing job widgets.

    This includes raises in the construction of widgets and missing widgets.
    """
    window = QMainWindow()
    curr_job_name = "DynamicCoherentStructureFactor"
    index = [
        job_index
        for job_index, job_name in enumerate(sorted(ENABLED_JOBS), 1)
        if job_name == curr_job_name
    ][0]

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

    window.show()
    qtbot.addWidget(window)

    view = widget._view

    action = widget._visualiser

    model = widget._model

    item = model._nodes[index]
    ind = model.indexFromItem(item)
    view.on_select_action(ind)

    widget_index = [
        windex
        for windex, widget_key in enumerate(action._widgets_in_layout.keys())
        if widget_key == "q_vectors"
    ][0]
    qvec_widget = action._widgets[widget_index]
    if "SphericalLattice" in qvector_type:
        with qtbot.waitSignal(qvec_widget.value_changed):
            qvec_widget._selector.selection = "SphericalQVectors"
    caplog.clear()

    with qtbot.waitSignal(qvec_widget.value_changed):
        qvec_widget._selector.selection = qvector_type

    print(caplog.text)
    print(qvector_type)

    assert "Traceback" not in caplog.text, "Error raised with traceback."
    if "Lattice" in qvector_type and "Dispersion" not in qvector_type:
        assert "WARNING" in caplog.text, "Warning not raised."
    else:
        assert "WARNING" not in caplog.text, "Warning raised."
