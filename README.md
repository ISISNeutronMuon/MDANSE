# MDANSE 

## Molecular Dynamics Analysis for Neutron Scattering Experiments

MDANSE is a Python application designed for computing neutron observables from molecular dynamics (MD) trajectories. The results can 
be directly compared with neutron scattering experiments, particularly inelastic and quasi-elastic neutron scattering 
spectroscopies.

To do this, it interfaces with a variety of MD simulation software such as CASTEP, VASP, DMOL, Gromacs, DL_POLY, CHARMM, LAMMPS, PBD, DFTB etc., and provides both a graphical user interface (GUI) and a command line interface. 

This project is built on the development published previously: \
G. Goret, B. Aoun, E. Pellegrini, "MDANSE: An Interactive Analysis Environment for Molecular Dynamics Simulations", 
J Chem Inf Model. 57(1):1-5 (2017).

## Version information

This is the development version of MDANSE. The main difference compared to the previous version is the transition from Python 2 to Python 3, and from wxWidgets to Qt. The previous version, formerly in the 'develop' branch, can now be found in the **legacy** branch.

The current version of MDANSE is currently still at the _alpha_ stage. You can help it advance to the _beta_ stage by reporting problems you experience while using MDANSE.

## Quick start: installation

We recommend that you install MDANSE in a Python virtual environment. You can create a virtual environment named mdanse_env by typing
```
python3 -m venv mdanse_env
```

To activate your virtual environment, type
```
source mdanse_env/bin/activate
```
in a bash console, or
```
mdanse_end/Scripts/activate.bat
```
if you are using cmd.exe on Windows.

While your virtual environment is active, you can install MDANSE:
```
pip install MDANSE MDANSE_GUI
```
and start the graphical interface by typing
```
mdanse_gui
```

The typical workflow of MDANSE:

1. Convert a trajectory from the file format generated by an MD simulation software into the MDANSE trajectory format,
2. Load the converted trajectory into MDANSE,
3. Perform an analysis,
4. Check the results with the plotter.


The most complete user documentation of MDANSE can be found on [our Read the Docs page](https://mdanse.readthedocs.io/en/protos). At the same time, it is still possible to access the original **[MDANSE User Guide](https://epubs.stfc.ac.uk/work/51935555)**.

Other information including example scripts can be found on the [MDANSE website](https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx) 

## What can MDANSE do?

Firstly, MDANSE can interface with MD simulation software. It does this by providing converters for different file formats
into an .MDT file (HDF format), which is then used for all calculations. The following MD packages are supported:

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
- ASE

The converted trajectory can then be loaded into MDANSE, where it can be visualised via the Molecular Viewer and animated.
Various trajectory variables (positions, velocities, and forces) can also be plotted for each particle. Then, various properties can be calculated, which can be compared with neutron (or, for some analysis types, with X-ray)
experimental data, or used as a prediction of results of a potential experiment. The following properties can be computed:

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
<li>Infrared</li>
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
<li>Voronoi (volume per atom)</li>
<li>X-Ray Static Structure Factor</li>
</ul></details>

<details><summary>Thermodynamics</summary><ul>
<li>Density</li>
<li>Temperature</li>
</ul></details>

Each of these analyses can be controlled using a number of parameters. For example, the user can select a subset of trajectory frames or a subset of atoms on which to perform the calculation, or specified atoms can be substituted with
different elements/isotopes. Finally, their results can be saved in an MDA file (HDF5 format), or a set of DAT files (text format), and those can then be plotted directly in MDANSE.

More detailed information on how MDANSE works, what it can do, and the science can all be found on [our Read the Docs page](https://mdanse.readthedocs.io/en/protos).

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
from the libraries [MMTK](https://github.com/khinsen/MMTK), [ScientificPython](https://github.com/khinsen/ScientificPython)
and [MDTraj](https://github.com/mdtraj/mdtraj).

For more information see:

>nMoldyn 3: Using task farming for a parallel spectroscopy-oriented analysis of molecular dynamics simulations.
K. Hinsen, E. Pellegrini, S. Stachura, G.R. Kneller J. Comput. Chem. (2012) 33:2043-2048 [https://doi.org/10.1002/jcc.23035][https://doi.org/10.1002/jcc.23035]. 

We are grateful to all the people who have helped in some way or another to improve nMOLDYN and/or MDANSE along those years. 
Apart from the main developers mentioned above, we would like to acknowledge explicitly the contributions done in the past 
by Bachir Aoun, Vania Calandrini, Paolo Calligari, Gael Goret, Remi Perenon and Rastislav Turanyi.

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

## Software Inquiries

For questions or contributions related to the software, please contact:

>Dr. Maciej Bartkowiak (maciej.bartkowiak@stfc.ac.uk)\
ISIS Neutron and Muon Source \
Rutherford Appleton Laboratory \
Didcot, UK
