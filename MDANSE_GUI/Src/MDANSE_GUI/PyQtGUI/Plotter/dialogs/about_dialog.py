# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/Plotter/__init__.py
# @brief     root file of Plotter
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2023-now
# @authors   Eric Pellegrini
#
# **************************************************************************

import platform

import h5py
import netCDF4

from qtpy import QtCore, QtWidgets

from MDANSE_GUI.PyQtGUI.Plotter.__pkginfo__ import __version__
from MDANSE_GUI.PyQtGUI.Plotter.icons import ICONS


class AboutDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        """Constructor.

        Args:
            parent (qtpy.QtWidgets.QWidget): the parent widget
        """
        super(AboutDialog, self).__init__(parent)

        self._build()

        self.setWindowTitle("About Plotter")

    def _build(self):
        """Build the dialog."""
        main_layout = QtWidgets.QVBoxLayout()

        message = """
        <dl>
            <dt><b>Plotter version</b></dt><dd>{Plotter_version}</dd>
            <dt><b>HDF5 version</b></dt><dd>{hdf5_version}</dd>
            <dt><b>h5py version</b></dt><dd>{h5py_version}</dd>
            <dt><b>NetCDF version</b></dt><dd>{netcdf_version}</dd>
            <dt><b>Qt version</b></dt><dd>{qt_version}</dd>
            <dt><b>PyQt version</b></dt><dd>{pyqt_version}</dd>
            <dt><b>Python version</b></dt><dd>{python_version}</dd>
            <dt><b>System</b></dt><dd>{system}</dd>
            <dt><b>Distribution</b></dt><dd>{distribution}</dd>
            <dt><b>Processor</b></dt><dd>{processor}</dd>
        </dl>
        <hr>
        <p>
        Copyright (C) <a href="{ill_url}">Institut Laue Langevin</a>
        </p>
        <hr>
        Bug report/feature request: pellegrini[at]ill.fr
        """

        uname = platform.uname()

        info = {
            "Plotter_version": __version__,
            "h5py_version": h5py.version.version,
            "hdf5_version": h5py.version.hdf5_version,
            "netcdf_version": netCDF4.__netcdf4libversion__,
            "qt_version": QtCore.qVersion(),
            "pyqt_version": QtCore.PYQT_VERSION_STR,
            "python_version": platform.python_version(),
            "ill_url": "http://www.ill.eu",
            "system": uname.system,
            "processor": uname.processor,
            "distribution": uname.version,
            "processor": uname.processor,
        }

        label = QtWidgets.QLabel()
        label.setOpenExternalLinks(True)
        label.setText(message.format(**info))

        main_layout.addWidget(label)

        self.setLayout(main_layout)

        self.setFixedSize(420, 465)
