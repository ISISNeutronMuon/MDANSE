.. MDANSE documentation master file, created by
   sphinx-quickstart on Wed Nov  2 14:09:24 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to MDANSE's documentation!
==================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

.. note::
   The MDANSE branch 1.5.x is the last one to be based on Python 2.
   Currently all the efforts of the developers of MDANSE are focused
   on preparing the MDANSE 2.0 release, based on Python 3.

Introduction
============

Molecular Dynamics Analysis for Neutron Scattering Experiments

MDANSE is a python application designed for computing neutron observables
from molecular dynamics (MD) trajectories that can be directly compared with
neutron scattering experiments, particularly inelastic and quasi-elastic
neutron scattering spectroscopies.

To do this, it interfaces with a variety of MD simulation software such
as CASTEP, VASP, DMOL, Gromacs, DLPOY, CHARMM, LAMMPS, PBD, DFTB etc., 
and provides both a graphical user interface (GUI) and a command line interface. 

This project is built on the development published previously: \
G. Goret, B. Aoun, E. Pellegrini, "MDANSE: An Interactive Analysis Environment for Molecular Dynamics Simulations", 
J Chem Inf Model. 57(1):1-5 (2017).


.. toctree::
   :maxdepth: 4
   :numbered:
   :hidden:
   :caption: MDANSE User Manual

   pages/opening
   pages/authors
   pages/introduction
   pages/installation
   pages/build
   pages/files
   pages/gui
   pages/dynamics
   pages/scattering
   pages/structure
   pages/analysis
   pages/cmd
   pages/trajectory
   pages/plotting
   pages/parameters
   pages/fca
   pages/references

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
