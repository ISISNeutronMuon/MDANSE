# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/PairDistributionFunction.py
# @brief     Implements module/class/test PairDistributionFunction
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import numpy as np

from MDANSE import REGISTRY
from MDANSE.Framework.Jobs.DistanceHistogram import DistanceHistogram
from MDANSE.Mathematics.Arithmetic import weight


class PairDistributionFunction(DistanceHistogram):
    """
    The Pair-Distribution Function (PDF) is an example of a pair correlation function, which
    describes how, on average, the atoms in a system are radially packed around each other. 
    This is a particularly effective way of describing the average structure of disordered 
    molecular systems such as liquids. Also in systems like liquids, where there is continual movement
    of the atoms and a single snapshot of the system shows only the instantaneous disorder, it is
    essential to determine the average structure.
    
    The PDF can be compared with experimental data from x-ray or neutron diffraction. 
	It can be used in conjunction with the inter-atomic pair potential 
    function to calculate the internal energy of the system, usually quite accurately.
	Finally it can even be used to derive the inter-atomic potentials of mean force.
    """

    label = "Pair Distribution Function"
    
    category = ('Analysis','Structure',)
    
    ancestor = ['hdf_trajectory','molecular_viewer']
    
    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """   

        npoints = len(self.configuration['r_values']['mid_points'])

        self._outputData.add('r',"line", self.configuration['r_values']['mid_points'], units="nm") 
        
        for x, y in self._elementsPairs:
            for i in ['pdf', 'rdf', 'tcf']:
                self._outputData.add("%s_intra_%s%s" % (i, x, y),"line", (npoints,), axis='r', units="au")
                self._outputData.add("%s_inter_%s%s" % (i, x, y),"line", (npoints,), axis='r', units="au")
                self._outputData.add("%s_total_%s%s" % (i, x, y),"line", (npoints,), axis='r', units="au")

        for i in ['pdf', 'rdf', 'tcf']:
            self._outputData.add("%s_intra_total" % i,"line", (npoints,), axis='r', units="au")
            self._outputData.add("%s_inter_total" % i,"line", (npoints,), axis='r', units="au")
            self._outputData.add("%s_total" % i,"line", (npoints,), axis='r', units="au")

        nFrames = self.configuration['frames']['number']

        self.averageDensity /= nFrames
        
        densityFactor = 4.0*np.pi*self.configuration['r_values']['mid_points']
        
        shellSurfaces = densityFactor*self.configuration['r_values']['mid_points']
        
        shellVolumes  = shellSurfaces*self.configuration['r_values']['step']
  
        nAtomsPerElement = self.configuration['atom_selection'].get_natoms()

        for pair in self._elementsPairs:
            ni = nAtomsPerElement[pair[0]]
            nj = nAtomsPerElement[pair[1]]
            
            idi = self.selectedElements.index(pair[0])
            idj = self.selectedElements.index(pair[1])

            if idi == idj:
                nij = ni*(ni-1)/2.0    
            else:
                nij = ni*nj
                self.hIntra[idi,idj] += self.hIntra[idj,idi]
                self.hInter[idi,idj] += self.hInter[idj,idi]
            
            fact = nij*nFrames*shellVolumes

            pdf_intra = self.hIntra[idi,idj,:] / fact
            pdf_inter = self.hInter[idi,idj,:] / fact
            pdf_total = pdf_intra + pdf_inter

            for i, pdf in zip(["intra", "inter", "total"], [pdf_intra, pdf_inter, pdf_total]):
                self._outputData["pdf_%s_%s%s" % (i, pair[0], pair[1])][:] = pdf
                self._outputData["rdf_%s_%s%s" % (i, pair[0], pair[1])][:] = shellSurfaces * self.averageDensity * pdf
                self._outputData["tcf_%s_%s%s" % (i, pair[0], pair[1])][:] = densityFactor * self.averageDensity * \
                                                                             (pdf if i == 'intra' else pdf - 1)

        weights = self.configuration["weights"].get_weights()

        for i in ['_intra', '_inter', '']:
            pdf = weight(weights, self._outputData, nAtomsPerElement, 2, "pdf{}_%s%s".format(i if i else '_total'))
            self._outputData["pdf%s_total" % i][:] = pdf
            self._outputData["rdf%s_total" % i][:] = shellSurfaces * self.averageDensity * pdf
            self._outputData["tcf%s_total" % i][:] = densityFactor * self.averageDensity * (pdf if i == '_intra'
                                                                                            else pdf - 1)

        self._outputData.write(self.configuration['output_files']['root'],
                               self.configuration['output_files']['formats'], self._info)
        
        self.configuration['trajectory']['instance'].close()     
  
        super(PairDistributionFunction,self).finalize()


REGISTRY['pdf'] = PairDistributionFunction
        
