.. MDANSE documentation master file, created by
   sphinx-quickstart on Wed Nov  2 14:09:24 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to MDANSE's documentation!
==================================

.. note::
   This is the documentation of the MDANSE 2.0 release.
   The documentation, just like the code itself, is still under development.

Introduction
============

`MDANSE Project Website <https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx>`_

`MDANSE GitHub Page <https://github.com/ISISNeutronMuon/MDANSE>`_

**MDANSE** (**Molecular Dynamics Analysis for Neutron Scattering Experiments**)
is a python application designed for computing neutron observables
from molecular dynamics (MD) trajectories that can be directly compared with
neutron scattering experiments, particularly inelastic and quasi-elastic
neutron scattering spectroscopies.

To do this, it interfaces with a variety of MD simulation software such
as CASTEP, VASP, DMOL, Gromacs, DL_POLY, CHARMM, LAMMPS, PBD, DFTB etc., 
and provides both a graphical user interface (GUI) and a command line interface. 

This project is built on the development published previously: \
G. Goret, B. Aoun, E. Pellegrini, "MDANSE: An Interactive Analysis Environment for Molecular Dynamics Simulations", 
J Chem Inf Model. 57(1):1-5 (2017).


.. raw:: html

   <div class="sd-grid">
       <div class="grid-item">
           <h3>💡 Explanations</h3>
           <p>Learn the basics and core concepts of MDANSE.</p>
           <a href="pages/explanations.html">Learn More</a>
       </div>
       <div class="grid-item">
           <h3>⚛️ How-To Guides</h3>
           <p>Practical step-by-step guides to help you utilize MDANSE effectively.</p>
           <a href="pages/H_gui.html">Learn More</a>
       </div>
       <div class="grid-item">
           <h3>🧪 Tutorials</h3>
           <p>Detailed tutorials to help you get started with MDANSE.</p>
           <a href="pages/T_Batch.html">Learn More</a>
       </div>
       <div class="grid-item">
           <h3>📚 Technical References</h3>
           <p>Deep dive into the technical details of MDANSE.</p>
           <a href="pages/R_contact.html">Learn More</a>
       </div>
   </div>


.. toctree::
   :maxdepth: 5
   :caption: 💡 Explanations

   pages/introduction
   pages/installation
   pages/files
   pages/gui
   pages/cmd
   pages/workflow
   pages/dynamics
   pages/scattering
   pages/structure
   pages/analysis
   pages/trajectory
   pages/plotting
   pages/fca

.. toctree::
   :maxdepth: 5
   :caption: ⚛️ How-To Guides

   pages/H_gui
   pages/H_cli
   pages/H_Dynamics
   pages/H_Scattering
   pages/H_Structure
   pages/H_other
   pages/H_gloss
   pages/H_Plotting
   pages/H_fca

.. toctree::
   :maxdepth: 5
   :caption: 🧪 Tutorials

   pages/T_Batch
   pages/T_sim
   pages/T_Analysis

.. toctree::
   :maxdepth: 5
   :caption: 📚 Technical References

   pages/R_contact
   pages/parameters
   pages/R_traj
   pages/R_units
   pages/R_further
   pages/references

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
