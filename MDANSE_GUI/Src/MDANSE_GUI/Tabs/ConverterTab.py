# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      MDANSE_GUI/Tabs/ConverterTab.py
# @brief     Shows the MDANSE jobs. Can run standalone.
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************
from functools import partial
from qtpy.QtCore import Slot
from qtpy.QtWidgets import QWidget

from MDANSE.Framework.Converters.Converter import Converter

from MDANSE_GUI.Tabs.GeneralTab import GeneralTab
from MDANSE_GUI.Tabs.Layouts.TriplePanel import TriplePanel
from MDANSE_GUI.Session.LocalSession import LocalSession
from MDANSE_GUI.Tabs.Visualisers.TextInfo import TextInfo
from MDANSE_GUI.Tabs.Visualisers.Action import Action
from MDANSE_GUI.Tabs.Models.JobTree import JobTree
from MDANSE_GUI.Tabs.Views.ActionsTree import ActionsTree


tab_label = """Convert your trajectory to the MDANSE MDT format.
If you cannot find the converter for your MD engine, the
ASE converter can be tried as a backup option.
"""


class ConverterTab(GeneralTab):
    """The tab for choosing and starting a new job."""

    def __init__(self, *args, **kwargs):
        self.action = kwargs.pop("action")
        super().__init__(*args, **kwargs)
        self._current_trajectory = ""
        self._job_starter = None

    def set_job_starter(self, job_starter):
        self._job_starter = job_starter
        self.action.new_thread_objects.connect(self._job_starter.startThread)

    @Slot(str)
    def set_current_trajectory(self, new_name: str):
        self._current_trajectory = new_name

    @classmethod
    def standard_instance(cls):
        action = Action()
        the_tab = cls(
            window,
            name="AvailableJobs",
            model=JobTree(parent_class=Converter),
            view=ActionsTree(),
            visualiser=TextInfo(
                header="MDANSE Converter",
                footer="Look up our Read The Docs page:"
                + "https://mdanse.readthedocs.io/en/protos/",
            ),
            layout=partial(TriplePanel, action=action),
            label_text=tab_label,
            action=action,
        )
        return the_tab

    @classmethod
    def gui_instance(
        cls,
        parent: QWidget,
        name: str,
        session: LocalSession,
        settings,
        logger,
        **kwargs,
    ):
        action = Action()
        the_tab = cls(
            parent,
            name=name,
            session=session,
            settings=settings,
            logger=logger,
            model=kwargs.get("model", JobTree(parent_class=Converter)),
            view=ActionsTree(),
            visualiser=TextInfo(
                header="MDANSE Converter",
                footer="Look up our "
                + '<a href="https://mdanse.readthedocs.io/en/protos/">Read The Docs</a>'
                + " page.",
            ),
            layout=partial(TriplePanel, action=action),
            label_text=tab_label,
            action=action,
        )
        return the_tab


if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)
    window = QMainWindow()
    action = Action()
    the_tab = ConverterTab(
        window,
        name="AvailableJobs",
        model=JobTree(parent_class=Converter),
        view=ActionsTree(),
        visualiser=TextInfo(
            header="MDANSE Converters",
            footer="Look up our "
            + '<a href="https://mdanse.readthedocs.io/en/protos/">Read The Docs</a>'
            + " page.",
        ),
        layout=partial(TriplePanel, action=action),
        label_text=tab_label,
        action=action,
    )
    the_tab._current_trajectory = "/Users/maciej.bartkowiak/an_example/BLAH.mdt"
    window.setCentralWidget(the_tab._core)
    window.show()
    app.exec()
