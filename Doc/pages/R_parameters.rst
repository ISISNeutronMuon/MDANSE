
.. _parameters:

Commonly used parameters
========================

This is a detailed explanation of a few input parameters that are most commonly
used by MDANSE.
A full list can be found in section :ref:`full_parameter_list`.

Frames
~~~~~~

+--------------+---------+------------------+---------------------------------------------------------+
| Parameter    | Format  | Default Value    | Description                                             |
+==============+=========+==================+=========================================================+
| First frame  | int     | 0                | The frame from which the analysis will begin, the       |
|              |         |                  | first frame taken into account.                         |
+--------------+---------+------------------+---------------------------------------------------------+
| Last frame   | int     | Last frame       | The frame until which the analysis proceeds. The last   |
|              |         |                  | frame taken into account.                               |
+--------------+---------+------------------+---------------------------------------------------------+
| Frame step   | int     | 1                | Determines the periodicity of which steps are used      |
|              |         |                  | and which are skipped. 1 means that all frames are      |
|              |         |                  | read, 2 means every other is read, etc.                 |
+--------------+---------+------------------+---------------------------------------------------------+


Correlation Frames
~~~~~~~~~~~~~~~~~~

+--------------+---------+------------------+---------------------------------------------------------+
| Parameter    | Format  | Default Value    | Description                                             |
+==============+=========+==================+=========================================================+
| First frame  | int     | 0                | The frame from which the analysis will begin, the       |
|              |         |                  | first frame taken into account.                         |
+--------------+---------+------------------+---------------------------------------------------------+
| Last frame   | int     | Last frame       | The frame until which the analysis proceeds. The last   |
|              |         |                  | frame taken into account.                               |
+--------------+---------+------------------+---------------------------------------------------------+
| Frame step   | int     | 1                | Determines the periodicity of which steps are used      |
|              |         |                  | and which are skipped. 1 means that all frames are      |
|              |         |                  | read, 2 means every other is read, etc.                 |
+--------------+---------+------------------+---------------------------------------------------------+
| Correlation  | int     | Last frame / 2   | Determines the size of the correlation window (in       |
| frames       |         |                  | frames). This determines the time range of the output   |
|              |         |                  | of the analysis. See also :ref:`correlation-frames`.      |
+--------------+---------+------------------+---------------------------------------------------------+

.. _param-qshells:

Q shells
~~~~~~~~

+--------------+---------+---------+--------------------------------------------------------+
| Input        | Format  | Default | Description                                            |
+==============+=========+=========+========================================================+
| from         | float   | 0       | The lowest value of :math:`|Q|` to be used in Q-vector |
|              |         |         | generation.                                            |
+--------------+---------+---------+--------------------------------------------------------+
| to           | float   | 10      | The highest value of :math:`|Q|` to be used in Q-vector|
|              |         |         | generation.                                            |
+--------------+---------+---------+--------------------------------------------------------+
| by step of   | float   | 1       | The step by which :math:`|Q|` is incremented when      |
|              |         |         | changing from one Q-shell to the next one. Please      |
|              |         |         | adjust the *width* input parameter accordingly when    |
|              |         |         | changing the step.                                     |
+--------------+---------+---------+--------------------------------------------------------+

The *unit* of the Q-vector length in MDANSE is :math:`\text{nm}^{-1}`.
.. _param-output-files:

Output trajectory
~~~~~~~~~~~~~~~~~

This is used in every converter, and a few analysis jobs that also output 
a trajectory (:ref:`analysis-reference-CenterOfMassesTrajectory`,
:ref:`analysis-reference-TrajectoryEditor`).

