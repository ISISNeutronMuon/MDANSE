
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
|              |         |                  | of the analysis. See also :ref:`correlation-frames`.    |
+--------------+---------+------------------+---------------------------------------------------------+

.. _param-qshells:

Q shells
~~~~~~~~

+--------------+---------+---------+--------------------------------------------------------+
| Input        | Format  | Default | Description                                            |
+==============+=========+=========+========================================================+
| from         | float   | 0       | The lowest value of :math:`q` to be used in            |
|              |         |         | :math:`\mathbf{q}`-vector generation.                  |
+--------------+---------+---------+--------------------------------------------------------+
| to           | float   | 10      | The highest value of :math:`q` to be used in           |
|              |         |         | :math:`\mathbf{q}`-vector generation.                  |
+--------------+---------+---------+--------------------------------------------------------+
| by step of   | float   | 1       | The step by which :math:`q` is incremented when        |
|              |         |         | changing from one :math:`\mathbf{q}`-shell to the      |
|              |         |         | next one. Please adjust the *width* input parameter    |
|              |         |         | accordingly when changing the step.                    |
+--------------+---------+---------+--------------------------------------------------------+

The *unit* of the :math:`\mathbf{q}`-vector length in MDANSE is :math:`\text{nm}^{-1}`.

.. _param-output-trajectory:

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
simultaneously. Atom Selection is entirely optional; if it is omitted,
all the particles in the simulation are used.

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

q-vectors
~~~~~~~~~

:math:`\mathbf{q}`-vectors can be created using several generators, which
sample the reciprocal space in different ways. Specific generators are described
in :ref:`vector-generator-list`.

For vector generators requiring "shells" and "width" input, the "shell" input defines
a range of bin centres, and "width" gives the bin width used for assigning vectors to shells.
For example, shells = (4.0, 8.0, 2.0) will generate 3 bins, centred on 4.0, 6.0 and 8.0
:math:`\text{nm}^{-1}`. The bins will contain vectors with :math:`q` in the ranges of
3.5-4.5, 5.5-6.5 and 7.5-8.5, respectively. That is, for each bin the range of accepted
:math:`q` is
:math:`(\text{centre}-0.5*\text{width},\, \text{centre}+0.5*\text{width})`.

Vector generators with "Lattice" in their name generate vectors commensurate with the
reciprocal lattice of the simulation box. This is important for analysis types which
calculate correlations of pairs of atoms (:ref:`current-correlation-function`
and :ref:`dynamic-coherent-structure-factor`).

While :ref:`dynamic-incoherent-structure-factor` does not require a Lattice vector
generator, it is still necessary to use one if you intend to combine the coherent
and incoherent parts into the total signal using
:ref:`neutron-dynamic-total-structure-factor`.

Lattice vector generators initially generate a random distribution of vectors
allowing also fractional coordinates, then round them to the nearest full lattice
vector. Typically, there will be multiple vectors corresponding to a single lattice vector.
The number of the initial vectors that ended up rounded to the same value is used as
a weight factor, increasing the contribution of the vectors that were more frequently
sampled. This should improve the results for low-symmetry unit cells, where lattice vectors
are not uniformly distributed. Also, this
means that the number of generated vectors can be increased significantly for
lattice vector generators. The calculation will only be performed for the unique vectors,
so once all the possible vectors in a shell have been generated, increasing the number
of vectors further will improve the accuracy of the weight
factors without increasing the computational effort.

In the MDANSE GUI it is possible to preview the number and distribution of generated
vectors before running the analysis. 

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
