# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/Converter.py
# @brief     Implements module/class/test Converter
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from abc import ABCMeta, abstractmethod, abstractclassmethod

import h5py

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Core.SubclassFactory import SubclassFactory


class InteractiveConverter(IJob):
    category = ("InteractiveConverter",)

    _converter_registry = {}
    _next_number = 1

    @classmethod
    def __init_subclass__(cls, regkey=None, **kwargs):
        super().__init_subclass__(**kwargs)
        if regkey is not None:
            cls._converter_registry[regkey] = cls
        else:
            raise ValueError("A regkey keyword parameter is needed in the subclass.")

    @classmethod
    def create(cls, name: str) -> "InteractiveConverter":
        converter_class = cls._converter_registry[name]
        return converter_class

    @classmethod
    def converters(cls):
        return list(cls._converter_registry.keys())

    def __init__(self, *args, **kwargs):
        """Should be called in the derived classes
        using super().
        Initialises the list of Wizard pages,
        which then has to be populated with
        dictionaries of fields.
        """
        self.pages = []

    @abstractmethod
    def getFieldValues(self, page_number: int = 0, values: dict = None) -> dict:
        """Returns the values of the GUI fields
        on the Nth page of the wizard interface.
        It is intended to be used for updating
        the values shown by the GUI, since the GUI
        will be initialised using default values.
        The page numbering starts from 0.
        """
        raise NotImplementedError

    @abstractmethod
    def setFieldValues(self, page_number: int = 0, values: dict = None) -> None:
        """Accepts the values of the input fields from the
        Nth page of the wizard. It uses the same key values
        as those returned by the getFields method.
        """
        raise NotImplementedError

    @abstractmethod
    def systemSummary(self) -> dict:
        """Returns all the information about the simulation
        that is currently stored by the converter. This will
        allow the users to verify if all the information was
        read correctly (or at all). This function must also
        place default values in the fields related to the
        parameters that could not be read.
        """
        raise NotImplementedError

    @abstractmethod
    def guessFromConfig(self, fname: str):
        """Tries to retrieve as much information as possible
        about the simulation to be converted from a config file.

        Arguments
        ---------

        fname (str) - name of the config file to be opened.
        """
        raise NotImplementedError

    @abstractmethod
    def guessFromTrajectory(self, fname: str):
        """Tries to retrieve as much information as possible
        about the simulation to be converted from a trajectory file.
        This will typically mean that the first frame of the trajectory
        will be read and parsed, while the rest of it will be ignored for now.

        Arguments
        ---------

        fname (str) - name of the trajectory file to be opened.
        """
        raise NotImplementedError

    @abstractmethod
    def run_step(self, index: int):
        """This function will be called iteratively in the conversion
        process, until all the requested trajectory frames have been
        converted.

        Arguments:
            index -- number of the next trajectory step to be processed
            by the converter
        """
        pass

    def __len__(self):
        """The length of an InteractiveConverter is the number
        of the Wizard pages it is expected to create.

        Returns:
            int - number of wizard pages needed by the converter
        """
        return len(self.pages)

    def __getitem__(self, index: int):
        if abs(index) >= self.__len__():
            raise IndexError(
                "Trying to access a nonexistent page" " of the InteractiveConverter."
            )
        else:
            return self.pages[index]

    def finalize(self):
        """I am not sure if this function is necessary. The specific converters
        seem to override it with their own version.
        """

        if not hasattr(self, "_trajectory"):
            return

        try:
            output_file = h5py.File(self._trajectory.filename, "a")
            # f = netCDF4.Dataset(self._trajectory.filename,'a')
        except:
            return

        try:
            if "time" in output_file.variables:
                output_file.variables["time"].units = "ps"
                output_file.variables["time"].axis = "time"
                output_file.variables["time"].name = "time"

            if "box_size" in output_file.variables:
                output_file.variables["box_size"].units = "nm"
                output_file.variables["box_size"].axis = "time"
                output_file.variables["box_size"].name = "box_size"

            if "configuration" in output_file.variables:
                output_file.variables["configuration"].units = "nm"
                output_file.variables["configuration"].axis = "time"
                output_file.variables["configuration"].name = "configuration"

            if "velocities" in output_file.variables:
                output_file.variables["velocities"].units = "nm/ps"
                output_file.variables["velocities"].axis = "time"
                output_file.variables["velocities"].name = "velocities"

            if "gradients" in output_file.variables:
                output_file.variables["gradients"].units = "amu*nm/ps"
                output_file.variables["gradients"].axis = "time"
                output_file.variables["gradients"].name = "gradients"
        finally:
            output_file.close()


class Converter(IJob, metaclass=SubclassFactory):
    category = ("Converters",)

    ancestor = ["empty_data"]

    @abstractmethod
    def run_step(self, index):
        pass

    def finalize(self):
        if not hasattr(self, "_trajectory"):
            return

        try:
            output_file = h5py.File(self._trajectory.filename, "a")
            # f = netCDF4.Dataset(self._trajectory.filename,'a')
        except:
            return

        try:
            if "time" in output_file.variables:
                output_file.variables["time"].units = "ps"
                output_file.variables["time"].axis = "time"
                output_file.variables["time"].name = "time"

            if "box_size" in output_file.variables:
                output_file.variables["box_size"].units = "nm"
                output_file.variables["box_size"].axis = "time"
                output_file.variables["box_size"].name = "box_size"

            if "configuration" in output_file.variables:
                output_file.variables["configuration"].units = "nm"
                output_file.variables["configuration"].axis = "time"
                output_file.variables["configuration"].name = "configuration"

            if "velocities" in output_file.variables:
                output_file.variables["velocities"].units = "nm/ps"
                output_file.variables["velocities"].axis = "time"
                output_file.variables["velocities"].name = "velocities"

            if "gradients" in output_file.variables:
                output_file.variables["gradients"].units = "amu*nm/ps"
                output_file.variables["gradients"].axis = "time"
                output_file.variables["gradients"].name = "gradients"
        finally:
            output_file.close()
