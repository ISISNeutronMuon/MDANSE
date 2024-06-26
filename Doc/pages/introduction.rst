Introduction
============

Neutron scattering experiments are valuable tools for investigating the
structure and dynamics of materials. Computational simulations and
modeling plays a crucial role in analyzing and interpreting such experiments,
leading to improvements in existing materials and the design of new ones.
Atomistic simulations, particularly molecular dynamics (MD) simulations, are
increasingly employed for these purposes. However, predicting neutron observables
from MD trajectories is a complex process that involves various calculations and
transformations, such as mean square displacements, densities of states, velocity
and position auto- and cross-correlation functions, and
convolutions with instrument parameters, to obtain neutron observables that can
be directly compared with experimental data.

Purpose and Capabilities
------------------------

MDANSE serves as a versatile toolkit designed to streamline the analysis of
molecular dynamics simulations. Its primary objectives are to:

- Facilitate the visualization and animation of trajectory data.
- Enable the computation of various properties, including dynamics, infrared,
  scattering, structural, and thermodynamic properties.

Flexibility and Compatibility
-----------------------------

MDANSE offers:

- A Python-based graphical user interface (GUI) via the MDANSE_GUI package,
  including a trajectory viewer and a data plotter.
- Command-line utilities for creating and running MDANSE jobs as Python scripts.
- Specialised trajectory converters for specific MD engines.
- A general trajectory converter based on ASE.

Your Guide to MDANSE
---------------------

This user's guide provides a detailed overview of MDANSE's capabilities, along
with theoretical background information and installation instructions for three
different platforms: Windows, MacOS, and Ubuntu.

Collaboration and Feedback
--------------------------

The authors welcome suggestions, feedback, and bug reports regarding the MDANSE
software and this user's guide, we encourage you to report them. Your feedback is
essential in helping us enhance the software and improve the user experience.

GitHub Repository
-----------------

You can report issues and make suggestions on our GitHub repository. Please visit
the following link to access the `MDANSE GitHub repository <https://github.com/ISISNeutronMuon/MDANSE>`_
