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

import itertools
from collections.abc import Iterable

import numpy as np


def get_weights(
    selected_props: dict[str, float | complex],
    all_props: dict[str, float | complex],
    selected_contents: dict[str, int],
    all_contents: dict[str, int],
    dim: int,
    conc_exp: float = 1.0,
) -> dict[str, float | complex]:
    """Calculate the scaling factors to be applied to output datasets.

    Returns a dictionary of scaling factors, where the
    chemical elements identifying each dataset are the keys.

    Parameters
    ----------
    selected_props : dict[str, float]
        Dictionary of values of an atom property for the selected subset of the trajectory, averaged over atoms in that object
    all_props : dict[str, float]
        Dictionary of values of an atom property for the trajectory, averaged over atoms in that object
    selected_contents : dict[str, int]
        Dictionary of numbers of atoms in the selected subset of the trajectory
    all_contents : dict[str, int]
        Dictionary of numbers of atoms of the trajectory
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
    n_atms = sum(all_contents[el] for el in all_props)
    weights, _ = adjust_weights(
        selected_props, selected_contents, n_atms, dim, conc_exp
    )
    _, normFactor = adjust_weights(all_props, all_contents, n_atms, dim, conc_exp)

    normalise = True
    try:
        len(normFactor)
    except TypeError:
        normalise = abs(normFactor) > 0.0  # if normFactor is 0, all weights are 0 too.
    if normalise:
        for k in weights:
            weights[k] /= normFactor
    weights["sum"] = normFactor

    return weights


def adjust_weights(
    props: dict[str, float | complex],
    contents: dict[str, int],
    n_atms: int,
    dim: int,
    conc_exp: float = 1.0,
) -> tuple[dict[str | tuple[str], float | complex], float]:
    """Combine the weights based on whether they will be used for nth-body
    property and adjust them based on their atom concentrations.

    Parameters
    ----------
    props : dict[str, float]
        Dictionary of values of an atom property for the selected subset of the trajectory, averaged over atoms in that object
    contents : dict[str, int]
        Dictionary of numbers of atoms in the selected subset of the trajectory
    n_atms : int
        Total number of atoms of the trajectory.
    dim : int
        number of atom types in the label of the output datasets (e.g. 1 for "O", 2 for "CuCu")
    conc_exp : float
        The exponent the at the product of the concentrations are taken
        to (e.g. (c_i * c_j)**0.5 which is used for DCSF jobs).

    Returns
    -------
    tuple[dict[Union[str, tuple[str]], float], float]
        The dictionary of weights and a normalisation factor.
    """
    normFactor = 0.0

    weights = {}

    if dim == 1:
        for el, property_product in props.items():
            atom_conc_product = contents[el] / n_atms
            factor = atom_conc_product**conc_exp * property_product
            weights[(el,)] = factor
            normFactor += atom_conc_product * property_product
    elif dim == 2:
        cartesianProduct = itertools.product(props, repeat=2)
        for el_a, el_b in cartesianProduct:
            atom_conc_product = contents[el_a] * contents[el_b] / n_atms**2
            property_product = props[el_a].conjugate() * props[el_b]

            factor = atom_conc_product**conc_exp * property_product
            # E.g. for property b_coh, 5 Cu atoms, 100 total atoms, and dim=2
            # factor = (5*5/(100*100))**conc_exp * b_coh_cu.conjugate() * b_coh_cu

            weights[(el_a, el_b)] = factor
            normFactor += atom_conc_product * property_product
    else:
        raise NotImplementedError(f"Dimension {dim} not implemented.")

    return weights, abs(normFactor.real)


def assign_weights(
    values: dict[str, np.ndarray],
    weights: dict[str, float | complex],
    match_key: str,
    match_labels: Iterable[tuple[str, tuple[str, ...]]],
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
    match_key: str
        A key used to generate the dict of matches to assign weights for.
    match_labels: Iterable[tuple[str, Union[tuple[str, ], tuple[str, str]]]]
        The labels used to generate the dict of matches to assign weights for.
    symmetric : bool, optional
        do not generate results for the same elements in a different sequence, by default True

    Returns
    -------
    np.ndarray
        total sum of all the component arrays scaled by their weights
    """
    matches = {match_key % label: k for label, k in match_labels}

    for k in values.keys() & matches:
        if symmetric:
            permutations = set(itertools.permutations(matches[k], r=len(matches[k])))
            w = sum(weights[p].real for p in permutations)
        else:
            w = weights[matches[k]].real

        values[k].scaling_factor *= w


def weighted_sum(values: dict[str, np.ndarray], match_key: str, match_labels: Iterable):
    """Sums up partial datasets multiplied by their scaling factors.
    The scaling factors have to be set before, typically by calling
    the assign_weights function.

    Parameters
    ----------
    values : Dict[str, np.ndarray]
        Dictionary of data arrays containing analysis results.
    match_key: str
        A key used to generate the list of matches to sum over.
    match_labels: Iterable
        The labels used to generate the list of matches to sum over.

    Returns
    -------
    np.ndarray
        Total sum of all the component arrays scaled by their weights
    """
    matches = {match_key % val[0] for val in match_labels}
    weighted_sum = 0.0

    for val in (val for key, val in values.items() if key in matches):
        weighted_sum += val * val.scaling_factor

    return weighted_sum
