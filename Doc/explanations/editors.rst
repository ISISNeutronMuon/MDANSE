
This section is dealing with specific types of trajectory editors performed by
MDANSE. If you are not sure where these fit into the general workflow
of data analysis, please read :ref:`workflow-of-analysis`.


Editors
^^^^^^^

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
