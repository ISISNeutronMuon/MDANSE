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

from typing import Dict
import itertools

import numpy as np


def get_weights(props: Dict[str, float], contents: Dict[str, int], dim: int):
    """Combines the information about the elements present in the system
    and the numerical values of their properties into weight factors
    which can be used to scale the partial results of analysis.

    Parameters
    ----------
    props : Dict[str, float]
        a dictionary of "element": value pairs, specifying the
        property of each element that will be used for weighting
    contents : Dict[str, int]
        a dictionary of "element": number_of_atoms pairs, specifying
        the number of atoms of each elements in the system
    dim : int
        number of elements of the output tuple, specifying how
        many atom types have to be combined into a single partial
        result key

    Returns
    -------
    Dict[Tuple(str, ...), float], float
        The dictionary keys are tuples composed of chemical element symbols (str)
        and the values are weights attributed to the specific combination of elements.
        The float number is the normalisation factor which was used to make
        all the weights add up to 1.
    """
    normFactor = None

    weights = {}

    cartesianProduct = set(itertools.product(list(props.keys()), repeat=dim))
    for elements in cartesianProduct:
        n = np.prod([contents[el] for el in elements])
        p = np.prod(np.array([props[el] for el in elements]), axis=0)

        fact = n * p

        weights[elements] = np.float64(np.copy(fact))

        if normFactor is None:
            normFactor = fact
        else:
            normFactor += fact

    for k in list(weights.keys()):
        weights[k] /= np.float64(normFactor)

    return weights, normFactor


def weight(props, values, contents, dim, key, symmetric=True, update_values=False):
    weights = get_weights(props, contents, dim)[0]
    weightedSum = None
    matches = dict([(key % k, k) for k in list(weights.keys())])

    for k, val in values.items():
        if k not in matches:
            continue

        if symmetric:
            permutations = set(itertools.permutations(matches[k], r=dim))
            w = sum([weights.pop(p) for p in permutations])
        else:
            w = weights.pop(matches[k])

        if weightedSum is None:
            weightedSum = w * val
        else:
            weightedSum += w * val

        if update_values:
            values[key % "total"] += w * val
            values[k][:] = w * val

    return weightedSum
