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
from typing import List, Dict, Tuple, Union
import itertools

import numpy as np


def complex_to_float(
    input_weights: dict[str, Union[complex, float]],
) -> dict[str, Union[complex, float]]:
    """Convert complex values to float if all imaginary parts are 0.

    It will replace the complex values with float values only if this
    does not lead to any loss on information.

    Parameters
    ----------
    input_weights : dict[str, Union[complex, float]]
        Weight dictionary with possibly complex values

    Returns
    -------
    dict[str, Union[complex, float]]
        Unchanged dictionary, or dictionary with float values
    """
    no_imaginary = True
    new_dict = {}
    for key, x in input_weights.items():
        if isinstance(x, np.ndarray):
            no_imaginary &= np.allclose(np.imag(x), 0.0)
            new_dict[key] = np.real(x)
        else:
            no_imaginary &= np.isclose(complex(x).imag, 0.0)
            new_dict[key] = complex(x).real
    if no_imaginary:
        return new_dict
    return input_weights


def weights_1D(contents, props, conc_exp=1.0):
    weights = {}
    norm_factor = 0.0
    n_atms = sum(contents.values())
    for element in contents:
        concentration = contents[element] / n_atms
        property = props[element]
        factor = concentration**conc_exp * property
        weights[(element,)] = factor
        norm_factor += concentration * property
    return weights, norm_factor


def weights_2D(contents, props, conc_exp=1.0):
    weights = {}
    norm_factor = 0.0
    n_atms = sum(contents.values())
    cartesianProduct = itertools.product(contents, repeat=2)
    for el1, el2 in cartesianProduct:
        concentration = contents[el1] * contents[el2] / n_atms**2
        if isinstance(props[el1], np.ndarray):
            prop1 = np.conjugate(props[el1].astype(complex))
        else:
            prop1 = complex(props[el1]).conjugate()
        if isinstance(props[el2], np.ndarray):
            prop2 = props[el2].astype(complex)
        else:
            prop2 = complex(props[el2])
        property = prop1 * prop2
        factor = concentration**conc_exp * property
        weights[(el1, el2)] = factor
        norm_factor += concentration * property
    return weights, norm_factor


def get_weights(
    props: dict[str, float], contents: dict[str, int], dim: int, conc_exp: float = 1.0
) -> dict[tuple[str], Union[float, complex]]:
    """Calculate the scaling factors to be applied to output datasets.

    Returns a dictionary of scaling factors, where the
    chemical elements identifying each dataset are the keys.

    Parameters
    ----------
    props : Dict[str, float]
        Dictionary of values of an atom property for a selected object, averaged over atoms in that object
    contents : Dict[str, int]
        Dictionary of numbers of atoms in an object
    dim : int
        number of atom types in the label of the output datasets (e.g. 1 for "O", 2 for "CuCu")
    conc_exp : float
        The exponent the at the product of the concentrations are taken
        to (e.g. (c_i * c_j)**0.5 which is used for DCSF jobs).

    Returns
    -------
    dict[tuple[str], float]
        Dictionary of scaling factors per dataset key, and a sum of all the factors
    """
    if dim == 1:
        weights, norm_factor = weights_1D(contents, props, conc_exp=conc_exp)
    elif dim == 2:
        weights, norm_factor = weights_2D(contents, props, conc_exp=conc_exp)
    else:
        raise NotImplementedError("Only 1D and 2D weights are available.")

    normalise = True
    try:
        len(norm_factor)
    except TypeError:
        normalise = (
            abs(norm_factor) > 0.0
        )  # if norm_factor is 0, all weights are 0 too.
    if normalise:
        for k in list(weights.keys()):
            weights[k] /= norm_factor

    weights["sum"] = norm_factor

    return complex_to_float(weights)


def assign_weights(
    values: Dict[str, np.ndarray],
    weights: Dict[str, float],
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
            w = 0
            permutations = set(itertools.permutations(matches[k], r=dim))
            for n, p in enumerate(permutations):
                if n % 2:
                    w += weights[p]
                else:
                    w += np.conjugate(weights[p])
        else:
            w = weights[matches[k]]

        values[k].scaling_factor *= w


def weighted_sum(
    values: Dict[str, np.ndarray],
    weights: Dict[str, float],
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
