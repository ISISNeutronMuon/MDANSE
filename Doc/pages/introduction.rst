Introduction
============

Neutron scattering experiments are valuable tools for investigating the
structure and dynamics of materials. Computational simulations and
modeling plays a crucial role in analyzing and interpreting such experiments,
leading to improvements in existing materials and the design of new ones.
Atomistic simulations, particularly molecular dynamics (MD) simulations, are
increasingly employed for these purposes. 
Many properties, including neutron observables, can be derived from
from MD trajectories. These include mean square displacement,
vibrational density of states, velocity
and position auto- and cross-correlation functions and van Hove functions.
In the case of neutron observables, the neutron scattering lengths of
the component atoms and convolutions with instrument parameters
need to be included in the calculation to produce neutron observables that can
be directly compared with experimental data.

Purpose and Capabilities
------------------------

MDANSE is a toolkit designed to analyse molecular dynamics simulations.
It can be used for

- visualization and animation of trajectory data,
- general trajectory analysis (average structure, dynamic properties, etc.)
- computation of neutron scattering observables,

Transferability and Compatibility
---------------------------------

- A Python-based graphical user interface (from the MDANSE_GUI package)
  can run different analysis types.
- The GUI can also save run parameters as scripts, which can be copied to
  and run on other platforms.
- Both the trajectories and the analysis results are saved as HDF5 files,
  and are transferable between different machines and operating systems.
- Specific trajectory converters are available for different MD engines,
  together with general trajectory converters based on ASE, MDAnalysis and mdtraj.

Your Guide to MDANSE
---------------------

This user's guide provides an overview of MDANSE's capabilities, along
with theoretical background information and installation instructions.

Collaboration and Feedback
--------------------------

The authors welcome suggestions, feedback, and bug reports regarding the MDANSE
software and this user's guide. Your feedback is
essential in helping us enhance the software and improve the user experience.
You can report issues and make suggestions on our `GitHub repository <https://github.com/ISISNeutronMuon/MDANSE>`_.
Alternatively, you can contact the developers directly by emailing us at MDANSE-help@stfc.ac.uk.
