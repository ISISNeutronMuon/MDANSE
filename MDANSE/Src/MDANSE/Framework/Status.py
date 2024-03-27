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
# Copyright (C)  Institut Laue Langevin 2013-now
# Copyright (C)  ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# Authors:    Scientific Computing Group at ILL (see AUTHORS)

import abc

import datetime

import numpy as np


def total_seconds(td):
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10.0**6


def convert_duration(seconds):
    """
    Convert a duration in seconds in days, hours, minutes and seconds
    """

    d = datetime.datetime(1, 1, 1) + datetime.timedelta(seconds=seconds)

    return (d.day - 1, d.hour, d.minute, d.second)


class Status(object, metaclass=abc.ABCMeta):
    """
    This class defines an interface for status objects.
    This kind of object is used to store the status a loop-based task.
    """

    def __init__(self):
        self._updateStep = 1

        self._currentStep = 0
        self._nSteps = None
        self._finished = False
        self._stopped = False
        self._startTime = datetime.datetime.today()
        self._deltas = [self._startTime]
        self._eta = "N/A"
        self._elapsedTime = "N/A"
        self._lastRefresh = self._startTime

    @abc.abstractmethod
    def finish_status(self):
        pass

    @abc.abstractmethod
    def start_status(self):
        pass

    @abc.abstractmethod
    def stop_status(self):
        pass

    @abc.abstractmethod
    def update_status(self):
        pass

    @property
    def currentStep(self):
        return self._currentStep

    @property
    def elapsedTime(self):
        return self._elapsedTime

    @property
    def eta(self):
        return self._eta

    def finish(self):
        self._finished = True

        self.finish_status()

    def get_current_step(self):
        return self._currentStep

    def get_elapsed_time(self):
        return self._elapsedTime

    def get_number_of_steps(self):
        return self._nSteps

    def is_finished(self):
        return self._finished

    def is_running(self):
        return not self._finished and not self._stopped

    def is_stopped(self):
        return self._stopped

    @property
    def nSteps(self):
        return self._nSteps

    def start(self, nSteps, rate=None):
        if self._nSteps is not None:
            return

        self._nSteps = nSteps

        if rate is not None:
            self._updateStep = max(0, int(rate * nSteps))

        self.start_status()

    def stop(self):
        self._eta = "N/A"
        self._stopped = True
        self.stop_status()

    def update(self, force=False):
        if self._updateStep == 0:
            return

        self._currentStep += 1

        lastUpdate = datetime.datetime.today()

        self._deltas.append(lastUpdate)

        if force or (total_seconds(lastUpdate - self._lastRefresh) > 5):
            self._lastRefresh = lastUpdate

            if self._nSteps is not None:
                self._elapsedTime = "%02dd:%02dh:%02dm:%02ds" % convert_duration(
                    total_seconds(datetime.datetime.today() - self._startTime)
                )
                duration = [
                    total_seconds(self._deltas[i + 1] - self._deltas[i])
                    for i in range(self._currentStep)
                ]
                duration = np.median(duration) * (self._nSteps - self._currentStep)
                duration = datetime.timedelta(seconds=round(duration))
                duration = convert_duration(total_seconds(duration))
                self._eta = "%02dd:%02dh:%02dm:%02ds" % duration

        self.update_status()
