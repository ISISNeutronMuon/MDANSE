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
import itertools

import numpy as np


def get_weights(
    props: dict[str, float], contents: dict[str, int], dim: int, conc_exp: float = 1.0
) -> tuple[dict[tuple[str], float], float]:
    """Calculate the scaling factors to be applied to output datasets.

    Returns a dictionary of scaling factors, where the
    chemical elements identifying each dataset are the keys.

    Parameters
    ----------
    props : dict[str, float]
        Dictionary of values of an atom property for a selected object, averaged over atoms in that object
    contents : dict[str, int]
        Dictionary of numbers of atoms in an object
    dim : int
        number of atom types in the label of the output datasets (e.g. 1 for "O", 2 for "CuCu")
    conc_exp : float
        The exponent the at the product of the concentrations are taken
        to (e.g. (c_i * c_j)**0.5 which is used for DCSF jobs).

    Returns
    -------
    Tuple(Dict[Tuple[str], float], float)
        Dictionary of scaling factors per dataset key, and a sum of all the factors
    """
    normFactor = 0.0

    weights = {}

    n_atms = sum(contents[el] for el in props)
    cartesianProduct = itertools.product(props, repeat=dim)
    for elements in cartesianProduct:
        atom_conc_product = np.prod([contents[el] / n_atms for el in elements])
        property_product = np.prod(np.array([props[el] for el in elements]), axis=0)

        factor = atom_conc_product**conc_exp * property_product
        # E.g. for property b_coh, 5 Cu atoms, 100 total atoms, and dim=2
        # factor = (5*5/(100*100))**conc_exp * b_coh(Cu)*b_coh(Cu)

        weights[elements] = np.float64(np.copy(factor))
        normFactor += atom_conc_product * property_product

    normalise = True
    try:
        len(normFactor)
    except TypeError:
        normalise = abs(normFactor) > 0.0  # if normFactor is 0, all weights are 0 too.
    if normalise:
        for k in list(weights.keys()):
            weights[k] /= np.float64(normFactor)

    weights["sum"] = normFactor

    return weights


def assign_weights(
    values: dict[str, np.ndarray],
    weights: dict[str, float],
    key: str,
    symmetric: bool = True,
):
    """Updates the scaling factors of partial datasets, without
    modifying the data.

    Parameters
    ----------
    values : Dict[str, np.ndarray]
        Dictionary of data arrays containing analysis results.
    weights : Dict[str, float]
        Dictionary of scaling factors per dataset
    key : str
        A string data set name with formatting elements (placeholders for chemical element labels)
    symmetric : bool, optional
        do not generate results for the same elements in a different sequence, by default True

    Returns
    -------
    np.ndarray
        total sum of all the component arrays scaled by their weights
    """
    matches = {key % k: k for k in weights if k not in ["sum"]}
    dim = key.count("%s")

    for k in values.keys() & matches:
        if symmetric:
            permutations = set(itertools.permutations(matches[k], r=dim))
            w = sum(weights[p] for p in permutations)
        else:
            w = weights[matches[k]]

        values[k].scaling_factor *= w


def weighted_sum(
    values: dict[str, np.ndarray],
    weights: dict[str, float],
    key: str,
):
    """Sums up partial datasets multiplied by their scaling factors.
    The scaling factors have to be set before, typically by calling
    the assign_weights function.

    Parameters
    ----------
    values : Dict[str, np.ndarray]
        Dictionary of data arrays containing analysis results.
    weights : Dict[str, float]
        Dictionary of scaling factors per dataset
    key : str
        A string data set name with formatting elements (placeholders for chemical element labels)

    Returns
    -------
    np.ndarray
        total sum of all the component arrays scaled by their weights
    """
    weightedSum = 0.0
    matches = {key % k for k in weights if k not in ["sum"]}

    for val in (val for key, val in values.items() if key in matches):
        weightedSum += val * val.scaling_factor

    return weightedSum