+--------------+---------+---------+--------------------------------------------------------+
| Input        | Format  | Default | Description                                            |
+==============+=========+=========+========================================================+
| filename     | str     |         | The full path to the new file that will be created by  |
|              |         |         | this run.                                              |
+--------------+---------+---------+--------------------------------------------------------+
| precision    | int     | 64      | Number of bits used for writing out floating point     |
|              |         |         | numbers. 64, 32 and 16 are possible                    |
+--------------+---------+---------+--------------------------------------------------------+
| chunk size   | int     | 128     | Number of atoms to be included in a single chunk of    |
|              |         |         | the HDF5 datasets in the output trajectory.            |
|              |         |         | An entire chunk must be loaded to access any number    |
|              |         |         | in that chunk. Smaller number means faster analysis,   |
|              |         |         | but also larger files. There rarely any advantage to   |
|              |         |         | chunks smaller than 128.                               |
+--------------+---------+---------+--------------------------------------------------------+
| compression  | str     | gzip    | Can be 'none', 'gzip' or 'lzf'. 'none' means no        |
|              |         |         | compression. For most trajectories, compressing the    |
|              |         |         | atom coordinate arrays visibly reduces the file size   |
|              |         |         | at an expense of only a minor slowing down.            |
+--------------+---------+---------+--------------------------------------------------------+
| log level    | str     | no logs | Can be "no logs", "DEBUG", "INFO", "WARN", "ERROR" or  |
|              |         |         | "CRITICAL". Not relevant to the output trajectory      |
|              |         |         | itself, but will change the amount of output in the    |
|              |         |         | log file of the converter run.                         |
+--------------+---------+---------+--------------------------------------------------------+


.. _param-output-files:

Output files
~~~~~~~~~~~~

Most analysis types define their output file using this.

+--------------+-----------+-----------+--------------------------------------------------------+
| Input        | Format    | Default   | Description                                            |
+==============+===========+===========+========================================================+
| filename     | str       |           | The full path to the new file that will be created by  |
|              |           |           | this run. Since multiple formats can be selected, it   |
|              |           |           | can be used as the base name to which different exten- |
|              |           |           | sions will be appended for different output formats.   |
+--------------+-----------+-----------+--------------------------------------------------------+
| format       | list[str] | MDAFormat | Can be ["MDAFormat"], ["TextFormat"] or both can be    |
|              |           |           | used with ["MDAFormat", "TextFormat"]. MDA format is   |
|              |           |           | the only format used by the MDANSE_GUI.                |
+--------------+-----------+-----------+--------------------------------------------------------+
| log level    | str       | no logs   | Can be "no logs", "DEBUG", "INFO", "WARN", "ERROR" or  |
|              |           |           | "CRITICAL". Not relevant to the output trajectory      |
|              |           |           | itself, but will change the amount of output in the    |
|              |           |           | log file of the converter run.                         |
+--------------+-----------+-----------+--------------------------------------------------------+

Atom Selection
^^^^^^^^^^^^^^

Atom Selection allows you to select any set of atoms and/or other
particles. These selected particles are then the ones that are made the
target of the analysis. There is no limit to which particles can be
included in a selection, or to how many selections can be used
simultaneously. There can even be none; Atom Selection is entirely
optional.

More information about atom selection can be found here: :ref:`atom-selection`.

.. _param-atom-transmutation:

Atom Transmutation
^^^^^^^^^^^^^^^^^^

Atom transmutation uses the same interface as atom selection.
Once you have selected the atoms you wanted to transmute,
you can choose what chemical elements to replace them with,
and add this change to the total transmutation mapping. 

.. _param-atom-charges:

Atom Charges
^^^^^^^^^^^^

The partial charge setting uses the same interface as the atom selection.
You will most likely need to create several selections one after another.
Every time you have selected atoms which should have the same charge assigned,
set their charge and reset the selection. Once all the charges have been set,
confirm the changes by clicking "Use setting".

.. _param-q-vectors:

Q vectors
~~~~~~~~~

Q vectors can be created using several generators. The generators use
different input parameters. The details are given here.

Spherical Lattice Vectors
^^^^^^^^^^^^^^^^^^^^^^^^^

