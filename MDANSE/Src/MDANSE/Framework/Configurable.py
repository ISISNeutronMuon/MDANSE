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
import collections
from typing import Optional

from more_itertools import value_chain

from MDANSE.Core.Error import Error
from MDANSE.MLogging import LOG


class ConfigurationError(Error):
    """
    Handles the exception that may occurs when configuring an object that derives from MDANSE.Core.Configurable class.
    """

    pass


class Configurable:
    """Allows any object that derives from it to be configurable within the MDANSE framework.

    Within that framework, to be configurable, a class must:
        #. derive from this class
        #. implement the "configurators"  class attribute as a list of 3-tuple whose:
            #.. 0-value is the type of the configurator that will be used to fetch the corresponding \
            MDANSE.Framework.Configurators.IConfigurator.IConfigurator derived class from the configurators registry
            #.. 1-value is the name of the configurator that will be used as the key of the _configuration attribute.
            #.. 2-value is the dictionary of the keywords used when initializing the configurator.
    """

    enabled = True

    settings = collections.OrderedDict()

    def __init__(self, settings=None, trajectory_input="mdanse"):
        """
        Constructor
        """

        self._configuration = collections.OrderedDict()

        self._configured = False

        if settings is not None:
            self.set_settings(settings)

        if trajectory_input == "mdmc":
            self.mdmc_trajectory_input()
        elif trajectory_input == "mock":
            self.mock_trajectory_input()

    def mdmc_trajectory_input(self):
        """Remove the hdf_trajectory (file-based) from settings,
        and introduce an MDMC trajectory instead.
        """
        for key, value in self.settings.items():
            if key == "trajectory":
                if value[0] == "HDFTrajectoryConfigurator":
                    self.settings[key] = ("MDMCTrajectoryConfigurator", {})

    def mock_trajectory_input(self):
        """Remove the hdf_trajectory (file-based) from settings,
        and introduce a mock trajectory instead.
        """
        for key, value in self.settings.items():
            if key == "trajectory":
                if value[0] == "HDFTrajectoryConfigurator":
                    self.settings[key] = ("MockTrajectoryConfigurator", {})

    def build_configuration(self):
        from MDANSE.Framework.Configurators.IConfigurator import IConfigurator

        self._configuration.clear()

        for name, (typ, kwds) in list(self.settings.items()):
            try:
                self._configuration[name] = IConfigurator.create(
                    typ, name, configurable=self, **kwds
                )
            # Any kind of error has to be caught
            except Exception:
                raise ConfigurationError(f"Could not set {name!r} configuration item")

    def set_settings(self, settings):
        self.settings = settings

        self.build_configuration()

    def __getitem__(self, name):
        """
        Returns a configuration item given its name.

        :param name: the name of the configuration item
        :type name: str

        If not found return an empty dictionary.
        """

        return self._configuration.setdefault(name, {})

    @property
    def configuration(self):
        """
        Return the configuration bound to the Configurable object.

        :return: the configuration bound to the Configurable object.
        :rtype: dict
        """

        return self._configuration

    def check_status(self):
        """Raise an exception if some of the job inputs are invalid.

        Loops over all the configuration items, and collects the error status
        of the invalid ones. For optional inputs, only a warning is logged.

        Raises
        ------
        RuntimeError
            Trying to run a job that is not configured correctly.

        """
        errors = {}
        warnings = {}
        for name, conf in list(self._configuration.items()):
            if not conf.valid:
                if conf.optional:
                    warnings[name] = conf.error_status
                else:
                    errors[name] = conf.error_status
        if warnings:
            LOG.warning(
                "\n".join(
                    ["Optional configuration entries were not valid:"]
                    + [f"{entry}: {error}" for entry, error in warnings.items()]
                )
            )
        if errors:
            raise RuntimeError(
                "\n".join(
                    ["Bad configuration entries:"]
                    + [f"{entry}: {error}" for entry, error in errors.items()]
                )
            )

    def setup(self, parameters: dict, rebuild: bool = True):
        """Builds and sets the configuration according to a set of
        input parameters.

        Parameters
        ----------
        parameters : dict
            A dictionary of setting parameters.
        rebuild : bool
            Rebuilds all the configurators if true.
        """
        self._configured = False

        if rebuild:
            self.build_configuration()

        # If no configurator has to be configured, just return
        if not self._configuration:
            self._configured = True
            return

        if not isinstance(parameters, dict):
            raise ConfigurationError("Invalid type for configuration parameters")

        # Loop over the configuration items
        for key, value in self._configuration.items():
            parameters.setdefault(key, value.default)

        toBeConfigured = set(self._configuration.keys())
        configured = set()

        while toBeConfigured != configured:
            progress = False

            for name, conf in self._configuration.items():
                if name in configured:
                    continue

                if not conf.valid:
                    LOG.error(conf.error_status)
                    self._configured = False
                    return

                if conf.check_dependencies(configured):
                    if not conf.optional:
                        conf.configure(parameters[name])
                    elif parameters[name]:
                        conf.configure(parameters[name])
                        if not conf.valid:
                            self._configuration[name] = False

                    conf.set_configured(True)

                    self._configuration[name] = conf

                    configured.add(name)

                    progress = True

                if not conf.valid and not conf.optional:
                    LOG.error(conf.error_status)
                    self._configured = False
                    return

            if not progress:
                raise ConfigurationError(
                    "Circular or unsatisfiable dependencies when setting up configuration."
                )

        self._configured = True

    def output_configuration(self) -> Optional[dict[str, str]]:
        if not self._configured:
            return
        return {name: conf.to_json() for name, conf in self._configuration.items()}

    def __str__(self) -> str:
        """
        Returns the informations about the current configuration in text form.

        Returns
        -------
        str
            the informations about the current configuration in text form
        """
        return "\n".join(
            f"{key}: {value}" for key, value in self._configuration.items()
        )

    @classmethod
    def build_doc_example(cls):
        docstring = ":Example:\n\n"
        docstring += ">>> \n"
        docstring += ">>> \n"
        docstring += ">>> parameters = {}\n"
        for k, v in cls.get_default_parameters().items():
            docstring += f">>> parameters[{k!r}]={v!r}\n"
        docstring += ">>> \n"
        docstring += f">>> job = IJob.create({cls.__name__!r})\n"
        docstring += ">>> job.setup(parameters)\n"
        docstring += ">>> job.run()\n"
        return docstring

    @classmethod
    def build_doc_texttable(cls, doclist):
        docstring = "\n**Job input configurators:** \n\n"

        columns = ["Configurator", "Default value", "Description"]

        sizes = [len(v) for v in columns]

        for v in doclist:
            sizes[0] = max(sizes[0], len(v["Configurator"]))
            sizes[1] = max(sizes[1], len(v["Default value"]))
            # Case of Description field: has to be splitted and parsed for inserting sphinx "|" keyword for multiline
            v["Description"] = v["Description"].strip()
            v["Description"] = v["Description"].splitlines()
            v["Description"] = ["| " + vv.strip() for vv in v["Description"]]
            sizes[2] = max(value_chain(sizes[2], map(len, v["Description"])))

        data_line = "| " + "| ".join(f"{{}}:<{size}" for size in sizes) + "|\n"
        sep_line = "+" + "+".join("-" * (size + 1) for size in sizes) + "+\n"

        docstring += sep_line
        docstring += data_line.format(*columns)
        docstring += sep_line.replace("-", "=")

        for v in doclist:
            docstring += data_line.format(
                v["Configurator"], v["Default value"], v["Description"][0]
            )
            if len(v["Description"]) > 1:
                for descr in v["Description"][1:]:
                    data_line.format("", "", descr)
            docstring += sep_line

        docstring += "\n"
        return docstring

    @classmethod
    def build_doc_htmltable(cls, doclist):
        docstring = "\n**Job input configurators:**"

        columns = ["Configurator", "Default value", "Description"]

        for v in doclist:
            # Case of Description field: has to be splitted and parsed for inserting sphinx "|" keyword for multiline
            v["Description"] = v["Description"].strip()
            v["Description"] = v["Description"].split("\n")
            v["Description"] = ["" + vv.strip() for vv in v["Description"]]

        docstring += "<table>\n"
        docstring += "<tr>"
        for col in columns:
            docstring += f"<th>{col}</th>"
        docstring += "</tr>\n"

        for v in doclist:
            docstring += "<tr>"
            for item in [
                v["Configurator"],
                v["Default value"],
                v["Description"][0],
            ]:
                docstring += f"<td>{item}</td>"
            docstring += "</tr>\n"

        docstring += "</table>\n"
        return docstring

    @classmethod
    def build_doc(cls, use_html_table=False):
        """
        Return the documentation about a configurable class based on its configurators contents.

        :param cls: the configurable class for which documentation should be built
        :type cls: an instance of MDANSE.Framework.Configurable.Configurable derived class

        :return: the documentation about the configurable class
        :rtype: str
        """
        from MDANSE.Framework.Configurators.IConfigurator import IConfigurator

        settings = getattr(cls, "settings", {})

        if not isinstance(settings, dict):
            raise ConfigurationError(
                "Invalid type for settings: must be a mapping-like object"
            )

        doclist = []

        for name, (typ, kwds) in list(settings.items()):
            cfg = IConfigurator.create(typ, name, **kwds)
            descr = kwds.get("description", "")
            descr += "\n" + str(cfg.__doc__)
            doclist.append(
                {
                    "Configurator": name,
                    "Default value": repr(cfg.default),
                    "Description": descr,
                }
            )

        docstring = cls.build_doc_example()

        if use_html_table:
            docstring += cls.build_doc_htmltable(doclist)
        else:
            docstring += cls.build_doc_texttable(doclist)

        return docstring

    @classmethod
    def get_default_parameters(cls):
        """
        Return the default parameters of a configurable based on its configurators contents.

        :param cls: the configurable class for which documentation should be built
        :type cls: an instance of MDANSE.Framework.Configurable.Configurable derived class

        :return: a dictionary of the default parameters of the configurable class
        :rtype: dict
        """
        from MDANSE.Framework.Configurators.IConfigurator import IConfigurator

        settings = getattr(cls, "settings", {})

        if not isinstance(settings, dict):
            raise ConfigurationError(
                "Invalid type for settings: must be a mapping-like object"
            )

        params = collections.OrderedDict()
        for name, (typ, kwds) in list(settings.items()):
            cfg = IConfigurator.create(typ, name, **kwds)
            params[name] = (cfg.default, cfg.label)

        return params
