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

import re
from typing import TypeVar

import numpy as np

from MDANSE.Chemistry import ATOMS_DATABASE

AtLabel = TypeVar("AtLabel", bound="AtomLabel")


class AtomLabel:
    def __init__(self, atm_label: str, **kwargs):
        """Creates an atom label object which is used for atom mapping
        and atom type guessing.

        Parameters
        ----------
        atm_label : str
            The main atom label.
        kwargs
            The other atom label.
        """
        # use translations since it's faster than the alternative
        # methods as of writing e.g. re.sub
        translation = str.maketrans("", "", ";=")
        self.atm_label = atm_label.translate(translation)
        self.grp_label = ""
        if kwargs:
            for k, v in kwargs.items():
                self.grp_label += f"{k}={str(v).translate(translation)};"
            self.grp_label = self.grp_label[:-1]
        self.mass = kwargs.get("mass", None)
        if self.mass is not None:
            self.mass = float(self.mass)

    def __eq__(self, other: AtLabel) -> bool:
        """Used to check if atom labels are equal.

        Parameters
        ----------
        other : AtomLabel
            The other atom label to compare against.

        Returns
        -------
        bool
            True if all attributes are equal.

        Raises
        ------
        AssertionError
            If the other object is not an AtomLabel.
        """
        if not isinstance(other, AtomLabel):
            raise TypeError(f"{other} should be an instance of AtomLabel.")

        return (
            self.grp_label == other.grp_label
            and self.atm_label == other.atm_label
            and self.mass == other.mass
        )

    def __hash__(self) -> int:
        """
        Returns
        -------
        int
            A hash of the object in its current state.
        """
        return hash((self.atm_label, self.grp_label, self.mass))


def guess_element(atm_label: str, mass: float | int | None = None) -> str:
    """From an input atom label find a match to an element in the atom
    database.

    Parameters
    ----------
    atm_label : str
        The atom label.
    mass : Union[float, int, None]
        The atomic weight in atomic mass units.

    Returns
    -------
    str
        The symbol of the guessed element.

    Raises
    ------
    AttributeError
        Error if unable to match to an element.
    """
    if (mass is not None and mass == 0.0) or atm_label.upper() in [
        "DUMMY",
        "DU",
        "D",
        "M",
    ]:
        return "Du"

    regex = "([A-Za-z][A-Za-z]?)"

    guesses = []
    guess_0 = re.findall(regex, atm_label)
    if len(guess_0) != 0:
        guess = guess_0[0].capitalize()
        guesses.append(guess)
        if len(guess) == 2:
            guesses.append(guess[0])

    best_match = None
    best_diff = np.inf
    for guess in guesses:
        if guess in ATOMS_DATABASE:
            if mass is None:
                return guess
            num = ATOMS_DATABASE.get_atom_property(guess, "proton")
            atms = ATOMS_DATABASE.match_numeric_property("proton", num)

            # if there is only one isotope for this element then we want
            # to return the general element label e.g. Na not Na23
            if len(atms) <= 2:
                atms = [re.findall(regex, atms[0])[0]]

            for atm in atms:
                atm_mass = ATOMS_DATABASE.get_atom_property(atm, "atomic_weight")
                diff = abs(mass - atm_mass)
                if diff < 1 and diff < best_diff:
                    best_match = atm
                    best_diff = diff

    if best_match is not None:
        return best_match

    # try to match based on mass only, if available and previous
    # guesses failed
    best_diff = np.inf
    if mass is not None:
        for atm, properties in ATOMS_DATABASE._data.items():
            atm_mass = properties.get("atomic_weight", None)
            if atm_mass is None:
                continue
            diff = abs(mass - atm_mass)
            if diff < 1 and diff < best_diff:
                best_match = atm
                best_diff = diff

        num = ATOMS_DATABASE.get_atom_property(best_match, "proton")
        atms = ATOMS_DATABASE.match_numeric_property("proton", num)
        if len(atms) <= 2:
            return re.findall(regex, atms[0])[0]
        else:
            return best_match

    raise AttributeError(f"Unable to guess: {atm_label}")


def get_element_from_mapping(
    mapping: dict[str, dict[str, str]], label: str, **kwargs
) -> str:
    """Determine the symbol of the element from the atom label and
    the information from the kwargs.

    Parameters
    ----------
    mapping : dict[str, dict[str, str]]
        A dict which maps group and atom labels to an element from the
        atom database.
    label : str
        The atom label.

    Returns
    -------
    str
        The symbol of the element from the MDANSE atom database.
    """
    label = AtomLabel(label, **kwargs)
    grp_label = label.grp_label
    atm_label = label.atm_label
    if grp_label in mapping and atm_label in mapping[grp_label]:
        element = mapping[grp_label][atm_label]
    elif "" in mapping and atm_label in mapping[""]:
        element = mapping[""][atm_label]
    else:
        element = guess_element(atm_label, label.mass)
    return element


def fill_remaining_labels(
    mapping: dict[str, dict[str, str]], labels: list[AtomLabel]
) -> None:
    """Given a list of labels fill the remaining labels in the mapping
    dictionary.

    Parameters
    ----------
    mapping : dict[str, dict[str, str]]
        The atom mapping dictionary.
    labels : list[AtomLabel]
        A list of atom labels.
    """
    for label in labels:
        grp_label = label.grp_label
        atm_label = label.atm_label
        if grp_label not in mapping:
            mapping[grp_label] = {}
        if atm_label not in mapping[grp_label]:
            mapping[grp_label][atm_label] = guess_element(atm_label, label.mass)


def mapping_to_labels(mapping: dict[str, dict[str, str]]) -> list[AtomLabel]:
    """Converts the mapping back into a list of labels.

    Parameters
    ----------
    mapping : dict[str, dict[str, str]]
        The atom mapping dictionary.

    Returns
    -------
    list[AtomLabel]
        List of atom labels from the mapping.
    """
    labels = []
    for grp_label, atm_map in mapping.items():
        kwargs = {}
        if grp_label:
            for k, v in [i.split("=") for i in grp_label.split(";")]:
                kwargs[k] = v
        for atm_label in atm_map.keys():
            labels.append(AtomLabel(atm_label, **kwargs))
    return labels


def check_mapping_valid(mapping: dict[str, dict[str, str]], labels: list[AtomLabel]):
    """Given a list of labels check that the mapping is valid.

    Parameters
    ----------
    mapping : dict[str, dict[str, str]]
        The atom mapping dictionary.
    labels : list[AtomLabel]
        A list of atom labels.

    Returns
    -------
    bool
        True if the mapping is valid.
    """
    pattern = re.compile(r"^([A-Za-z]\w*=[^=;]+(;[A-Za-z]\w*=[^=;]+)*)*$")
    if not all(pattern.match(grp_label) for grp_label in mapping):
        return False

    if set(mapping_to_labels(mapping)) != set(labels):
        return False

    for label in labels:
        grp_label = label.grp_label
        atm_label = label.atm_label
        if mapping[grp_label][atm_label] not in ATOMS_DATABASE:
            return False

    return True