+------------------+-----------+---------+------------------------------------------------------------+
| Parameter        | Format    | Default | Description                                                |
+==================+===========+=========+============================================================+
| seed             | int       | 0       | RNG seed used to generate the vectors. Setting the same    |
|                  |           |         | seed ensures reproducibility of random numbers.            |
+------------------+-----------+---------+------------------------------------------------------------+
| n vectors        | int       | 50      | Number of hkl vectors in each shell. Higher values result  |
| (Number of hkl   |           |         | in higher accuracy but longer computation time.            |
| vectors)         |           |         |                                                            |
+------------------+-----------+---------+------------------------------------------------------------+
| width            | float     | 1.0     | Accepted tolerance of each shell. Often identical to the   |
|                  |           |         | "by step of" parameter.                                    |
+------------------+-----------+---------+------------------------------------------------------------+
| Generate button  |           |         | Generates hkl vectors based on the specified parameters    |
|                  |           |         | (seed, n vectors, width). Must be clicked before saving.   |
+------------------+-----------+---------+------------------------------------------------------------+
| Name             | str       | None    | Allows you to name the generated vectors. Name must be     |
|                  |           |         | set before saving the vectors.                             |
+------------------+-----------+---------+------------------------------------------------------------+
| Save button      |           |         | Saves the generated vectors. It doesn't close the Q        |
|                  |           |         | Vectors window. Saved vectors may be in a specific format. |    
+------------------+-----------+---------+------------------------------------------------------------+


Circular Lattice Vectors
^^^^^^^^^^^^^^^^^^^^^^^^

+------------------+-----------+---------+------------------------------------------------------------+
| Parameter        | Format    | Default | Description                                                |
+==================+===========+=========+============================================================+
| seed             | int       | 0       | The RNG seed used to generate the vectors. Setting the same|
|                  |           |         | seed ensures reproducibility of random numbers.            |
+------------------+-----------+---------+------------------------------------------------------------+
| n vectors        | int       | 50      | Number of hkl vectors in each shell. Higher values result  |
|                  |           |         | in higher accuracy but at the cost of longer computational |
|                  |           |         | time.                                                      |
+------------------+-----------+---------+------------------------------------------------------------+
| width            | float     | 1.0     | Accepted tolerance of each shell. Often identical to the   |
|                  |           |         | "by step of" parameter.                                    |
+------------------+-----------+---------+------------------------------------------------------------+
| Generate button  |           |         | Generates hkl vectors based on the specified parameters    |
|                  |           |         | (seed, n vectors, width). Must be clicked before saving.   |
+------------------+-----------+---------+------------------------------------------------------------+
| Name             | str       | None    | Allows you to name the generated vectors. Name must be     |
|                  |           |         | set before saving the vectors.                             |
+------------------+-----------+---------+------------------------------------------------------------+
| Save button      |           |         | Saves the generated vectors. It doesn't close the Q        |
|                  |           |         | Vectors window. Saved vectors may be in a specific format. |    
+------------------+-----------+---------+------------------------------------------------------------+

-  axis 1

   +--------------+-----------+---------+-----------------------+
   | Component    | Format    | Default | Description           |
   +==============+===========+=========+=======================+
   | x-component  | int       | 1       | X-component for plane |
   +--------------+-----------+---------+-----------------------+
   | y-component  | int       | 0       | Y-component for plane |
   +--------------+-----------+---------+-----------------------+
   | z-component  | int       | 0       | Z-component for plane |
   +--------------+-----------+---------+-----------------------+

-  axis 2

   +--------------+-----------+---------+-----------------------+
   | Component    | Format    | Default | Description           |
   +==============+===========+=========+=======================+
   | x-component  | int       | 0       | X-component for plane |
   +--------------+-----------+---------+-----------------------+
   | y-component  | int       | 1       | Y-component for plane |
   +--------------+-----------+---------+-----------------------+
   | z-component  | int       | 0       | Z-component for plane |
   +--------------+-----------+---------+-----------------------+



Linear Lattice Vectors
^^^^^^^^^^^^^^^^^^^^^^

