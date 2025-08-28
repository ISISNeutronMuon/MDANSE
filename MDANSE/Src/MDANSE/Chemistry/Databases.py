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

import copy
import json
from collections import defaultdict
from collections.abc import ItemsView
from pathlib import Path
from typing import Any, SupportsComplex

from MDANSE.Core.Error import Error
from MDANSE.Core.Platform import PLATFORM
from MDANSE.Core.Singleton import Singleton
from MDANSE.Framework.Units import measure
from MDANSE.IO.IOUtils import MDANSEEncoder
from MDANSE.MLogging import LOG

TOLERANCE_IMG = 1e-13


def str_to_num(numstr: SupportsComplex) -> float | complex:
    """Convert the number from string format to float or complex.

    Parameters
    ----------
    numstr : SupportsComplex
        Input to be converted or stripped of imaginary part.

    Returns
    -------
    Union[float, complex]
        the input number as complex, or float if there is no imaginary part

    """
    return_value = complex(numstr)
    if abs(return_value.imag) < TOLERANCE_IMG:
        return_value = return_value.real
    return return_value


def color(color_string: str | None = None):
    """Validate a color string for the atom database.

    Returns the color string for white if the input is None.

    Parameters
    ----------
    color_string: Optional[str]
        The color string, if None then it returns a color string
        for white.

    Returns
    -------
    str
        The color string

    """
    if not color_string:
        # default color is white
        return "255;255;255"

    if (
        not isinstance(color_string, str)
        or len(color_string.split(";")) != 3
        or any(not i.isdigit() for i in color_string.split(";"))
        or any(0 < int(i) > 255 for i in color_string.split(";"))
    ):
        raise ValueError(f"{color_string} is not a valid color string.")

    return color_string


class _Database(metaclass=Singleton):
    """Base class for all the databases."""

    _DEFAULT_DATABASE: Path
    _USER_DATABASE: Path

    def __init__(self):
        self._data = {}
        self._default_data = {}

        self._reset()

        # Load the user database. If any problem occurs while loading it, loads the default one
        self._load()

    def __iter__(self):
        """Return a generator over the entries stored in the database."""
        for v in self._data.values():
            yield copy.deepcopy(v)

    def _load(
        self,
        user_database: Path | str | None = None,
        default_database: Path | str | None = None,
    ) -> None:
        """Load the atom database from the pre-defined paths.

        This method should never be called elsewhere than __init__ or unit testing.

        Parameters
        ----------
        user_database : Path | str | None, optional
            The path to the user-defined database. If None, built-in path is used.
        default_database : Path | str | None, optional
            The path to the MDANSE atom database. If None, built-in path is used.

        """
        if user_database is None:
            user_database = self._USER_DATABASE
        else:
            user_database = Path(user_database)
        if default_database is None:
            default_database = self._DEFAULT_DATABASE
        else:
            default_database = Path(default_database)

        database_path = user_database if user_database.exists() else default_database

        with open(default_database, encoding="utf-8") as f:
            self._default_data = json.load(f)

        with open(database_path, encoding="utf-8") as f:
            self._data = json.load(f)

    def items(self) -> ItemsView[str, dict]:
        """Return the iterator over the items of the data dict.

        Allows for iteration over particle names and their data
        simultaneously.

        Returns
        -------
        ItemsView[str, dict]
            dict_items iterator of the internal dictionary.

        """
        return self._data.items()

    def _reset(self) -> None:
        """Reset the database, removing all data."""
        self._data.clear()

    def save(self) -> None:
        """Save a copy of the database to MDANSE application directory.

        This database will then be used in the future.
        If the user database already exists, calling this function will overwrite it.
        """
        with open(self._USER_DATABASE, "w") as f:
            json.dump(self._data, f, indent=4)


class AtomsDatabaseError(Error):
    """Error type for the exceptions related to AtomsDatabase."""

    pass


