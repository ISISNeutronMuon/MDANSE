.. MDANSE documentation master file, created by
   sphinx-quickstart on Wed Nov  2 14:09:24 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to MDANSE's documentation!
==================================

**Useful links**: `MDANSE GitHub <https://github.com/ISISNeutronMuon/MDANSE>`_ | `MDANSE-Examples GitHub <https://github.com/ISISNeutronMuon/MDANSE-Examples>`_

**MDANSE (Molecular Dynamics Analysis for Neutron Scattering Experiments)**
is a Python application designed for computing neutron observables
from molecular dynamics (MD) trajectories.
The results can be directly compared with
neutron scattering experiments, particularly inelastic and quasi-elastic
neutron scattering spectroscopies.

MDANSE can analyse MD trajectories 
produced by different simulation software, including
CASTEP, VASP, Gromacs, DL_POLY, CHARMM, LAMMPS, DFTB and CP2K.
General-purpose trajectory converters using external libraries
(ASE, mdtraj and MDAnalysis) are also available in MDANSE.

The recommended way of working with MDANSE is via the
graphical user interface (GUI) provided by
the `MDANSE_GUI Python package <https://pypi.org/project/MDANSE-GUI/>`_.
However, it is also possible to install only
`the core MDANSE package <https://pypi.org/project/MDANSE/>`_ and
use it to run analysis scripts
(also the scripts created in the GUI on another platform).

The MDANSE project has been published previously in: \
`G. Goret, B. Aoun, E. Pellegrini, "MDANSE: An Interactive Analysis Environment for Molecular Dynamics Simulations",
J. Chem. Inf. Model. 2017, 57, 1, 1–5 <https://doi.org/10.1021/acs.jcim.6b00571>`_.


.. raw:: html

   <div class="sd-grid">
       <div class="grid-item">
           <h3>💡 Explanations</h3>
           <p>Learn the basics and core concepts of MDANSE.</p>
           <a href="pages/introduction.html">Learn More</a>
       </div>
       <div class="grid-item">
           <h3>⚛️ How-To Guides</h3>
           <p>Practical step-by-step guides to help you utilize MDANSE effectively.</p>
           <a href="pages/H_start.html">Learn More</a>
       </div>
       <div class="grid-item">
           <h3>🧪 Tutorials</h3>
           <p>Detailed tutorials to help you get started with MDANSE.</p>
           <a href="pages/T_external.html">Learn More</a>
       </div>
       <div class="grid-item">
           <h3>📚 Technical References</h3>
           <p>Deep dive into the technical details of MDANSE.</p>
           <a href="pages/R_contact.html">Learn More</a>
       </div>
   </div>

.. toctree::
   :maxdepth: 5
   :hidden:
   :caption: 💡 Explanations

   pages/introduction
   pages/getting_started
   pages/files
   pages/workflow
   pages/trajectory
   pages/correlation
   pages/weights
   pages/grouping
   pages/atom_selection
   pages/qvectors
   pages/dynamics
   pages/scattering
   pages/structure
   pages/analysis
   pages/notation

.. toctree::
   :maxdepth: 5
   :hidden:
   :caption: ⚛️ How-To Guides

   pages/H_start
   pages/H_conv
   pages/H_Plotting
   pages/H_cluster

.. toctree::
   :maxdepth: 5
   :hidden:
   :caption: 🧪 Tutorials

   pages/T_external

.. toctree::
   :maxdepth: 5
   :hidden:
   :caption: 📚 Technical References

   pages/R_contact
   pages/R_traj
   pages/R_parameters
   pages/converters
   pages/analysis_jobs
   pages/vector_generators
   pages/parameters
   pages/R_units
   pages/R_parallel
   pages/R_further
   pages/references
