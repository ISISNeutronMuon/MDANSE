#MDANSE : Molecular Dynamics Analysis for Neutron Scattering Experiments
#------------------------------------------------------------------------------------------
#Copyright (C)
#2015- Eric C. Pellegrini Institut Laue-Langevin
#BP 156
#6, rue Jules Horowitz
#38042 Grenoble Cedex 9
#France
#pellegrini[at]ill.fr
#goret[at]ill.fr
#aoun[at]ill.fr
#
#This library is free software; you can redistribute it and/or
#modify it under the terms of the GNU Lesser General Public
#License as published by the Free Software Foundation; either
#version 2.1 of the License, or (at your option) any later version.
#
#This library is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#Lesser General Public License for more details.
#
#You should have received a copy of the GNU Lesser General Public
#License along with this library; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

''' 
Created on May 26, 2015

:author: Eric C. Pellegrini
'''

import os
import re
import tarfile

import numpy

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

    type = 'svg'
    
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
    
        tf.close()
