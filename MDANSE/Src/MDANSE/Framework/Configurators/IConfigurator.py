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

import abc
import json

from MDANSE.Core.Error import Error

from MDANSE.Core.SubclassFactory import SubclassFactory


class ConfiguratorError(Error):
    """
    This class handles any exception related to Configurator-derived object
    """

    def __init__(self, message, configurator=None):
        """
        Initializes the the object.

        :param message: the exception message
        :type message: str
        :param configurator: the configurator in which the exception was raised
        :type configurator: an instance or derived instance of a MDANSE.Framework.Configurators.Configurator object
        """

        self._message = message
        self._configurator = configurator

    def __str__(self):
        """
        Returns the informal string representation of this object.

        :return: the informal string representation of this object
        :rtype: str
        """

        if self._configurator is not None:
            self._message = "Configurator: %r --> %s" % (
                self._configurator.name,
                self._message,
            )

        return self._message

    @property
    def configurator(self):
        """
        Returns the configurator in which the exception was raised

        :return: the configurator in which the exception was raised
        :rtype: an instance or derived instance of a MDANSE.Framework.Configurators.Configurator object
        """
        return self._configurator


class IConfigurator(dict, metaclass=SubclassFactory):
    """
    This class implements the base class for configurator objects. A configurator object is a dictionary-derived object that is used
    to configure one item of a given configuration. Once the input value given for that item is configured, the dictionary is updated
    with keys/values providing information about this item.

    A configurator is not designed to be used as a stand-alone object. It should be used within the scope of a Configurable object that
    will store a complete configuration for a given task (e.g. job, Q vectors, instrument resolution ...).

    Usually, configurator objects are self-consistent but for complex ones, it can happen that they depends on other configurators of the
    configuration.
    """

    _default = None

    _encoder = json.encoder.JSONEncoder()
    _decoder = json.decoder.JSONDecoder()

    _doc_ = "undocumented"

    def __init__(self, name, **kwargs):
        """
        Initializes a configurator object.
        
        :param name: the name of this configurator.
        :type name: str
        :param dependencies: the other configurators on which this configurator depends on to be configured. \
        This has to be input as a dictionary that maps the name under which the dependency will be used within \
        the configurator implementation to the actual name of the configurator on which this configurator is depending on.  
        :type dependencies: (str,str)-dict
        :param default: the default value of this configurator.
        :type default: any python object
        :param label: the label of the panel in which this configurator will be inserted in the MDANSE GUI.
        :type label: str
        :param widget: the configurator widget that corresponds to this configurator.
        :type widget: str
        """

        self._name = name

        self._configurable = kwargs.get("configurable", None)

        self._root = kwargs.get("root", None)

        self._dependencies = kwargs.get("dependencies", {})

        self._default = kwargs.get("default", self.__class__._default)

        self._label = kwargs.get(
            "label",
            (
                self.__class__._label
                if hasattr(self.__class__, "_label")
                else " ".join(name.split("_")).strip()
            ),
        )

        self._widget = kwargs.get("widget", self.__class__)

        self._optional = kwargs.get("optional", False)

        self._configured = False

        self._valid = True

        self._error_status = "OK"

        self._original_input = ""

    @property
    def configurable(self):
        return self._configurable

    @property
    def default(self):
        """
        Returns the default value of this configurator.

        :return: the default value of this configurator.
        :rtype: any Python object
        """

        return self._default

    @property
    def dependencies(self):
        """
        Returns the dependencies maps of this configurator.

        :return: the dependencies maps of this configurator.
        :rtype: (str,str)-dict
        """

        return self._dependencies

    @property
    def label(self):
        """
        Returns the label of this configurator that will be used when inserting its corresponding widget in a configuration panel.

        :return: the label of this configurator.
        :rtype: str
        """

        return self._label

    @property
    def name(self):
        """
        Returns the name of this configurator. That name will be used as a key of a Configurable object.

        :return: the name of this configurator.
        :rtype: str
        """

        return self._name

    @property
    def valid(self):
        """Tells if the current value stored by the configurator
        is a valid input.
        There is no benefit in rejecting the entire configuration
        and killing the GUI just because a value needs to be corrected.
        Instead the GUI should highlight the values that need correcting.

        Returns
        -------
        bool
            true if the current value stored by the configurator can be used
        """
        return self._valid

    @property
    def error_status(self):
        return self._error_status

    @error_status.setter
    def error_status(self, error_text: str):
        """Sets the string explaining why the current input
        cannot be accepted.

        If the string is longer than 'OK', the self._valid
        flag is set to False.

        Parameters
        ----------
        error_text : str
            Text explaining why the current input is invalid
        """
        self._error_status = error_text
        if len(self._error_status) > 2:
            self._valid = False
        else:
            self._valid = True

    @property
    def optional(self):
        """
        Returns the optional state name of this configurator.

        :return: the optional state.
        :rtype: boolean
        """

        return self._optional

    @property
    def root(self):
        return self._root

    @property
    def widget(self):
        """
        Returns the name of the widget that will be associated to this configurator.

        :return: the name of the configurator-widget.
        :rtype: str
        """

        return self._widget

    @abc.abstractmethod
    def configure(self, value):
        """
        Configures this configurator with a given value.

        :param value: the input value to be configured.
        :type value: depends on the configurator

        :note: this is an abstract method.
        """

    def to_json(self) -> str:
        return self._encoder.encode(self._original_input)

    def from_json(self, json_input: str):
        self.configure(self._decoder.decode(json_input))

    def set_configured(self, configured):
        self._configured = configured

    def is_configured(self):
        return self._configured

    def set_configurable(self, configurable):
        self._configurable = configurable

    def check_dependencies(self, configured=None):
        """
        Check that the configurators on which this configurator depends on have already been configured.

        :param configured: the names of the configurators that have already been configured when configuring this configurator.
        :type: list of str

        :return: True if the configurators on which this configurator depends on have already been configured. False otherwise.
        :rtype: bool
        """

        if configured == None:
            names = [str(key) for key in self._configurable._configuration.keys()]
            configured = [
                name
                for name in names
                if self._configurable._configuration[name].is_configured()
            ]

        for c in list(self._dependencies.values()):
            if c not in configured:
                return False

        return True

    def get_information(self):
        """
        Returns some informations about this configurator.

        :return: the information about this configurator
        :rtype: str

        :note: this is an abstract method.
        """

        return ""
