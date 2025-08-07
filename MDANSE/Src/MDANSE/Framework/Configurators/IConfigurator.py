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
from __future__ import annotations

import abc
import json
from typing import TYPE_CHECKING
from warnings import warn

import numpy as np
from more_itertools import value_chain

from MDANSE.Core.Error import Error
from MDANSE.Core.SubclassFactory import SubclassFactory
from MDANSE.IO.IOUtils import MDANSEEncoder
from MDANSE.MLogging import LOG

if TYPE_CHECKING:
    from MDANSE.Framework.Configurable import Configurable


ERROR_LENGTH_MIN = len("OK")


class ConfiguratorWarning(Warning):
    """Reports a problem with one of the job inputs.

    This warning is produced when the job is still able to execute,
    but there are reasons to believe that the results may be scientifically
    incorrect.
    """


class ConfiguratorError(Error):
    """Error raised by a job input parser."""

    def __init__(self, message: str, configurator: IConfigurator | None = None):
        """Store the error message and configurator reference.

        Parameters
        ----------
        message : str
            Error message related to one of the job inputs
        configurator : IConfigurator, optional
            Reference to the input parser producing the error, by default None

        """
        self._message = message
        self.configurator = configurator

    def __str__(self) -> str:
        """Return a readable summary of the error as string.

        Returns
        -------
        str
            Text and source of the error.

        """
        if self.configurator is not None:
            self._message = (
                f"Configurator: {self.configurator.name!r} --> {self._message}"
            )

        return self._message


class IConfigurator(dict, metaclass=SubclassFactory):
    """The parent class for all the input parameter parsers.

    This class implements the base class for configurator objects.
    A configurator object is a dictionary-derived object that is used
    to configure one item of a given configuration. Once the input
    value given for that item is configured, the dictionary is updated
    with keys/values providing information about this item.

    A configurator is not designed to be used as a stand-alone object.
    It should be used within the scope of a Configurable object that
    will store a complete configuration for a given task (e.g. job,
    Q vectors, instrument resolution ...).

    Usually, configurator objects are self-consistent but for complex ones,
    it can happen that they depends on other configurators of the
    configuration.
    """

    _default = None

    _encoder = MDANSEEncoder()
    _decoder = json.decoder.JSONDecoder()

    _doc_ = "undocumented"

    def __init__(self, name: str, **kwargs):
        """Create an input parser for an MDANSE job input parameter.

        Parameters
        ----------
        name : str
            the key of this object in the Configurable dictionary

        """
        self.name = name

        self._printable_attributes = [
            "name",
            "_original_input",
            "configured",
            "valid",
            "default",
            "_error_status",
            "_warning_status",
        ]

        self.configurable = kwargs.get("configurable")

        self.root = kwargs.get("root")

        self.dependencies = kwargs.get("dependencies", {})

        self.default = kwargs.get("default", self.__class__._default)

        self.label = kwargs.get(
            "label",
            (getattr(type(self), "label", name.replace("_", " ").strip())),
        )

        self.optional = kwargs.get("optional", False)

        self.configured = False

        self.valid = True

        self._error_status = "OK"
        self._warning_status = ""

        self._original_input = ""

    def __str__(self) -> str:
        """Output all the configurator attributes and dict entries as text."""
        return "\n".join(
            value_chain(
                "",
                (
                    f"{label}={getattr(self, label, 'Not set')}"
                    for label in self._printable_attributes
                ),
                (f"{key}={self.get(key, 'Not set')!s}" for key in self),
            ),
        )

    def repr(self) -> str:
        return f"{type(self).__name__}{super().__repr__()}"

    @property
    def error_status(self):
        """Details of the configuration error.

        It is set to 'OK' if no errors occurred.
        """
        return self._error_status

    @error_status.setter
    def error_status(self, error_text: str):
        """Set the error description string.

        If the string is longer than 'OK', the self.valid
        flag is set to False.

        Parameters
        ----------
        error_text : str
            Text explaining why the current input is invalid

        """
        self._error_status = error_text
        self.valid = error_text == "OK"

    @property
    def warning_status(self):
        """Text describing the potential problems with this input value."""
        return self._warning_status

    @warning_status.setter
    def warning_status(self, warning_text: str):
        """Store the warning text and emit a Python warning.

        Parameters
        ----------
        warning_text : str
            Short summary of the problem with this job input.

        """
        self._warning_status = warning_text
        if warning_text:
            LOG.warning(warning_text)
            warn(warning_text, ConfiguratorWarning)

    @abc.abstractmethod
    def configure(self, value: str):
        """Set the value of this job input variable.

        Parameters
        ----------
        value : str
            Text string defining the value of the job variable.

        """

    def update_needed(self, new_input: str) -> bool:
        """Check if the configurator needs to be set up again.

        Parameters
        ----------
        new_input : str
            Input parameters as string

        Returns
        -------
        bool
            If True, self.configure(new_input) needs to be run
        """
        return not self.configured or self._original_input != new_input

    def to_json(self) -> str:
        """Encode this input variable as a JSON string.

        Returns
        -------
        str
            JSON representation of the input value of this variable.

        """
        return self._encoder.encode(self._original_input)

    def from_json(self, json_input: str):
        """Set this input value from its JSON representation.

        Parameters
        ----------
        json_input : str
            input value of this variable encoded as a JSON string.

        """
        self.configure(self._decoder.decode(json_input))

    def set_configured(self, configured: bool):
        """Set the 'configured' flag to the input value.

        Parameters
        ----------
        configured : bool
            True if this configurator has already parsed its input

        """
        self.configured = configured

    def is_configured(self) -> bool:
        """Return True if the input parsing has been completed, False otherwise.

        Returns
        -------
        bool
            True if the input parsing has been completed

        """
        return self.configured

    def set_configurable(self, configurable: Configurable):
        """Store a reference to the parent instance of the Configurable class.

        Parameters
        ----------
        configurable : Configurable
            the Configurable instance for which is using this configurator

        """
        self.configurable = configurable

    def check_dependencies(self, configured: list[str] | None = None) -> bool:
        """Check if the other Configurators needed by this one are ready.

        Parameters
        ----------
        configured : list[str], optional
            List of job inputs known to have already been configured, by default None

        Returns
        -------
        bool
            True if all dependencies are ready, False otherwise

        """
        if configured is None:
            configured = [
                str(name)
                for name, prop in self.configurable._configuration.items()
                if prop.is_configured()
            ]
        return all(c in configured for c in self.dependencies.values())
