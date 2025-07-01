
This section is dealing with specific types of analysis performed by
MDANSE. If you are not sure where these fit into the general workflow
of data analysis, please read :ref:`workflow-of-analysis`.

Analysis: Other
===============

This section contains background theory for following plugins:

-  :ref:`infrared`
-  :ref:`dipole-autocorrelation-function`
-  :ref:`density`
-  :ref:`temperature`
-  :ref:`center-of-masses-trajectory`


Infrared
^^^^^^^^

.. _infrared:

Infrared
''''''''
Calculates the molecular infrared spectrum averaged over all molecules
in the trajectory. The infrared spectrum is calculated from the Fourier
transform of the autocorrelation of the time-derivative of the
molecular dipole:

.. math::
   :label: ir1

   I(\omega) \propto  \frac{1}{N_{m}}\sum_{m} \frac{1}{6\pi} \int \mathrm{d}t \,  \left\langle \dot{\vec{\mu}}_{m}(0) \cdot \dot{\vec{\mu}}_{m}(t) \right\rangle e^{-i\omega t}

where :math:`N_{m}` is the number of molecules and :math:`\dot{\vec{\mu}}_{m}(t)` is
the time-derivative of the molecular dipole moment of molecule :math:`m`.

.. _dipole-autocorrelation-function:

Dipole Autocorrelation Function
'''''''''''''''''''''''''''''''

Calculates the molecular dipole autocorrelation function which is closely
related to the molecular infrared spectrum

.. math::
   :label: ir2

   \mathrm{DACF}(t) = \frac{1}{3 N_{m}}\sum_{m} \left\langle \vec{\mu}_{m}(0) \cdot \vec{\mu}_{m}(t) \right\rangle

where :math:`N_{m}` is the number of molecules :math:`m` and :math:`\vec{\mu}(t)` is
the molecular dipole moment of molecule :math:`m`.


Thermodynamics
^^^^^^^^^^^^^^

.. _density:

Density
'''''''
Density is used in molecular dynamics simulations to calculate and
analyze the density of particles within a simulated system. Density
refers to the concentration of particles (atoms, molecules, or ions)
in a given volume of space. This helps researchers understand how
particles are distributed within the simulation box and how their
density changes over time. By calculating density profiles or histograms,
scientists can gain insights into phase transitions, the formation of
clusters, or the behavior of molecules in various regions of the system.
Understanding density is crucial for studying phase changes, solvation,
and other thermodynamic processes in molecular systems.

.. _temperature:

Temperature
'''''''''''
The temperature is another essential tool in molecular dynamics
simulations that allows researchers to monitor and control the
temperature of the simulated system. Temperature is a fundamental
thermodynamic variable that influences molecular motion and interactions.
This plugin provides the means to calculate and adjust the temperature
throughout a simulation, ensuring that the system remains at the desired
temperature or follows a specific temperature profile. Monitoring
temperature fluctuations and deviations from the desired values is
crucial for accurately simulating and understanding the thermodynamic
behavior of molecules. Controlling temperature is particularly
important when studying phase transitions, chemical reactions, and
equilibrium properties of molecular systems.

Trajectory
^^^^^^^^^^

.. _center-of-masses-trajectory:

Center Of Masses Trajectory
'''''''''''''''''''''''''''

The center of mass trajectory (COMT) analysis consists in deriving the
trajectory of the respective centres of mass of a set of groups of
atoms. In order to produce a visualizable trajectory, MDANSE assigns
the centres of mass to pseudo-hydrogen atoms whose mass is equal to the
mass of their associated group. Thus, the produced trajectory can be
reused for other analysis. In that sense, COMT analysis is a practical
way to reduce noticeably the dimensionality of a system.

.. _trajectory-editor:

Trajectory Editor
'''''''''''''''''

It is a general-purpose tool for writing out a new trajectory with
contents different to the input one. 

At the moment, the main applications include:

- molecule detection,
- setting unit cell parameters,
- setting partial charges,
- removing or transmuting atoms,
- removing frames.
