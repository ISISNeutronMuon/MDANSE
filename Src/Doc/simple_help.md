MDANSE - simple help
====================

Sequence of operations in MDANSE: 
---------------------------------

1. Convert trajectory into MDANSE-usable form. 

2. Load converted trajectory (.nc file). 

3. Molecular viewer plugin allows e.g. atom selection. Q-vector plugin allows these to be defined for analyses.

4. Run analyses - many can be 
run simultaneously on one or several processors. 

5. Plot results.

**Convertors** are required to transform the standard MD trajectories from MD codes into a form that is usable by MDANSE (netcdf format). For non-standard trajectories, a generic convertor for ascii files is available.

**Q-vectors** are required when calculating quantities like I(Q,t) and S(Q,w). From analyses windows, they are chosen from available definitions, which in-turn are determined from the Q-vector plug-in. Q-vectors can be generated in a number of ways, the most common (for a periodic system) being the *spherical lattice* in terms of Q (units nm-1) and 'grid' in terms of (h,k,l). The generated list of Q-vectors can be visualized and saved with a name which is then available for corresponding analyses for the trajectory. 

**Instrument resolution** is a function which determines the window function which is used when time-dependent data is Fourier transformed into the frequency domain - it is used to mimic the resolution function of a neutron scattering instrument. The 'set' button allows the functional form and corresponding parameters to be visualized and saved. Analyses using the Fast Fourier Transform are much faster if the number of frames is a power of 2.

**Weights** are required in many analyses, for example the coherent scattering length (b_coherent) for the Dynamic Coherent Structure Factor (DCSF). The most reasonable weighting scheme is proposed for each analysis. It can be changed from the drop-down list. The corresponding values are shown in the periodic table and associated table of data. They can be edited and saved. Any data in the table can be used for the weighting scheme. 

**Atom selection** allows analyses to be performed on subsets of atoms. Choosing the *molecular viewer* plugin shows the molecular model which in-turn allows the *atom selection* plugin to be chosen. The atom colors in the molecular viewer can also be edited in the periodic table of data. The interface allows selections to be made using keywords (atom names, types, groups, residues, etc), python scripts, mouse clicks in the model window (which is very useful when selecting atoms in specific positions) and a box widget (selection by regions of the periodic lattice). The atom selection is saved with a name and is available in all relevant analyses.

**Atom transmutation** works as for atom selection. The final atom type for the selected atoms must then be chosen from the drop-down list. This is typically used to replace hydrogen with deuterium in neutron scattering studies. 

**Units** the basic units in MDANSE are
- ps for time
- THz for frequency
- nm for distance
- nm-1 for Q. 

These units can be changed in the plotter e.g. THz to meV or invcm (wavenumber), nm to ang, invnm to invang.
