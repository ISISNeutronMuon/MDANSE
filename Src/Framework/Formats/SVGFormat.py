# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Formats/SVGFormat.py
# @brief     Implements module/class/test SVGFormat
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import os
import re
import StringIO
import tarfile

import numpy

from MDANSE import REGISTRY
from MDANSE.Externals.svgfig.svgfig import _hacks, Frame, Poly
from MDANSE.Framework.Formats.IFormat import IFormat

_hacks["inkscape-text-vertical-shift"] = True

def format_unit_string(unitString):

    return re.sub('[%()]','',unitString)

class SVGFormat(IFormat):
    '''
    This class handles the writing of output variables in SVG format. Each output variable is written into separate SVG files which are further
    added to a single archive file.
    
    :attention: only the 1D output variables can be written in SVG file format.
    '''
    
    extension = ".svg"
    
    extensions = ['.svg']
        
    @classmethod
    def write(cls,filename,data, header=""):
        '''
        Write a set of output variables into a set of SVG files.
        
        Each output variable will be output in a separate SVG file. All the SVG files will be compressed into a tar file.
        
        :param filename: the path to the output archive file that will contain the SVG files written for each output variable.
        :type filename: str
        :param data: the data to be written out.
        :type data: dict of Framework.OutputVariables.IOutputVariable
        :param header: the header to add to the output file.
        :type header: str
        '''

        filename = os.path.splitext(filename)[0]
        filename = "%s.tar" % filename

        tf = tarfile.open(filename,'w')
                                
        for var in data.values():
                        
            if var.ndim != 1:
                continue
            
            if var.axis in data:
                axis = data[var.axis]
                xtitle = "%s (%s)" % (axis.name,format_unit_string(axis.units))
            else:
                axis = numpy.arange(len(var))
                xtitle = 'index'
                
            ytitle = "%s (%s)" % (var.name,format_unit_string(var.units))
                        
            pl = Poly(zip(axis,var),stroke='blue')

            svgfilename = os.path.join(os.path.dirname(filename),'%s%s' % (var.name,cls.extensions[0]))
            
            Frame(min(axis),max(axis),min(var),max(var),pl,xtitle=xtitle,ytitle=ytitle).SVG().save(svgfilename)

            tf.add(svgfilename, arcname='%s%s' % (var.name,cls.extensions[0]))
            
            os.remove(svgfilename)
            
        if header:
            tempStr = StringIO.StringIO()
            tempStr.write(header)
            tempStr.write('\n\n')  
            tempStr.seek(0)
            info = tarfile.TarInfo(name='jobinfo.txt')
            info.size=tempStr.len
            tf.addfile(tarinfo=info, fileobj=tempStr)
                
        tf.close()

REGISTRY['svg'] = SVGFormat
