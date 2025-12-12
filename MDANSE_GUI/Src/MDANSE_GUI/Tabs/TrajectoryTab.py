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
from __future__ import annotations

import os
from functools import partial
from pathlib import Path

from qtpy.QtCore import Slot
from qtpy.QtWidgets import QFileDialog, QWidget

from MDANSE_GUI.MolecularViewer.MolecularViewer import MolecularViewerExtended
from MDANSE_GUI.Session.Session import Session
from MDANSE_GUI.Tabs.GeneralTab import GeneralTab
from MDANSE_GUI.Tabs.Layouts.MultiPanel import MultiPanel
from MDANSE_GUI.Tabs.Models.GeneralModel import GeneralModel
from MDANSE_GUI.Tabs.Views.TrajectoryView import TrajectoryView
from MDANSE_GUI.Tabs.Visualisers.TrajectoryInfo import TrajectoryInfo
from MDANSE_GUI.Tabs.Visualisers.View3D import View3D

label_text = """<b>Load and view trajectories.</b>
<br><br>
Any trajectory you select will be visualised in the 3D view window on the right side.
The animation of the MD trajectory will allow you to verify if the contents
of the trajectory are what you expected.
<br><br>
You can load .mdt trajectories created using MDANSE converters, or
H5MD trajectories, as long as they contain physical unit information.
<br><br>
Additionally, atom trace plotting option is available in the right panel.
Choose an atom by clicking on it, and visualise the volume occupied by
the atom over all simulation frames.
"""


class TrajectoryTab(GeneralTab):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._core.add_button("Load .MDT Trajectories", self.load_trajectories)
        self._model.finished_loading.connect(self.tab_notification)

    @Slot()
    def load_trajectories(self):
        fnames = QFileDialog.getOpenFileNames(
            self._core,
            "Load an MD trajectory",
            str(self.get_path("trajectory")),
            "HDF5 files, MDANSE or H5MD format (*.mdt *.h5);;H5MD files (*.h5);;All files (*)",
        )

        loaded_files = []  # list to store loaded files for recent files tracking

        for fname in fnames[0]:
            self.load_trajectory(fname)
            filepath = Path(fname)
            last_path = str(filepath.parent)
            loaded_files.append(str(filepath))
            self.set_path("trajectory", last_path)
            self._session.save()

    @Slot(str)
    def load_trajectory(self, fname: str):
        fpath = Path(fname)
        if len(fname) > 0:
            short_name = fpath.name
            self._core._model.append_object((fname, short_name))
            self._session.protect_filename(fname)

    @classmethod
    def gui_instance(
        cls,
        parent: QWidget,
        name: str,
        session: Session,
        settings,
        logger,
        **kwargs,
    ):
        the_tab = cls(
            parent,
            name=name,
            session=session,
            settings=settings,
            logger=logger,
            model=kwargs.get("model", GeneralModel()),
            view=TrajectoryView(),
            visualiser=View3D(MolecularViewerExtended()),
            layout=partial(
                MultiPanel,
                left_panels=[
                    TrajectoryInfo(
                        header="MDANSE Trajectory",
                        footer="Look up our "
                        + '<a href="https://mdanse.readthedocs.io/en/protos/">Read The Docs</a>'
                        + " page.",
                    )
                ],
            ),
            label_text=label_text,
        )
        the_tab._model.free_name.connect(session.free_filename)
        return the_tab
