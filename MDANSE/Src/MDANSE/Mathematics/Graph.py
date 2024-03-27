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
# Authors:    Scientific Computing Group at ILL (see AUTHORS)

import collections


class Node(object):
    def __init__(self, name, **kwargs):
        self._name = name
        self._links = set()
        for k, v in list(kwargs.items()):
            setattr(self, k, v)

    @property
    def name(self):
        return self._name

    @property
    def links(self):
        return self._links

    def add_link(self, other):
        self._links.add(other)
        other._links.add(self)


class Graph(object):
    def __init__(self):
        self._nodes = collections.OrderedDict()

    @property
    def nodes(self):
        return self._nodes

    def add_node(self, name, **kwargs):
        self._nodes[name] = Node(name, **kwargs)

    def add_link(self, source, target):
        self._nodes[source].add_link(self._nodes[target])

    def build_connected_components(self):
        # List of connected components found. The order is random.
        result = []

        # Make a copy of the set, so we can modify it.
        nodes = [self._nodes[k] for k in sorted(self._nodes.keys())]
        nodes.reverse()

        # Iterate while we still have nodes to process.
        while nodes:
            # Get a random node and remove it from the global set.
            n = nodes.pop()

            # This set will contain the next group of nodes connected to each other.
            group = set([n])

            # Build a queue with this node in it.
            queue = [n]

            # Iterate the queue.
            # When it's empty, we finished visiting a group of connected nodes.
            while queue:
                # Consume the next item from the queue.
                n = queue.pop(0)

                # Fetch the neighbors.
                neighbors = n.links

                # Remove the neighbors we already visited.
                neighbors.difference_update(group)

                # Remove the remaining nodes from the global set.
                for neigh in neighbors:
                    if neigh in nodes:
                        nodes.remove(neigh)

                # Add them to the group of connected nodes.
                group.update(neighbors)

                # Add them to the queue, so we visit them in the next iterations.
                queue.extend(neighbors)

            # Sort the group
            group = list(group)
            group.sort(key=lambda n: n.name)

            # Add the group to the list of groups.
            result.append(group)

        # Return the list of groups.
        return result