+------------------+-----------+---------+------------------------------------------------------------+
| Parameter        | Format    | Default | Description                                                |
+==================+===========+=========+============================================================+
| seed             | int       | 0       | The RNG seed used to generate the vectors. Setting the same|
|                  |           |         | seed ensures reproducibility of random numbers.            |
+------------------+-----------+---------+------------------------------------------------------------+
| n vectors        | int       | 50      | Number of hkl vectors in each shell. Higher values result  |
|                  |           |         | in higher accuracy but at the cost of longer computational |
|                  |           |         | time.                                                      |
+------------------+-----------+---------+------------------------------------------------------------+
| width            | float     | 1.0     | Accepted tolerance of each shell. Often identical to the   |
|                  |           |         | "by step of" parameter.                                    |
+------------------+-----------+---------+------------------------------------------------------------+
| axis             |           |         |                                                            |
+------------------+-----------+---------+------------------------------------------------------------+
|   x-component   | int       | 1       | The x-components of the specified axis.                     |
+------------------+-----------+---------+------------------------------------------------------------+
|   y-component   | int       | 0       | The y-components of the specified axis.                     |
+------------------+-----------+---------+------------------------------------------------------------+
|   z-component   | int       | 0       | The z-components of the specified axis.                     |
+------------------+-----------+---------+------------------------------------------------------------+
| Generate button  |           |         | Generates hkl vectors based on the specified parameters    |
|                  |           |         | (seed, n vectors, width). Must be clicked before saving.   |
+------------------+-----------+---------+------------------------------------------------------------+
| Name             | str       | None    | This is the empty box at the bottom of the window. It      |
|                  |           |         | allows you to name the generated vectors. This must be     |
|                  |           |         | set before saving the vectors.                             |
+------------------+-----------+---------+------------------------------------------------------------+
| Save button      |           |         | Saves the generated vectors. It doesn't close the Q        |
|                  |           |         | Vectors window. Saved vectors may be in a specific format. |    
+------------------+-----------+---------+------------------------------------------------------------+


Miller Indices Lattice Vectors
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

+-----------------+-----------+---------+------------------------------------------------------------+
| Parameter       | Format    | Default | Description                                                |
+=================+===========+=========+============================================================+
| seed            | int       | 0       | The RNG seed used to generate the vectors. Setting the same|
|                 |           |         | seed ensures reproducibility of random numbers.            |
+-----------------+-----------+---------+------------------------------------------------------------+
| width           | float     | 1.0     | Accepted tolerance of each shell. Often identical to the   |
|                 |           |         | "by step of" parameter.                                    |
+-----------------+-----------+---------+------------------------------------------------------------+


-  h (and the same goes for k and l fields)

+-----------------+-----------+---------+------------------------------------------------------------+
| Parameter       | Format    | Default | Description                                                |
+=================+===========+=========+============================================================+
|   from          | int       | 0       | Minimum value used to construct the range of h vectors.    |
+-----------------+-----------+---------+------------------------------------------------------------+
|   to            | int       | 0       | Maximum value used to construct the range of h vectors.    |
+-----------------+-----------+---------+------------------------------------------------------------+
|   by step of    | int       | 1       | Step used to construct the range of h vectors. If it is    |
|                 |           |         | 1, every integer between **from** and **to** is placed     |
|                 |           |         | into the range; if it is 2, every other, etc.              |
+-----------------+-----------+---------+------------------------------------------------------------+
| Generate button |           |         | Generates hkl vectors based on the specified parameters    |
|                 |           |         | (h ranges). Must be clicked before saving.                 |
+-----------------+-----------+---------+------------------------------------------------------------+
| Name            | str       | None    | This is the empty box at the bottom of the window. It      |
|                 |           |         | allows you to name the generated vectors. This must be     |
|                 |           |         | set before saving the vectors.                             |
+-----------------+-----------+---------+------------------------------------------------------------+
| Save button     |           |         | Saves the generated vectors. It doesn't close the Q      |
|                 |           |         | Vectors window. Saved vectors may be in a specific format.|    
+-----------------+-----------+---------+------------------------------------------------------------+


