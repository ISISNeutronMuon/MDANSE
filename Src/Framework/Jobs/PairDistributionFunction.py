import numpy

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
    
    ancestor = ["mmtk_trajectory","molecular_viewer"]  
    
    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """   

        npoints = len(self.configuration['r_values']['mid_points'])

        self._outputData.add('r',"line", self.configuration['r_values']['mid_points'], units="nm") 
        
        for pair in self._elementsPairs:
            self._outputData.add("pdf_intra_%s%s" % pair,"line", (npoints,), axis='r', units="au")                                                 
            self._outputData.add("pdf_inter_%s%s" % pair,"line", (npoints,), axis='r', units="au",)                                                 
            self._outputData.add("pdf_total_%s%s" % pair,"line", (npoints,), axis='r', units="au")                                                 

        self._outputData.add("pdf_intra_total","line", (npoints,), axis='r', units="au")                                                 
        self._outputData.add("pdf_inter_total","line", (npoints,), axis='r', units="au")                                                 
        self._outputData.add("pdf_total","line", (npoints,), axis='r', units="au")                                                 
        
        nFrames = self.configuration['frames']['number']

        self.averageDensity /= nFrames
        
        densityFactor = 4.0*numpy.pi*self.configuration['r_values']['mid_points']
        
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
            
            self._outputData["pdf_intra_%s%s" % pair][:] = self.hIntra[idi,idj,:] / fact
            self._outputData["pdf_inter_%s%s" % pair][:] = self.hInter[idi,idj,:] / fact
            self._outputData["pdf_total_%s%s" % pair][:] = self._outputData["pdf_intra_%s%s" % pair][:] + self._outputData["pdf_inter_%s%s" % pair][:]

        weights = self.configuration["weights"].get_weights()
        
        pdfIntraTotal = weight(weights,self._outputData,nAtomsPerElement,2,"pdf_intra_%s%s")
        self._outputData["pdf_intra_total"][:] = pdfIntraTotal
        
        pdfInterTotal = weight(weights,self._outputData,nAtomsPerElement,2,"pdf_inter_%s%s")
        self._outputData["pdf_inter_total"][:] = pdfInterTotal

        pdfTotal = weight(weights,self._outputData,nAtomsPerElement,2,"pdf_total_%s%s")
        self._outputData["pdf_total"][:] = pdfTotal
                
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
        
        self.configuration['trajectory']['instance'].close()     
  
        super(PairDistributionFunction,self).finalize()
        
REGISTRY['pdf'] = PairDistributionFunction
        
