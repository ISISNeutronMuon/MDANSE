# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/RegistryViewer.py
# @brief     Shows the MDANSE jobs. Can run standalone.
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************


from qtpy.QtCore import QObject, Slot, Signal
from qtpy.QtWidgets import QWidget

from MDANSE.Framework.Jobs.IJob import IJob

from MDANSE_GUI.Tabs.GeneralTab import GeneralTab
from MDANSE_GUI.Tabs.Layouts.DoublePanel import DoublePanel
from MDANSE_GUI.Session.LocalSession import LocalSession
from MDANSE_GUI.Tabs.Visualisers.TextInfo import TextInfo
from MDANSE_GUI.Tabs.Models.JobHolder import JobHolder
from MDANSE_GUI.Tabs.Views.RunTable import RunTable


run_tab_label = """This table shows the status of jobs
which have been started in your session.
You can check which jobs were successful,
and if they failed, you can see the details
of the error message.
"""


class RunTab(GeneralTab):
    """The tab for tracking the progress of running jobs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def standard_instance(cls):
        the_tab = cls(
            window,
            name="RunMonitor",
            model=JobHolder(),
            view=RunTable(),
            visualiser=TextInfo(
                header="MDANSE Analysis Output",
                footer="Look up our Read The Docs page:"
                + "https://mdanse.readthedocs.io/en/protos/",
            ),
            layout=DoublePanel,
            label_text=run_tab_label,
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
        the_tab = cls(
            parent,
            name=name,
            session=session,
            settings=settings,
            logger=logger,
            model=kwargs.get("model", JobHolder()),
            view=RunTable(),
            visualiser=TextInfo(
                header="MDANSE Analysis",
                footer="Look up our "
                + '<a href="https://mdanse.readthedocs.io/en/protos/">Read The Docs</a>'
                + " page.",
            ),
            layout=DoublePanel,
            label_text=run_tab_label,
        )
        return the_tab


if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication, QMainWindow, QVBoxLayout

    app = QApplication(sys.argv)
    window = QMainWindow()
    the_tab = RunTab(
        window,
        name="RunningJobs",
        model=JobHolder(),
        view=RunTable(),
        visualiser=TextInfo(),
        layout=DoublePanel,
        label_text=run_tab_label,
    )
    window.setCentralWidget(the_tab._core)
    window.show()
    app.exec()