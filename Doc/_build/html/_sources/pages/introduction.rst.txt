
Introduction
============

Neutron scattering experiments are useful tools for probing atomic
positions and molecular dynamics in materials. Computational simulations
and modelling are essential tools to analyse and interpret such
experiments. These interpretations help to improve existing materials
for bespoke applications and design new ones. Atomistic simulations,
particularly molecular dynamics (MD) simulations are being used
increasingly for these purposes. However, predicting neutron observables
from MD trajectories is not straightforward. A number of operations,
such as calculations of mean square displacements, densities of states,
velocity and position auto- and cross-correlation functions, Fourier
transformations and convolutions with instrument parameters are required
to calculate neutron observables that can be compared directly with
experimental data.

Some of these steps were implemented in the open source MDANSE
(Molecular Dynamics Analysis of Neutron Scattering Experiments)
[`1 <#SignetBibliographie_001>`__]. This software is a Python based
application for analysing MD simulation data. This has interface with
more than ten MD codes including ab-initio MD codes as listed in
Appendix 1. MDANSE is benefited from a simple python-based graphical
users interface (GUI) to compare the calculated spectrum with
experimental data. It also can be used through command line scripts. In
addition to this GUI, a well developed molecular viewer and 2D/3D
plotter improve the users experience in analysing neutron experimental
data.

This users guide provides a detailed overview of the capabilities of
MDANSE along with theoretical background and installation instructions
on three different platforms Windows, Mac OS and Ubuntu. Authors will be
happy to receive any suggestions, feedback and bug reports about the
MDANSE software and this Users guide.