Spherical Vectors
^^^^^^^^^^^^^^^^^
+-----------------+-----------+---------+------------------------------------------------------------+
| Parameter       | Format    | Default | Description                                                |
+=================+===========+=========+============================================================+
| seed            | int       | 0       | The RNG seed used to generate the vectors. Setting the same|
|                 |           |         | seed ensures reproducibility of random numbers.            |
+-----------------+-----------+---------+------------------------------------------------------------+
| n vectors       | int       | 50      | The number of hkl vectors in each shell. Higher values     |
|                 |           |         | result in higher accuracy but longer computational time.   |
+-----------------+-----------+---------+------------------------------------------------------------+
| width           | float     | 1.0     | The accepted tolerance of each shell. Often identical to   |
|                 |           |         | the "by step of" parameter.                                |
+-----------------+-----------+---------+------------------------------------------------------------+
| Generate button |           |         | Generates hkl vectors based on the specified parameters    |
|                 |           |         | (seed, n vectors, width). Must be clicked before saving.   |
+-----------------+-----------+---------+------------------------------------------------------------+
| Name            | str       | None    | This is the empty box at the bottom of the window. It      |
|                 |           |         | allows you to name the generated vectors before saving.    |
+-----------------+-----------+---------+------------------------------------------------------------+
| Save button     |           |         | Saves the generated vectors. It doesn't close the Q        |
|                 |           |         | Vectors window.                                            |
+-----------------+-----------+---------+------------------------------------------------------------+


Circular Vectors
^^^^^^^^^^^^^^^^

+-----------------+-----------+---------+--------------------------------------------------------+
| Parameter       | Format    | Default | Description                                            |
+=================+===========+=========+========================================================+
| seed            | int       | 0       | The RNG seed used to generate the vectors. Setting the |
|                 |           |         | same seed ensures that the same random numbers are     |
|                 |           |         | generated, making the calculation reproducible.        |
+-----------------+-----------+---------+--------------------------------------------------------+
| n vectors       | int       | 50      | The number of hkl vectors in each shell. Increasing    |
|                 |           |         | this value improves accuracy but also increases        |
|                 |           |         | computational time.                                    |
+-----------------+-----------+---------+--------------------------------------------------------+
| width           | float     | 1.0     | The accepted tolerance of each shell. It often matches |
|                 |           |         | the "by step of" parameter.                            |
+-----------------+-----------+---------+--------------------------------------------------------+
| axis 1          |           |         | Axis 1 parameters:                                     |
|                 |           |         |   - x-component: int, default 1                        |
|                 |           |         |     The x-component of the first axis used to specify  |
|                 |           |         |     the plane.                                         |
|                 |           |         |   - y-component: int, default 0                        |
|                 |           |         |     The y-component of the first axis used to specify  |
|                 |           |         |     the plane.                                         |
|                 |           |         |   - z-component: int, default 0                        |
|                 |           |         |     The z-component of the first axis used to specify  |
|                 |           |         |     the plane.                                         |
+-----------------+-----------+---------+--------------------------------------------------------+
| axis 2          |           |         | Axis 2 parameters:                                     |
|                 |           |         |   - x-component: int, default 0*                       |
|                 |           |         |     The x-component of the second axis used to         |
|                 |           |         |     specify the plane.                                 |
|                 |           |         |   - y-component: int, default 1                        |
|                 |           |         |     The y-component of the second axis used to         |
|                 |           |         |     specify the plane.                                 |
|                 |           |         |   - z-component: int, default 0                        |
|                 |           |         |     The z-component of the second axis used to         |
|                 |           |         |     specify the plane.                                 |
+-----------------+-----------+---------+--------------------------------------------------------+
| Generate button |           |         | Generates hkl vectors based on the specified           |
|                 |           |         | parameters (seed, n vectors, width, axis components).  |
|                 |           |         | Must be clicked before saving.                         |
+-----------------+-----------+---------+--------------------------------------------------------+
| Name            | str       | None    | This is the empty box at the bottom of the window.     |
|                 |           |         | It allows you to name the generated vectors before     |
|                 |           |         | saving. Must be set before saving.                     |
+-----------------+-----------+---------+--------------------------------------------------------+
| Save button     |           |         | Saves the generated vectors. It does not close the Q   |
|                 |           |         | Vectors window. The saved vectors may be in a          |
|                 |           |         | specific format, such as a table format.               |
+-----------------+-----------+---------+--------------------------------------------------------+