class AtomsDatabase(_Database):
    """The atoms database of MDANSE.

    Storing all the chemical atoms (and their isotopes) is necessary for any analysis
    based on molecular dynamics trajectories. Indeed, most of them use atomic
    physico-chemical properties such as atomic weight, neutron scattering length,
    atomic radius ...

    The first time the user launches MDANSE, the database is initially loaded from
    a json file stored in MDANSE default database path. Once modified, the user copy
    will be stored in the user's MDANSE application directory (OS dependent). The user
    copy will be preferred by MDANSE over the central database.

    Once loaded, the database is stored internally in a nested dictionary whose primary
    keys are the atom names and the secondary keys are property names.

    :Example:

    >>> # Import the database
    >>> from MDANSE.Chemistry import ATOMS_DATABASE
    >>>
    >>> # Fetch the hydrogen natural element --> get a deep-copy of its properties
    >>> hydrogen = ATOMS_DATABASE["H"]
    >>>
    >>> # Fetch the hydrogen H1 isotope --> get a deep-copy of its properties
    >>> h1 = ATOMS_DATABASE["H1"]
    >>>
    >>> # Return a set of the properties stored in the database
    >>> l = ATOMS_DATABASE.properties()
    >>>
    >>> # Return the atomic weight of U235 atom
    >>> w = ATOMS_DATABASE["U235"]["atomic_weight"]
    >>>
    >>> # Returns the atoms stored currently in the database
    >>> atoms = ATOMS_DATABASE.atoms()
    """

    _DEFAULT_DATABASE = Path(__file__).parent / "atoms.json"

    # The user path
    _OLD_USER_DATABASE = PLATFORM.application_directory() / "atoms.json"

    _USER_DATABASE = PLATFORM.application_directory() / "atoms_extended.json"

    # The python types supported by the database
    _TYPES = {
        "str": str,
        "int": int,
        "float": float,
        "list": list,
        "complex": complex,
        "color": color,
    }

    _encoder = MDANSEEncoder()

    def __init__(self):
        self._properties = defaultdict(lambda: "str")
        self._units = defaultdict(lambda: "none")
        self._atoms_by_atomic_number = {num: [] for num in range(140)}

        super().__init__()

        self.default_atoms_types = list(self._default_data["atoms"].keys())
        self.default_atoms_properties = list(self._default_data["properties"].keys())

        if self._OLD_USER_DATABASE.exists():
            LOG.warning(
                "The old atom database %s will be ignored! MDANSE will use %s instead",
                self._OLD_USER_DATABASE,
                self._USER_DATABASE,
            )

    def __contains__(self, element: str) -> bool:
        """Return true if the element is in the database.

        Parameters
        ----------
        element : str
            Name of the entry. Here, an atom type name.

        Returns
        -------
        bool
            True if atom is in the database, False otherwise.

        """
        return element in self._data

    def __getitem__(self, item: str) -> dict:
        """Return an entry from the database.

        The return value is a deep copy of the element to preserve the database
        integrity.

        Parameters
        ----------
        item : str
            Name of the database entry. Here it is an atom type name.

        """
        try:
            return copy.deepcopy(self._data[item])
        except KeyError as err:
            raise KeyError(
                f"The element {item} is not registered in the database."
            ) from err

    def _load(
        self,
        user_database: Path | str | None = None,
        default_database: Path | str | None = None,
    ) -> None:
        """Load the atom database from the pre-defined paths.

        This method should never be called elsewhere than __init__ or unit testing.

        Parameters
        ----------
        user_database : Path | str | None, optional
            The path to the user-defined database. If None, built-in path is used.
        default_database : Path | str | None, optional
            The path to the MDANSE atom database. If None, built-in path is used.

        """
        self._properties = defaultdict(lambda: "str")
        self._units = defaultdict(lambda: "none")
        super()._load(default_database)

        self._properties.update(self._data["properties"])
        self._units.update(self._data["units"])
        self._data = self._data["atoms"]

        super()._load(user_database)

        self._properties.update(self._data["properties"])
        self._units.update(self._data["units"])
        self._data = self._data["atoms"]

        try:
            number_of_protons = self.get_property("proton")
        except KeyError:
            pass
        else:
            for atom in self.atoms:
                protons = int(number_of_protons[atom])
                self._atoms_by_atomic_number[protons].append(atom)

    def add_atom(self, atom: str) -> None:
        """Add a new element to the atom database.

        The data for this atom will be filled with default values and will not be saved
        until the `save()` method is called.

        Parameters
        ----------
        atom : str
            The atom name.

        Raises
        ------
        AtomsDatabaseError
            When the atom already exist in the database.

        """
        if atom in self._data:
            raise AtomsDatabaseError(
                f"The atom {atom} is already stored in the database.",
            )

        properties = {}
        for pname, ptype in self._properties.items():
            properties[pname] = AtomsDatabase._TYPES[ptype]()
        self._data[atom] = properties

    def add_property(self, pname: str, ptype: str, unit: str = "none") -> None:
        """Add a new property to the atoms database.

        When added, the property will be set with a default value to
        all the elements of the database.

        Parameters
        ----------
        pname : str
            Name of the new property.
        ptype : str
            Data type of the property values.
        unit : str
            Physical unit used for the values in the database.

        Raises
        ------
        AtomsDatabaseError
            If the property already exists.
        TypeError
            If the data type is not recognised.

        """
        if pname in self._properties:
            raise AtomsDatabaseError(
                f"The property {pname} is already registered in the database.",
            )

        if ptype not in AtomsDatabase._TYPES:
            raise TypeError(f"The property type {ptype} is unknown.")

        self._properties[pname] = ptype
        ptype = AtomsDatabase._TYPES[ptype]
        self._units[pname] = unit

        for element in self._data.values():
            element[pname] = ptype()

    @property
    def atoms(self) -> list[str]:
        """Returns the names of all the atoms in the database, sorted alphabetically."""
        return sorted(self._data.keys())

    def get_isotopes(self, atom: str) -> list[str]:
        """Return the names of all the isotopes of the input atom.

        Parameters
        ----------
        atom : str
            Atom type name.

        Returns
        -------
        list[str]
            List of isotope names.

        Raises
        ------
        KeyError
            If atom type is not in the database.

        """
        if atom not in self._data:
            raise KeyError(f"The atom {atom} is not in the database.")

        # The isotopes are searched according to |symbol| property
        symbol = self._data[atom]["symbol"]

        return [
            iname
            for iname, props in self._data.items()
            if props["symbol"] == symbol and iname != symbol
        ]

    @property
    def properties(self) -> list[str]:
        """Return the names of the properties stored in the atoms database."""
        return sorted(self._properties.keys())

    @property
    def units(self) -> dict[str, str]:
        """Return the dictionary mapping properties to their physical units."""
        return self._units

    def get_property(self, pname: str) -> dict[str, str | int | float | list]:
        """Return the values of a property for all atoms.

        Parameters
        ----------
        pname : str
            Atom property name.

        Returns
        -------
        dict[str, str | int | float | list]
            Dictionary of {atom_type: value} pairs.

        Raises
        ------
        KeyError
            If the property is not in the database.

        """
        if pname not in self._properties:
            raise KeyError(f"The property {pname} is not registered in the database.")

        return {element: self.get_value(element, pname) for element in self._data}

    def get_value(
        self, atom: str, pname: str, *, raw_value: bool = False
    ) -> str | int | float | list:
        """Return the value of the property for the input atom type.

        Parameters
        ----------
        atom : str
            Atom type name.
        pname : str
            Atom property name.
        raw_value : bool
            If True, no unit conversion is applied to the value. False by default.

        Returns
        -------
        str | int | float | list
            Value of the property.

        Raises
        ------
        KeyError
            If atom type or property cannot be found in the database.

        """
        if atom not in self._data:
            raise KeyError(f"The atom {atom} is not in the database.")

        if pname not in self._properties:
            raise KeyError(f"The property {pname} is not registered in the database.")
        ptype_str = self._properties[pname]
        ptype = AtomsDatabase._TYPES[ptype_str]
        punit = self._units[pname]

        value = self._data[atom].get(pname, ptype())
        if raw_value:
            return value
        if ptype_str == "complex":
            value = str_to_num(value)
        unit_conv = {
            "fm": "ang",
            "barn": "ang2",
        }
        if punit in unit_conv:
            return measure(value, punit).toval(unit_conv.get(punit))
        if punit == "none":
            return value
        return measure(value, punit).toval()

    def set_value(
        self,
        atom: str,
        pname: str,
        value: str | int | float | list,
    ) -> None:
        """Assign the value to the property of the atom.

        Parameters
        ----------
        atom : str
            Atom type name.
        pname : str
            Atom property name.
        value : str | int | float | list
            New value.

        Raises
        ------
        KeyError
            If the atom or property are not in the database.
        AtomsDatabaseError
            If the property does not support the input value type.

        """
        if atom not in self._data:
            raise KeyError(f"The element {atom} is not in the database.")

        if pname not in self._properties:
            raise KeyError(f"The property {pname} is not registered in the database.")

        try:
            self._data[atom][pname] = AtomsDatabase._TYPES[self._properties[pname]](
                value,
            )
        except ValueError as err:
            raise AtomsDatabaseError(
                f"Can not coerce {value} to {self._properties[pname]} type.",
            ) from err

    def has_atom(self, atom: str) -> bool:
        """Check if the atom type is in the database.

        Parameters
        ----------
        atom : str
            Atom type name.

        Returns
        -------
        bool
            True if the atom information is in the database, False otherwise.

        """
        return atom in self._data

    def has_property(self, pname: str) -> bool:
        """Check if a property is in the database.

        Parameters
        ----------
        pname : str
            Atom property name.

        Returns
        -------
        bool
            True if the property is in the database, False otherwise.

        """
        return pname in self._properties

    def match_numeric_property(
        self,
        pname: str,
        value: int | float,
        tolerance: float = 0.0,
    ) -> list[str]:
        """Return names of atoms for which the given property is within tolerance.

        Parameters
        ----------
        pname : str
            Name of the atom property.
        value : int | float
            Requested value of the property.
        tolerance : float, optional
            Allowed difference between the requested and atom values, by default 0.0

        Returns
        -------
        list[str]
            Names of atoms with the property value within limits.

        Raises
        ------
        AtomsDatabaseError
            If the property cannot be compared to a number.
        KeyError
            If the property cannot be found.

        """
        try:
            if self._properties[pname] not in ["int", "float", "complex"]:
                raise AtomsDatabaseError(
                    f'The provided property must be numeric, but "{pname}" has type '
                    f"{self._properties[pname]}.",
                )
        except KeyError as err:
            raise KeyError(
                f"The property {pname} is not registered in the database."
            ) from err

        tolerance = abs(tolerance)
        try:
            return [
                atom
                for atom, properties in self._data.items()
                if abs(properties.get(pname, 0) - value) <= tolerance
            ]
        except TypeError as err:
            raise AtomsDatabaseError(
                f"The provided value must be a numeric type, but {value} was provided,"
                " which is of"
                f" type {type(value)}. If you are sure that {value} is numeric, then"
                "your database might be corrupt.",
            ) from err

    @property
    def n_atoms(self) -> int:
        """Return the number of atoms stored in the atoms database.

        Returns
        -------
        int
            Number of all the stored atom types.

        """
        return len(self._data)

    @property
    def n_properties(self) -> int:
        """Return the number of properties stored in the atoms database.

        Returns
        -------
        int
            Number of all the stored properties.

        """
        return len(self._properties)

    @property
    def numeric_properties(self) -> list[str]:
        """Return the names of the numeric properties stored in the atoms database.

        Returns
        -------
        list[str]
            Names of the properties which are numbers.

        """
        return [
            pname
            for pname, prop in self._properties.items()
            if prop in ["int", "float", "complex"]
        ]

    def _reset(self) -> None:
        """Reset (clear) the atom database."""
        self._data.clear()
        self._properties.clear()

    def save(self) -> None:
        """Save a copy of the atom database to MDANSE application directory.

        This database will then be used in the future.
        If the user database already exists, calling this function will overwrite it.
        """
        d = {"properties": self._properties, "units": self._units, "atoms": self._data}

        with open(AtomsDatabase._USER_DATABASE, "w") as fout:
            fout.write(json.dumps(d, indent=4, cls=MDANSEEncoder))

    def get_atom_property(
        self,
        symbol: str,
        atom_property: str,
    ) -> int | float | str | None:
        """Return the value of one property for one atom type.

        Parameters
        ----------
        symbol : str
            Atom symbol (element symbol, followed by mass for isotopes).
        atom_property : str
            Name of the requested property.

        Returns
        -------
        int | float | str | None
            Value of the property. Different properties have different types.

        """
        try:
            return self.get_value(symbol, atom_property)
        except KeyError:
            if atom_property == "dummy":
                if symbol == "Du" or self._data[symbol]["element"] == "dummy":
                    return 1
                return 0
            return None

    def get_property_dict(self, symbol: str) -> dict[str, Any]:
        """Get a dictionary of properties and values for one atom type.

        Parameters
        ----------
        symbol : str
            Symbol of the atom.

        Returns
        -------
        dict[str, Any]
            The atom property dictionary.

        """
        return {
            property_name: self.get_value(symbol, property_name)
            for property_name in self.properties
        }

    def remove_atom(self, symbol: str):
        """Remove an atom from the database.

        Parameters
        ----------
        symbol : str
            The atoms symbol to remove from the database.

        """
        try:
            del self._data[symbol]
        except KeyError as err:
            raise AtomsDatabaseError(f"Atom {symbol} does not exist.") from err

    def remove_property(self, label: str):
        """Remove an atom property from the database.

        Parameters
        ----------
        label : str
            The property to remove from the database.

        """
        try:
            del self._properties[label]
        except KeyError:
            raise AtomsDatabaseError(f"Atom property {label} does not exist.")

        for atm in self.atoms:
            del self._data[atm][label]

    def rename_atom_type(self, old_key: str, new_key: str):
        """Rename the atom key in the atom database.

        Parameters
        ----------
        old_key : str
            The key of the atom to change.
        new_key : str
            The new key of the atom.

        """
        if old_key not in self._data:
            raise AtomsDatabaseError(f"Atom {old_key} does not exist.")
        if new_key in self._data:
            raise AtomsDatabaseError(
                f"Cannot rename atom from {old_key} to {new_key} as {new_key}"
                " already exists.",
            )
        self._data[new_key] = self._data.pop(old_key)

    def rename_atom_property(self, old_key: str, new_key: str):
        """Rename the atom property in the atom database.

        Parameters
        ----------
        old_key : str
            The key of the atom property to change.
        new_key : str
            The new key of the atom property.

        """
        if old_key not in self._properties:
            raise AtomsDatabaseError(f"Atom property {old_key} does not exist.")
        if new_key in self._properties:
            raise AtomsDatabaseError(
                f"Cannot rename atom property from {old_key} to {new_key} as {new_key}"
                " already exists.",
            )
        self._properties[new_key] = self._properties.pop(old_key)
        for element in self._data.values():
            element[new_key] = element.pop(old_key)


if __name__ == "__main__":
    from MDANSE.Chemistry import ATOMS_DATABASE

    print(ATOMS_DATABASE.numeric_properties)  # noqa: T201
