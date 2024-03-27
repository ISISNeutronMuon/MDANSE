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

import os
import io
import tarfile
import codecs
import time

import numpy as np


from MDANSE.Framework.Formats.IFormat import IFormat


def length_stringio(input: "io.BytesIO") -> int:
    result = input.getbuffer().nbytes
    return result


class TextFormat(IFormat):
    """
    This class handles the writing of output variables in Text format. Each output variable is written into separate Text files which are further
    added to a single archive file.
    """

    extension = ".dat"

    extensions = [".dat", ".txt"]

    @classmethod
    def write(cls, filename, data, header=""):
        """
        Write a set of output variables into a set of Text files.

        Each output variable will be output in a separate Text file. All the Text files will be compressed into a tar file.

        :param filename: the path to the output archive file that will contain the Text files written for each output variable.
        :type filename: str
        :param data: the data to be written out.
        :type data: dict of Framework.OutputVariables.IOutputVariable
        :param header: the header to add to the output file.
        :type header: str
        """

        filename = os.path.splitext(filename)[0]
        filename = "%s_text.tar" % filename

        tf = tarfile.open(filename, "w")

        if header:
            real_buffer = io.BytesIO()
            tempStr = codecs.getwriter("utf-8")(real_buffer)
            for line in header:
                tempStr.write(str(line))
            tempStr.write("\n\n")
            real_buffer.seek(0)
            info = tarfile.TarInfo(name="jobinfo.txt")
            info.size = length_stringio(real_buffer)
            info.mtime = time.time()
            tf.addfile(tarinfo=info, fileobj=real_buffer)

        for var in list(data.values()):
            real_buffer = io.BytesIO()
            tempStr = codecs.getwriter("utf-8")(real_buffer)
            tempStr.write(var.info())
            tempStr.write("\n\n")
            cls.write_data(tempStr, var, data)
            real_buffer.seek(0)

            info = tarfile.TarInfo(name="%s%s" % (var.varname, cls.extensions[0]))
            info.size = length_stringio(real_buffer)
            info.mtime = time.time()
            tf.addfile(tarinfo=info, fileobj=real_buffer)

        tf.close()

    @classmethod
    def write_data(cls, fileobject, data, allData):
        """
        Write an Framework.OutputVariables.IOutputVariable into a file-like object

        :param fileobject: the file object where the output variable should be written.
        :type fileobject: python file-like object
        :param data: the output variable to write (subclass of NumPy array).
        :type data: Framework.OutputVariables.IOutputVariable
        :param allData: the complete set of output variables
        :type allData: dict of Framework.OutputVariables.IOutputVariable

        :attention: this is a recursive method.
        """

        if data.ndim > 2:
            fileobject.write("Can not write Text output for data of dimensionality > 2")

        elif data.ndim == 2:
            xData, yData = data.axis.split("|")

            if xData == "index":
                xValues = np.arange(data.shape[0])
                fileobject.write("# 1st column: %s (%s)\n" % (xData, "au"))
            else:
                xValues = allData[xData]
                fileobject.write(
                    "# 1st column: %s (%s)\n"
                    % (allData[xData].varname, allData[xData].units)
                )

            if yData == "index":
                yValues = np.arange(data.shape[1])
                fileobject.write("# 1st row: %s (%s)\n\n" % (yData, "au"))
            else:
                yValues = allData[yData]
                fileobject.write(
                    "# 1st row: %s (%s)\n\n"
                    % (allData[yData].varname, allData[yData].units)
                )

            zData = np.zeros((data.shape[0] + 1, data.shape[1] + 1), dtype=np.float64)
            zData[1:, 0] = xValues
            zData[0, 1:] = yValues
            zData[1:, 1:] = data

            np.savetxt(fileobject, zData)
            fileobject.write("\n")

        else:
            xData = data.axis.split("|")[0]

            if xData == "index":
                xValues = np.arange(data.size)
                fileobject.write("# 1st column: %s (%s)\n" % (xData, "au"))
            else:
                xValues = allData[xData]
                fileobject.write(
                    "# 1st column: %s (%s)\n"
                    % (allData[xData].varname, allData[xData].units)
                )

            fileobject.write("# 2nd column: %s (%s)\n\n" % (data.varname, data.units))

            np.savetxt(fileobject, np.column_stack([xValues, data]))
            fileobject.write("\n")