Linear Vectors
^^^^^^^^^^^^^^

+-----------------+-----------+---------+-------------------------------------------------------+
| Parameter       | Format    | Default | Description                                           |
+=================+===========+=========+=======================================================+
| seed            | int       | 0       | The RNG seed used to generate the vectors. Setting    |
|                 |           |         | the same seed ensures that the same random numbers    |
|                 |           |         | are generated, making the calculation more            |
|                 |           |         | reproducible.                                         |
+-----------------+-----------+---------+-------------------------------------------------------+
| n vectors       | int       | 50      | The number of hkl vectors in each shell. Higher       |
|                 |           |         | values result in higher accuracy but longer           |
|                 |           |         | computational time.                                   |
+-----------------+-----------+---------+-------------------------------------------------------+
| width           | float     | 1.0     | The accepted tolerance of each shell. It is often     |
|                 |           |         | identical to the "by step of" parameter.              |
+-----------------+-----------+---------+-------------------------------------------------------+
| axis            |           |         | Axis parameters:                                      |
|                 |           |         |   - x-component: int, default 1                       |
|                 |           |         |     The x-component of the specified axis.            |
|                 |           |         |   - y-component: int, default 0                       |
|                 |           |         |     The y-component of the specified axis.            |
|                 |           |         |   - z-component: int, default 0                       |
|                 |           |         |     The z-component of the specified axis.            |
+-----------------+-----------+---------+-------------------------------------------------------+
| Generate button |           |         | Generates hkl vectors based on the specified          |
|                 |           |         | parameters (seed, n vectors, width, axis              |
|                 |           |         | components). Must be clicked before saving.           |
+-----------------+-----------+---------+-------------------------------------------------------+
| Name            | str       | None    | This is the empty box at the bottom of the window.    |
|                 |           |         | It allows you to name the generated vectors before    |
|                 |           |         | saving. Must be set before saving.                    |
+-----------------+-----------+---------+-------------------------------------------------------+
| Save button     |           |         | Saves the generated vectors. It does not close the    |
|                 |           |         | Q Vectors window.                                     |
+-----------------+-----------+---------+-------------------------------------------------------+


Grid Vectors
^^^^^^^^^^^^

+-----------------+-----------+---------+---------------------------------------------------------------+
| Parameter       | Format    | Default | Description                                                   |
+=================+===========+=========+===============================================================+
| seed            | int       | 0       | The RNG seed used to generate the vectors. Setting the same   |
|                 |           |         | seed ensures that the same random numbers are generated,      |
|                 |           |         | making the calculation more reproducible.                     |
+-----------------+-----------+---------+---------------------------------------------------------------+
| hrange (krange  |           |         | Range parameters for h, k, and l vectors:                     |
| , lrange fields)|           |         |   - from: int, default 0                                      |
|                 |           |         |     The minimum value used to construct the range of h        |
|                 |           |         |     vectors.                                                  |
|                 |           |         |   - to: int, default 0                                        |
|                 |           |         |     The maximum value used to construct the range of h        |
|                 |           |         |     vectors.                                                  |
|                 |           |         |   - by step of: int, default 1                                |
|                 |           |         |     The step used to construct the range of h vectors. If it  |
|                 |           |         |     is 1, every integer between **from** and **to** is        |
|                 |           |         |     placed into the range; if it is 2, every other, etc.      |
+-----------------+-----------+---------+---------------------------------------------------------------+
| qstep           | float     | 0.01    | Determines how the hkl vectors are grouped.                   |
+-----------------+-----------+---------+---------------------------------------------------------------+
| Generate button |           |         | Generates hkl vectors based on the specified parameters       |
|                 |           |         | (seed, hrange, krange, lrange, qstep). Must be clicked        |
|                 |           |         | before saving.                                                |
+-----------------+-----------+---------+---------------------------------------------------------------+
| Name            | str       | None    | This is the empty box at the bottom of the window. It         |
|                 |           |         | allows you to name the generated vectors before saving.       |
|                 |           |         | Must be set before saving.                                    |
+-----------------+-----------+---------+---------------------------------------------------------------+
| Save button     |           |         | Saves the generated vectors. It does not close the Q          |
|                 |           |         | Vectors window. Saved vectors may be in a specific format.    |
+-----------------+-----------+---------+---------------------------------------------------------------+


