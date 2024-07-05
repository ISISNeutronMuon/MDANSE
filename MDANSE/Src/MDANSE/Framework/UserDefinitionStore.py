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
import pickle
import os

from MDANSE import PLATFORM
from MDANSE.Core.Error import Error
from MDANSE.Core.Singleton import Singleton
from MDANSE.MLogging import LOG


class UserDefinitionStoreError(Error):
    pass


class UserDefinitionStore(object, metaclass=Singleton):
    """
    This class is used to register, save and delete MDANSE user definitions (a.k.a. UD).

    Basically, user definitions are used to keep track of definitions made on a given target. The target can
    be a file or any kind of object that has to be associated with the user definitions.
    This definitions can be selections of atoms, Q vectors definitions, axis definitions ... The
    user definitions are loaded when MDANSE starts through a cPickle file that will store these definitions.
    """

    UD_PATH = os.path.join(PLATFORM.application_directory(), "user_definitions_md3.ud")

    def __init__(self):
        self._definitions = {}

        self.load()

    @property
    def definitions(self):
        return self._definitions

    def load(self):
        """
        Load the user definitions.
        """

        if not os.path.exists(UserDefinitionStore.UD_PATH):
            return

        # Try to open the UD file.
        try:
            f = open(UserDefinitionStore.UD_PATH, "rb")
            UD = pickle.load(f)

        # If for whatever reason the pickle file loading failed do not even try to restore it
        except Exception as e:
            LOG.error("Exception reading the User Definitions")
            LOG.error(e)
            return

        else:
            self._definitions.update(UD)
            f.close()

    def save(self):
        """
        Save the user definitions.

        :param path: the path of the user definitions file.
        :type path: str
        """

        try:
            f = open(UserDefinitionStore.UD_PATH, "wb")
        except IOError:
            return
        else:
            pickle.dump(self._definitions, f, protocol=2)
            f.close()

    def remove_definition(self, *defs):
        if self.has_definition(*defs):
            defs = list(defs)
            locald = self._definitions
            while defs:
                val = defs.pop(0)
                if len(defs) == 0:
                    del locald[val]
                    return
                locald = locald[val]

    def set_definition(self, target, section, name, value):
        if self.has_definition(target, section, name):
            raise UserDefinitionStoreError(
                "Item %s is already registered as an user definition. You must delete it before setting it."
                % (target, section, name)
            )

        self._definitions.setdefault(target, {}).setdefault(section, {})[name] = value

    def filter(self, *defs):
        d = self.get_definition(*defs)
        if d is None:
            return []

        return list(d.keys())

    def get_definition(self, *defs):
        """
        Returns a user definition given its target, category and its name.

        :return: the user definition if it found or None otherwise
        :rtype: any
        """

        locald = self._definitions

        defs = list(defs)
        while defs:
            val = defs.pop(0)
            locald = locald.get(val, None)

            if locald is None:
                return None

            if not defs:
                break

            if not isinstance(locald, dict):
                return None

        return locald

    def has_definition(self, *defs):
        locald = self._definitions

        defs = list(defs)
        while defs:
            val = defs.pop(0)
            locald = locald.get(val, None)

            if locald is None:
                return False

            if not defs:
                break

            if not isinstance(locald, dict):
                return False

        return True


UD_STORE = UserDefinitionStore()
