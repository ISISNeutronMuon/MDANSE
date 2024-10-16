#    This file is part of MDANSE.
#
#    MDANSE is free software: you can redistribute it and/or modify
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
from MDANSE.Framework.Configurators.RangeConfigurator import RangeConfigurator


class FramesConfigurator(RangeConfigurator):
    """
    This configurator allows to input a frame selection for the analysis.
    
    The frame selection can be input as:
    
    #. a 3-tuple where the 1st, 2nd will correspond respectively to the indexes of the first and \
    last (excluded) frames to be selected while the 3rd element will correspond to the step number between two frames. For example (1,11,3) will give 1,4,7,10
    #. *'all'* keyword, in such case, all the frames of the trajectory are selected
    #. ``None`` keyword, in such case, all the frames of the trajectory are selected

    :note: this configurator depends on 'trajectory' configurator to be configured
    """

    _label = "Subset of frames to be selected (first, last, step size)"
    _default = "all"

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
        self._original_input = value

        trajConfig = self._configurable[self._dependencies["trajectory"]]
        n_steps = trajConfig["length"]

        # if all or None set to default
        if value in ["all", None]:
            value = [0, n_steps, 1]

        # check all values castable to int
        try:
            num_values = [int(x) for x in value[0:3]]
        except (ValueError, TypeError):
            self.error_status = "Input values must castable to int"
            return

        # special case for negative last step option
        if num_values[1] < 0:
            num_values[1] = n_steps - num_values[1]

        first, last, step = num_values

        # check first setting
        if first < 0 or first > n_steps - 1:
            self.error_status = f"First frame needs to be between 0 and {n_steps - 1}"
            return

        # check last setting
        if last <= 0 or last > n_steps or last <= first:
            self.error_status = f"Last frame needs to be between 1 and {n_steps} and greater than the first frame"
            return

        # check step setting
        if step < 1:
            self.error_status = f"Cannot create a range with a step: {step}"
            return

        self._mini = 0
        self._maxi = trajConfig["length"]

        RangeConfigurator.configure(self, value)
        if not self.valid:
            return

        self["n_frames"] = self["number"]

        self["time"] = trajConfig["md_time_step"] * self["value"]

        # case of single frame selected
        try:
            self["time_step"] = self["time"][1] - self["time"][0]
        except IndexError:
            self["time_step"] = 1.0

        self["duration"] = self["time"] - self["time"][0]

    def preview_output_axis(self):
        if not self.is_configured():
            return None, None
        if not self._valid:
            return None, None
        return self["time"], "ps"

    def get_information(self):
        """
        Returns some informations about this configurator.

        :return: the information about this configurator
        :rtype: str
        """

        try:
            result = (
                "%d frames selected (first=%.3f ; last = %.3f ; time step = %.3f)\n"
                % (
                    self["n_frames"],
                    self["time"][0],
                    self["time"][-1],
                    self["time_step"],
                )
            )
        except KeyError:
            result = "FramesConfigurator could not be configured!"

        return result