Approximated Dispersion Vectors
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
+-----------------+-----------+----------------------+------------------------------------------------------------+
| Parameter       | Format    | Default              | Description                                                |
+=================+===========+======================+============================================================+
| generator       | drop-down | circular_lattice     | The selection of which type of Q Vectors is being          |
|                 |           |                      | defined.                                                   |
+-----------------+-----------+----------------------+------------------------------------------------------------+
| Q start (nm^-1) |           |                      | Q start parameters for the first and second Q points:      |
|                 |           |                      |   - x-component: int, default 1                            |
|                 |           |                      |     The x-component of this Q point.                       |
|                 |           |                      |   - y-component: int, default 0                            |
|                 |           |                      |     The y-component of this Q point.                       |
|                 |           |                      |   - z-component: int, default 0                            |
|                 |           |                      |     The z-component of this Q point.                       |
+-----------------+-----------+----------------------+------------------------------------------------------------+
| Q step (nm^-1)  | float     | 0.1                  | The increment by which Q is increased when tracing the     |
|                 |           |                      | line between the two points.                               |
+-----------------+-----------+----------------------+------------------------------------------------------------+
| Generate button |           |                      | Generates hkl vectors based on the specified parameters    |
|                 |           |                      | (generator, Q start, Q step). Must be clicked before       |
|                 |           |                      | saving.                                                    |
+-----------------+-----------+----------------------+------------------------------------------------------------+
| Name            | str       | None                 | This is the empty box at the bottom of the window. It      |
|                 |           |                      | allows you to name the generated vectors before saving.    |
|                 |           |                      | Must be set before saving.                                 |
+-----------------+-----------+----------------------+------------------------------------------------------------+
| Save button     |           |                      | Saves the generated vectors. It does not close the Q       |
|                 |           |                      | Vectors window. Saved vectors may be in a specific format. |    
+-----------------+-----------+----------------------+------------------------------------------------------------+

.. _param-instrument-resolution:

Instrument resolution
~~~~~~~~~~~~~~~~~~~~~

This option is available in all the analyses performing a time Fourier
Transform, e.g. for the calculation of the density of states or the
dynamic structure factor. The following resolution shapes are supported
in MDANSE at the moment:

- Gaussian

  :code:`('gaussian', {'mu': 0.0, 'sigma': 1.0})`

- Lorentzian

  :code:`('lorentzian', {'mu': 0.0, 'sigma': 1.0})`

- Pseudo-Voigt

  The corresponding MDANSE input is:

  :code:`('pseudo-voigt', {'eta': 0.5, 'mu_lorentzian': 0.0, 'sigma_lorentzian': 1.0, 'mu_gaussian': 0.0, 'sigma_gaussian': 1.0})`

- square

  The corresponding MDANSE input is:

  :code:`('square', {'mu': 0.0, 'sigma': 1.0})`

- triangular

  The corresponding MDANSE input is:

  :code:`('triangular', {'mu': 0.0, 'sigma': 1.0})`

- ideal
  The corresponding MDANSE input is:

  :code:`('ideal', {})`
