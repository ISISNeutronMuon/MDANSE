# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/CoordinationNumber.py
# @brief     Implements module/class/test CoordinationNumber
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-2021
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections

import numpy

from MDANSE import REGISTRY
from MDANSE.Framework.Jobs.DistanceHistogram import DistanceHistogram

class CoordinationNumber(DistanceHistogram):
    """
    The Coordination Number is computed from the pair distribution function for a set of atoms. 
    It describes the total number of neighbours, as a function of distance, from a central atom, or the centre of a group of atoms.
    """

    label = "Coordination Number"
    
    category = ('Analysis','Structure',)
    
    ancestor = ["mmtk_trajectory","molecular_viewer"]        

    settings = collections.OrderedDict()
    settings['trajectory'] = ('mmtk_trajectory',{})
    settings['frames'] = ('frames', {'dependencies':{'trajectory':'trajectory'}})
    settings['r_values'] = ('range', {'valueType':float, 'includeLast':True, 'mini':0.0})
    settings['atom_selection'] = ('atom_selection', {'dependencies':{'trajectory':'trajectory'}})
    settings['atom_transmutation'] = ('atom_transmutation', {'dependencies':{'trajectory':'trajectory','atom_selection':'atom_selection'}})
    settings['output_files'] = ('output_files', {'formats':["netcdf","ascii"]})
    settings['running_mode'] = ('running_mode',{})
                
    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """   

        npoints = len(self.configuration['r_values']['mid_points'])

        self._outputData.add('r','line', self.configuration['r_values']['mid_points'], units="nm") 
        
        for pair in self._elementsPairs:
            invPair = pair[::-1]
            self._outputData.add("cn_intra_%s%s" % pair,"line", (npoints,), axis='r',units="au")                                                 
            self._outputData.add("cn_inter_%s%s" % pair,"line", (npoints,), axis='r', units="au",)                                                 
            self._outputData.add("cn_total_%s%s" % pair,"line", (npoints,), axis='r', units="au")                                                 
            self._outputData.add("cn_intra_%s%s" % invPair,"line", (npoints,), axis='r', units="au")                                                 
            self._outputData.add("cn_inter_%s%s" % invPair,"line", (npoints,), axis='r', units="au",)                                                 
            self._outputData.add("cn_total_%s%s" % invPair,"line", (npoints,), axis='r', units="au")                                                 
        
        nFrames = self.configuration['frames']['number']
        
        densityFactor = 4.0*numpy.pi*self.configuration['r_values']['mid_points']
        
        shellSurfaces = densityFactor*self.configuration['r_values']['mid_points']
        
        shellVolumes  = shellSurfaces*self.configuration['r_values']['step']
  
        self.averageDensity *= 4.0*numpy.pi/nFrames

        r2 = self.configuration['r_values']['mid_points']**2
        dr = self.configuration['r_values']['step']
        
        for k in self._concentrations.keys():
            self._concentrations[k] /= nFrames

        nAtomsPerElement = self.configuration['atom_selection'].get_natoms()
        for pair in self._elementsPairs:
            at1,at2 = pair 
            ni = nAtomsPerElement[at1]
            nj = nAtomsPerElement[at2]
            
            idi = self.selectedElements.index(at1)
            idj = self.selectedElements.index(at2)

            if idi == idj:
                nij = ni*(ni-1)/2.0    
            else:
                nij = ni*nj
                self.hIntra[idi,idj] += self.hIntra[idj,idi]
                self.hInter[idi,idj] += self.hInter[idj,idi]
            
            fact = nij*nFrames*shellVolumes
             
            self.hIntra[idi,idj,:] /= fact             
            self.hInter[idi,idj,:] /= fact
                         
            cnIntra = numpy.add.accumulate(self.hIntra[idi,idj,:]*r2)*dr
            cnInter = numpy.add.accumulate(self.hInter[idi,idj,:]*r2)*dr
            cnTotal = cnIntra + cnInter
            
            cAlpha = self._concentrations[pair[0]]
            cBeta = self._concentrations[pair[1]]
                        
            invPair = pair[::-1]

            self._outputData["cn_intra_%s%s" % pair][:] = self.averageDensity*cBeta*cnIntra
            self._outputData["cn_inter_%s%s" % pair][:] = self.averageDensity*cBeta*cnInter        
            self._outputData["cn_total_%s%s" % pair][:] = self.averageDensity*cBeta*cnTotal 
            self._outputData["cn_intra_%s%s" % invPair][:] = self.averageDensity*cAlpha*cnIntra
            self._outputData["cn_inter_%s%s" % invPair][:] = self.averageDensity*cAlpha*cnInter        
            self._outputData["cn_total_%s%s" % invPair][:] = self.averageDensity*cAlpha*cnTotal 

        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
        
        self.configuration['trajectory']['instance'].close()     
  
        DistanceHistogram.finalize(self)

REGISTRY['cn'] = CoordinationNumber
