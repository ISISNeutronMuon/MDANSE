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

import platform

import h5py

from qtpy import QtCore, QtWidgets

import MDANSE_GUI


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
            "Plotter_version": MDANSE_GUI.__version__,
            "h5py_version": h5py.version.version,
            "hdf5_version": h5py.version.hdf5_version,
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
