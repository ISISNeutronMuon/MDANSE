# MDANSE 

## Molecular Dynamics Analysis for Neutron Scattering Experiments

MDANSE is a python application designed for computing neutron observables from molecular dynamics (MD) trajectories that can 
be directly compared with neutron scattering experiments, particularly inelastic and quasi-elastic neutron scattering 
spectroscopies.

To do this, it interfaces with a variety of MD simulation software such as CASTEP, VASP, DMOL, Gromacs, DL_POLY, CHARMM, LAMMPS, PBD, DFTB etc., 

and provides both a graphical user interface (GUI) and a command line interface. 

This project is built on the development published previously: \
G. Goret, B. Aoun, E. Pellegrini, "MDANSE: An Interactive Analysis Environment for Molecular Dynamics Simulations", 
J Chem Inf Model. 57(1):1-5 (2017).

## Quick start

The easiest way to start using MDANSE is to download a built installer from [MDANSE website](https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx) 
or our latest [github release](https://github.com/ISISNeutronMuon/MDANSE/releases/).
There, we provide installers for the major operating systems, Windows, Linux and MacOS, which can be downloaded and installed
any other software on that OS. After that, we recommend starting by using the GUI. The typical workflow will look as follows:

1. Convert a trajectory from the file format generated by an MD simulation software into a NetCDF format (File>Trajectory conveters)
2. Load the converted trajectory into MDANSE (File>Load data)
3. Perform an analysis of choice (through the Plugins panel)
4. Check the results with the plotter


The most complete user documentation of MDANSE can be found on [our Read the Docs page](https://mdanse.readthedocs.io). At the same time, it is still possible to access the original **[MDANSE User Guide](https://epubs.stfc.ac.uk/work/51935555)** \

Other information including example scripts can be found on the [MDANSE website](https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx) 


## Installing from source

Since MDANSE is currently written in Python 2.7, installing it from the source code can be challenging. There are guides
for doing this in the [MDANSE User Guide](https://epubs.stfc.ac.uk/work/51935555), 
[this issue](https://github.com/ISISNeutronMuon/MDANSE/issues/8), and the [Wiki](https://github.com/ISISNeutronMuon/MDANSE/wiki).
However, if your system is not included in any of these, or you have any difficulties, please don't hesitate to contact us.

## What can MDANSE do?

Firstly, MDANSE can interface with MD simulation software. It does this by providing converters for proprietary file formats
into MMTK-style NetCDF format, which is then used for all calculations. The following MD packages are supported:

- CASTEP
- CHARMM
- DFTB 
- Discover 
- DL_POLY 
- DMol 
- Forcite
- Gromacs
- LAMMPS
- NAMD
- PDB
- VASP
- XPLOR

The converted trajectory can then be loaded into MDANSE, where it can be visualised via the Molecular Viewer and animated.
Various trajectory variables (positions, velocities, and forces) can also be plotted for each particle. Then, if the 
trajectory is as expected, various properties can be calculated, which can be compared with neutron (or, some, with X-ray)
experimental data, or used as new data to draw conclusions from. The following properties can be computed:

<details><summary>Dynamics</summary><ul>
<li>Angular correlation</li>
<li>Density of states</li>
<li>Mean Square Displacement</li>
<li>Order parameter</li>
<li>Position Autocorrelation Function</li>
<li>Velocity Autocorrelation Function</li>
</ul></details>

<details><summary>Infrared</summary><ul>
<li>Dipole Autocorrelation Function</li>
</ul></details>

<details><summary>Scattering</summary><ul>
<li>Current correlation function</li>
<li>Dynamic Coherent Structure Factor</li>
<li>Dynamic Incoherent Structure Factor</li>
<li>Elastic Incoherent Structure Factor</li>
<li>Gaussian Dynamic Incoherent Structure Factor</li>
<li>Neutron Dynamic Total Structure Factor</li>
</ul></details>

<details><summary>Structural</summary><ul>
<li>Area Per Molecule</li>
<li>Coordination Number</li>
<li>Density Profile</li>
<li>Eccentricity</li>
<li>Molecular Trace</li>
<li>Pair Distribution Function</li>
<li>Root Mean Square Deviation</li>
<li>Root Mean Square Fluctuation</li>
<li>Radius of Gyration</li>
<li>Solvent Accessible Surface</li>
<li>Spatial Density</li>
<li>Static Structure Factor</li>
<li>Voronoi</li>
<li>X-Ray Static Structure Factor</li>
</ul></details>

<details><summary>Thermodynamics</summary><ul>
<li>Density</li>
<li>Temperature</li>
</ul></details>

Each of these analyses can be configured in various ways. For example, the frames that are used can be changed, certain
atoms can be specified to be the only ones for which the property is computed, or specified atoms can be substituted with
different elements/isotopes. Finally, their results can be outputted in a NetCDF file, an HDF5 file, or a set of DAT 
files, and those can then be plotted directly in MDANSE.

More detailed information on how MDANSE works, what it can do, and the science can all be found in the 
**[MDANSE User Guide](https://epubs.stfc.ac.uk/work/51935555)**

## Citing MDANSE

If you used MDANSE in your research, please cite the following paper:

>MDANSE: An Interactive Analysis Environment for Molecular Dynamics Simulations.
G. Goret, B. Aoun, E. Pellegrini. J Chem Inf Model. (2017) 57(1):1-5.

## License

MDANSE is licensed under GPL-3.0. See [LICENSE](https://github.com/ISISNeutronMuon/MDANSE/blob/develop/LICENSE) for more 
information.


## Acknowledgements

MDANSE started as a fork of [version 3 of the nMOLDYN program](https://github.com/khinsen/nMOLDYN3).
nMOLDYN was originally developed by Gerald Kneller in 1995 and subsequently also by Konrad Hinsen, Tomasz Rog,
Krzysztof Murzyn, Slawomir Stachura, and Eric Pellegrini. MDANSE includes most of the code of nMOLDYN3, and also code
from the libraries [MMTK](https://github.com/khinsen/MMTK) and [ScientificPython](https://github.com/khinsen/ScientificPython),
in order to reduce dependencies and thus facilitate installation.

For more information see:

>nMoldyn 3: Using task farming for a parallel spectroscopy-oriented analysis of molecular dynamics simulations.
K. Hinsen, E. Pellegrini, S. Stachura, G.R. Kneller J. Comput. Chem. (2012) 33:2043-2048 [https://doi.org/10.1002/jcc.23035][https://doi.org/10.1002/jcc.23035]. 

We are grateful to all the people who have helped in some way or another to improve nMOLDYN and/or MDANSE along those years. 
Apart from the main developers mentioned above, we would like to acknowledge explicitly the contributions done in the past 
by Bachir Aoun, Vania Calandrini, Paolo Calligari, Gael Goret and Remi Perenon.

The MDANSE project is supported by Ada Lovelace Centre, ISIS Neutron and Muon Source, Science
and Technology Facilities Council, UKRI, and the Institut Laue-Langevin (Grenoble, France). 
Past financial support from the French Agence Nationale de la Recherche (ANR) through contracts 
No. ANR-2010-COSI-001-01 and ANR-06-CIS6-012-01, and the Horizon 2020 Framework Programme of 
the European Union under project number 654000 is also acknowledged.

## Joining the project

MDANSE is currently maintained and developed by software developers from ISIS and ILL, but we are fully open to new
collaborators who would like to contribute code, documentation, tutorials or usage examples.
If you want to join the project contact:

>Dr. Sanghamitra Mukhopadhyay (sanghamitra.mukhopadhyay@stfc.ac.uk) \
ISIS Neutron and Muon Source \
Rutherford Appleton Laboratory \
Didcot, UK
