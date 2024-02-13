# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/__init__.py
# @brief     Implements module/class/test __init__
#
# @homepage https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************


def main():
    from qtpy.QtWidgets import QApplication
    from MDANSE_GUI.Plotter.widgets.main_window import MainWindow
    import sys

    app = QApplication(sys.argv)
    root = MainWindow(None)
    root.show()
    app.exec()


if __name__ == "__main__":
    main()
