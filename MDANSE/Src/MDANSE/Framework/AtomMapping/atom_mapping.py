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
from typing import Union
import re
import numpy as np

from MDANSE.Chemistry import ATOMS_DATABASE


class AtomLabel:

    def __init__(self, atm_label, **kwargs):
        self.atm_label = atm_label
        self.grp_label = f""
        if kwargs:
            for k, v in kwargs.items():
                self.grp_label += f"{k}={v};"
            self.grp_label = self.grp_label[:-1]
        self.mass = kwargs.get("mass", None)
        if self.mass is not None:
            self.mass = float(self.mass)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AtomLabel):
            AssertionError(f"{other} should be an instance of AtomLabel.")
        if self.grp_label == other.grp_label and self.atm_label == other.atm_label:
            return True


def guess_element(atm_label: str, mass: Union[float, int, None] = None) -> str:
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
    if mass is not None and mass == 0.0:
        return "Du"

    guesses = []
    guess_0 = re.findall("([A-Za-z][a-z]?)", atm_label)
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
            for atm in atms:
                atm_mass = ATOMS_DATABASE.get_atom_property(atm, "atomic_weight")
                diff = abs(mass - atm_mass)
                if diff < best_diff:
                    best_match = atm
                    best_diff = diff
    if best_match is not None:
        return best_match

    # try to match based on mass if available and guesses failed
    best_diff = np.inf
    if mass is not None:
        for atm, properties in ATOMS_DATABASE._data.items():
            atm_mass = properties.get("atomic_weight", None)
            if atm_mass is None:
                continue
            diff = abs(mass - atm_mass)
            if diff < best_diff:
                best_match = atm
                best_diff = diff
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
    for label in labels:
        grp_label = label.grp_label
        atm_label = label.atm_label
        if grp_label not in mapping or atm_label not in mapping[grp_label]:
            return False
        if mapping[grp_label][atm_label] not in ATOMS_DATABASE:
            return False
    return True
