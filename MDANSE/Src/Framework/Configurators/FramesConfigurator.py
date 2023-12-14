# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Configurators/FramesConfigurator.py
# @brief     Implements module/class/test FramesConfigurator
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import numpy as np


from MDANSE.Framework.Configurators.RangeConfigurator import RangeConfigurator


class FramesConfigurator(RangeConfigurator):
    """
    This configurator allows to input a frame selection for the analysis.
    
    The frame selection can be input as:
    
    #. a 3-tuple where the 1st, 2nd will corresponds respectively to the indexes of the first and \
    last (excluded) frames to be selected while the 3rd element will correspond to the step number between two frames. For example (1,11,3) will give 1,4,7,10
    #. *'all'* keyword, in such case, all the frames of the trajectory are selected
    #. ``None`` keyword, in such case, all the frames of the trajectory are selected

    :note: this configurator depends on 'trajectory' configurator to be configured
    """

    def __init__(self, name, **kwargs):
        """
        Initializes the configurator.

        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        """

        RangeConfigurator.__init__(self, name, sort=True, **kwargs)

    def configure(self, value):
        """
        Configure the frames range that will be used to perform an analysis.

        :param value: the input value
        :type value: 3-tuple, 'all' or None
        """

        trajConfig = self._configurable[self._dependencies["trajectory"]]

        if value in ["all", None]:
            value = (0, trajConfig["length"], 1)
        elif np.allclose(value, [0, -1, 1]):
            value = (0, trajConfig["length"], 1)

        self._mini = 0
        self._maxi = trajConfig["length"]

        RangeConfigurator.configure(self, value)

        self["n_frames"] = self["number"]

        self["time"] = trajConfig["md_time_step"] * self["value"]

        # case of single frame selected
        try:
            self["time_step"] = self["time"][1] - self["time"][0]
        except IndexError:
            self["time_step"] = 1.0

        self["duration"] = self["time"] - self["time"][0]

    def get_information(self):
        """
        Returns some informations about this configurator.

        :return: the information about this configurator
        :rtype: str
        """

        return "%d frames selected (first=%.3f ; last = %.3f ; time step = %.3f)\n" % (
            self["n_frames"],
            self["time"][0],
            self["time"][-1],
            self["time_step"],
        )
