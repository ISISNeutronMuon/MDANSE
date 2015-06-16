#MDANSE : Molecular Dynamics Analysis for Neutron Scattering Experiments
#------------------------------------------------------------------------------------------
#Copyright (C)
#2015- Eric C. Pellegrini Institut Laue-Langevin
#BP 156
#71 avenue des Martyrs
#38000 Grenoble Cedex 9
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
Created on Apr 10, 2015

:author: Eric C. Pellegrini
'''

import collections

import numpy

from MDANSE import ELEMENTS
from MDANSE.Framework.Jobs.DistanceHistogram import DistanceHistogram
from MDANSE.Mathematics.Arithmetic import weight

class StaticStructureFactor(DistanceHistogram):
    """
    Computes the static structure factor from the pair distribution function for a set of atoms.
    """

    type = 'ssf'

    label = "Static Structure Factor"
    
    category = ('Structure',)
    
    ancestor = "mmtk_trajectory"
    
    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['r_values'] = ('range', {'valueType':float, 'includeLast':True, 'mini':0.0})
    settings['q_values'] = ('range', {'valueType':float, 'includeLast':True, 'mini':0.0})
    settings['atom_selection'] = ('atom_selection', {'dependencies':{'trajectory':'trajectory'}})
    settings['transmutated_atoms'] = ('atom_transmutation', {'dependencies':{'trajectory':'trajectory',
                                                                                  'atom_selection':'atom_selection'}})
    settings['weights'] = ('weights', {'default':'b_coherent'})
    settings['output_files'] = ('output_files', {'formats':["netcdf","ascii"]})
    settings['running_mode'] = ('running_mode',{})
                
    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """   

        nq = self.configuration['q_values']['number']
                
        nFrames = self.configuration['frames']['number']

        self.averageDensity /= nFrames
        
        densityFactor = 4.0*numpy.pi*self.configuration['r_values']['mid_points']
        
        shellSurfaces = densityFactor*self.configuration['r_values']['mid_points']
        
        shellVolumes  = shellSurfaces*self.configuration['r_values']['step']

        self._outputData.add('q',"line", self.configuration['q_values']['value'], units="inv_nm") 

        q = self._outputData['q']
        r = self.configuration['r_values']['mid_points']
  
        fact1 = 4.0*numpy.pi*self.averageDensity

        sincqr = numpy.sinc(numpy.outer(q,r)/numpy.pi)
        
        dr = self.configuration['r_values']['step']
        
        for pair in self._elementsPairs:

            self._outputData.add("ssf_intra_%s%s" % pair,"line", (nq,), axis='q', units="au")                                                 
            self._outputData.add("ssf_inter_%s%s" % pair,"line", (nq,), axis='q', units="au",)                                                 
            self._outputData.add("ssf_total_%s%s" % pair,"line", (nq,), axis='q', units="au")                                                 

            ni = self.configuration['atom_selection']['n_atoms_per_element'][pair[0]]
            nj = self.configuration['atom_selection']['n_atoms_per_element'][pair[1]]
            
            idi = self.selectedElements.index(pair[0])
            idj = self.selectedElements.index(pair[1])

            if pair[0] == pair[1]:
                nij = ni*(ni-1)/2.0    
            else:
                nij = ni*nj
                self.hIntra[idi,idj] += self.hIntra[idj,idi]
                self.hInter[idi,idj] += self.hInter[idj,idi]
            
            fact = nij*nFrames*shellVolumes

            pdfIntra = self.hIntra[idi,idj,:] / fact
            pdfInter = self.hInter[idi,idj,:] / fact
                        
            self._outputData["ssf_intra_%s%s" % pair][:] = fact1*numpy.sum((r**2)*pdfIntra*sincqr,axis=1)*dr
            self._outputData["ssf_inter_%s%s" % pair][:] = 1.0 + fact1*numpy.sum((r**2)*(pdfInter-1.0)*sincqr,axis=1)*dr
            self._outputData["ssf_total_%s%s" % pair][:] = self._outputData["ssf_intra_%s%s" % pair][:] + self._outputData["ssf_inter_%s%s" % pair][:]

        self._outputData.add("ssf_intra","line", (nq,), axis='q', units="au")                                                 
        self._outputData.add("ssf_inter","line", (nq,), axis='q', units="au",)                                                 
        self._outputData.add("ssf_total","line", (nq,), axis='q', units="au")                                                 

        props = dict([[k,ELEMENTS[k,self.configuration["weights"]["property"]]] for k in self.configuration['atom_selection']['n_atoms_per_element'].keys()])

        ssfIntra = weight(props,
                          self._outputData,
                          self.configuration['atom_selection']['n_atoms_per_element'],
                          2,
                          "ssf_intra_%s%s")
        self._outputData["ssf_intra"][:] = ssfIntra

        ssfInter = weight(props,
                          self._outputData,
                          self.configuration['atom_selection']['n_atoms_per_element'],
                          2,
                          "ssf_inter_%s%s")

        self._outputData["ssf_inter"][:] = ssfInter
 
        self._outputData["ssf_total"][:] = ssfIntra + ssfInter
        
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
        
        self.configuration['trajectory']['instance'].close()