# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/InputData/InputFileData.py
# @brief     Implements module/class/test InputFileData
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import abc
import os

from MDANSE.Framework.InputData.IInputData import IInputData


class InputFileData(IInputData):
    def __init__(self, filename, load=True):
        IInputData.__init__(self, filename)

        self._basename = os.path.basename(filename)
        self._dirname = os.path.dirname(filename)

        if load:
            self.load()

    @property
    def filename(self):
        """
        Returns the filename associated with the input data.

        :return: the filename associated with the input data.
        :rtype: str
        """

        return self._name

    @property
    def shortname(self):
        """
        Returns the shortname of the file associated with the input data.

        :return: the shortname of the file associated with the input data.
        :rtype: str
        """

        return self._basename

    @property
    def basename(self):
        """
        Returns the basename of the file associated with the input data.

        :return: the basename of the file associated with the input data.
        :rtype: str
        """

        return self._basename

    @property
    def dirname(self):
        return self._dirname

    @abc.abstractmethod
    def load(self):
        pass

    @abc.abstractmethod
    def close(self):
        pass
