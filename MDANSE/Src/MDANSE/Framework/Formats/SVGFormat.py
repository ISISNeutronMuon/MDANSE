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

import os
import re
import io
import tarfile

import numpy as np


from MDANSE.Externals.svgfig.svgfig import _hacks, Frame, Poly
from MDANSE.Framework.Formats.IFormat import IFormat

_hacks["inkscape-text-vertical-shift"] = True


def format_unit_string(unitString):
    return re.sub("[%()]", "", unitString)


class SVGFormat(IFormat):
    """
    This class handles the writing of output variables in SVG format. Each output variable is written into separate SVG files which are further
    added to a single archive file.

    :attention: only the 1D output variables can be written in SVG file format.
    """

    extension = ".svg"

    extensions = [".svg"]

    @classmethod
    def write(cls, filename, data, header=""):
        """
        Write a set of output variables into a set of SVG files.

        Each output variable will be output in a separate SVG file. All the SVG files will be compressed into a tar file.

        :param filename: the path to the output archive file that will contain the SVG files written for each output variable.
        :type filename: str
        :param data: the data to be written out.
        :type data: dict of Framework.OutputVariables.IOutputVariable
        :param header: the header to add to the output file.
        :type header: str
        """

        filename = os.path.splitext(filename)[0]
        filename = "%s.tar" % filename

        tf = tarfile.open(filename, "w")

        for var in list(data.values()):
            if var.ndim != 1:
                continue

            if var.axis in data:
                axis = data[var.axis]
                xtitle = "%s (%s)" % (axis.name, format_unit_string(axis.units))
            else:
                axis = np.arange(len(var))
                xtitle = "index"

            ytitle = "%s (%s)" % (var.varname, format_unit_string(var.units))

            pl = Poly(list(zip(axis, var)), stroke="blue")

            svgfilename = os.path.join(
                os.path.dirname(filename), "%s%s" % (var.varname, cls.extensions[0])
            )

            Frame(
                min(axis),
                max(axis),
                min(var),
                max(var),
                pl,
                xtitle=xtitle,
                ytitle=ytitle,
            ).SVG().save(svgfilename)

            tf.add(svgfilename, arcname="%s%s" % (var.varname, cls.extensions[0]))

            os.remove(svgfilename)

        if header:
            tempStr = io.StringIO()
            tempStr.write(header)
            tempStr.write("\n\n")
            tempStr.seek(0)
            info = tarfile.TarInfo(name="jobinfo.txt")
            info.size = tempStr.len
            tf.addfile(tarinfo=info, fileobj=tempStr)

        tf.close()
