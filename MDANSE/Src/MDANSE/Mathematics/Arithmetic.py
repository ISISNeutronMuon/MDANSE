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
# Copyright (C)  Institut Laue Langevin 2013-now
# Copyright (C)  ISIS Neutron and Muon Source, STFC, UKRI 2021-now

import math
import cmath
import itertools
from functools import reduce

import numpy as np


def get_weights(props, contents, dim):
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


def weight(props, values, contents, dim, key, symmetric=True):
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

    return weightedSum
