.. _vector-generator-list:

List of q-vector generators
===========================


.. _qvectors-reference-CircularLatticeQVectors:

CircularLatticeQVectors
~~~~~~~~~~~~~~~~~~~~~~~

Generates Q vectors on a plane perpendicular to the 'axis' vector.

Vectors are grouped into shells limited to the range of
(q - width/2, q + width/2) around the shell centre q.

Only vectors commensurate with the reciprocal space lattice will be generated.
If more lattice vectors than requested are available in the requested range
for a shell, a subset of the vectors will be selected with the probability
given as a Gaussian function with FWHM of width/2 and centred on the :math:`|q|`
which is the nominal centre of the shell.

:math:`|Q|` values for which no valid vectors can be found are omitted in the output.

Inputs:

- seed: :ref:`configurator-analysis-IntegerConfigurator` default=0
- shells: :ref:`configurator-analysis-RangeConfigurator` default=(0.0, 5.0, 1.0)
- n_samples: :ref:`configurator-analysis-IntegerConfigurator` default=50000
- n_vectors: :ref:`configurator-analysis-IntegerConfigurator` default=100
- width: :ref:`configurator-analysis-FloatConfigurator` default=1.0
- force_equal_weights: :ref:`configurator-analysis-BooleanConfigurator` default=False
- axis: :ref:`configurator-analysis-VectorConfigurator` default=[0, 0, 1]


.. _qvectors-reference-CircularQVectors:

CircularQVectors
~~~~~~~~~~~~~~~~

Generates Q vectors as concentric circles on a plane.

Vectors will be generated as shells of vectors of similar lengths
and random orientations on a plane perpendicular to the 'axis' vector.

The vector lengths in a single shell assume a normal distribution with the
FWHM of 'width'/2 and limited to the range of (q - width/2, q + width/2)
around the shell centre defined by the 'shells' input.

Inputs:

- seed: :ref:`configurator-analysis-IntegerConfigurator` default=0
- shells: :ref:`configurator-analysis-RangeConfigurator` default=(0.0, 5.0, 1.0)
- n_vectors: :ref:`configurator-analysis-IntegerConfigurator` default=50
- width: :ref:`configurator-analysis-FloatConfigurator` default=1.0
- axis: :ref:`configurator-analysis-VectorConfigurator` default=[0, 0, 1]


.. _qvectors-reference-DispersionLatticeQVectors:

DispersionLatticeQVectors
~~~~~~~~~~~~~~~~~~~~~~~~~

Generates Q vectors along a line in the HKL units of the simulation box.

The input 'start' and 'step' vectors are expressed as HKL values of the
crystal lattice defined by the simulation box. Every vector will be
generated as :math:`\mathbf{k}_{start} + n\mathbf{k}_{step}` for
integer n from 0 to n_steps.

Inputs:

- start: :ref:`configurator-analysis-VectorConfigurator` default=[0, 0, 0]
- step: :ref:`configurator-analysis-VectorConfigurator` default=[1, 0, 0]
- n_steps: :ref:`configurator-analysis-IntegerConfigurator` default=10


.. _qvectors-reference-DispersionQVectors:

DispersionQVectors
~~~~~~~~~~~~~~~~~~

Generates Q vectors along a path between two points.

As opposed to DispersionLatticeQVectors, the vectors will not
necessarily correspond to integer HKL values.

Inputs:

- q_start: :ref:`configurator-analysis-VectorConfigurator` default=[0, 0, 0]
- q_end: :ref:`configurator-analysis-VectorConfigurator` default=[1, 0, 0]
- q_step: :ref:`configurator-analysis-FloatConfigurator` default=0.1


.. _qvectors-reference-GridQVectors:

GridQVectors
~~~~~~~~~~~~

Generates vectors on a grid.

Vectors are generated from HKL values based on the definition of the unit cell.

As opposed to MillerIndicesQVectors, this generator will use ALL the vectors
in the specified range, assigning each one of them to one of the shells.

The qstep parameter defines the size of the bin used for grouping vectors
into shells based on their length.

Inputs:

- hrange: :ref:`configurator-analysis-RangeConfigurator` default=(0, 8, 1)
- krange: :ref:`configurator-analysis-RangeConfigurator` default=(0, 8, 1)
- lrange: :ref:`configurator-analysis-RangeConfigurator` default=(0, 8, 1)
- q_step: :ref:`configurator-analysis-FloatConfigurator` default=0.2


.. _qvectors-reference-LinearLatticeQVectors:

LinearLatticeQVectors
~~~~~~~~~~~~~~~~~~~~~

Generates vectors randomly on a straight line.

Only vectors commensurate with the reciprocal space lattice will be generated.
If more lattice vectors than requested are available in the requested range
for a shell, a subset of the vectors will be selected with the probability
given as a Gaussian function with FWHM of width/2 and centred on the :math:`|q|`
which is the nominal centre of the shell.

:math:`|Q|` values for which no valid vectors can be found are omitted in the output.
Most calculations will produce one data point per :math:`|Q|` by averaging the results
over all vectors in the group, which is still called a shell.

Inputs:

- seed: :ref:`configurator-analysis-IntegerConfigurator` default=0
- shells: :ref:`configurator-analysis-RangeConfigurator` default=(0.0, 5.0, 1.0)
- n_samples: :ref:`configurator-analysis-IntegerConfigurator` default=50000
- n_vectors: :ref:`configurator-analysis-IntegerConfigurator` default=100
- width: :ref:`configurator-analysis-FloatConfigurator` default=1.0
- force_equal_weights: :ref:`configurator-analysis-BooleanConfigurator` default=False
- axis: :ref:`configurator-analysis-VectorConfigurator` default=[1, 0, 0]


.. _qvectors-reference-LinearQVectors:

LinearQVectors
~~~~~~~~~~~~~~

Generates vectors randomly on a straight line.

Most calculations will produce one data point for :math:`|Q|` by averaging the results
over all vectors in the group, which is still called a shell.

The vector lengths in a single shell assume a normal distribution with the
FWHM of 'width'/2 and limited to the range of (q - width/2, q + width/2)
around the shell centre defined by the 'shells' input.

Inputs:

- seed: :ref:`configurator-analysis-IntegerConfigurator` default=0
- shells: :ref:`configurator-analysis-RangeConfigurator` default=(0.0, 5.0, 1.0)
- n_vectors: :ref:`configurator-analysis-IntegerConfigurator` default=50
- width: :ref:`configurator-analysis-FloatConfigurator` default=1.0
- axis: :ref:`configurator-analysis-VectorConfigurator` default=[1, 0, 0]


.. _qvectors-reference-MillerIndicesQVectors:

MillerIndicesQVectors
~~~~~~~~~~~~~~~~~~~~~

Generates vectors on a grid.

Vectors are generated from HKL values based on
the definition of the unit cell.
They are then grouped into shells based on
their length.

Inputs:

- shells: :ref:`configurator-analysis-RangeConfigurator` default=(0.0, 5.0, 1.0)
- width: :ref:`configurator-analysis-FloatConfigurator` default=1.0
- h: :ref:`configurator-analysis-RangeConfigurator` default=(0, 8, 1)
- k: :ref:`configurator-analysis-RangeConfigurator` default=(0, 8, 1)
- l: :ref:`configurator-analysis-RangeConfigurator` default=(0, 8, 1)


.. _qvectors-reference-SphericalLatticeQVectors:

SphericalLatticeQVectors
~~~~~~~~~~~~~~~~~~~~~~~~

Generates randomly-selected lattice vectors grouped into spheres.

Only vectors commensurate with the reciprocal space lattice will be generated.
If more lattice vectors than requested are available in the requested range
for a shell, a subset of the vectors will be selected with the probability
given as a Gaussian function with FWHM of width/2 and centred on the :math:`|q|`
which is the nominal centre of the shell.

:math:`|Q|` values for which no valid vectors can be found are omitted in the output.
Most calculations will produce one data point per :math:`|Q|` by averaging the results
over all vectors in the shell.

Inputs:

- seed: :ref:`configurator-analysis-IntegerConfigurator` default=0
- shells: :ref:`configurator-analysis-RangeConfigurator` default=(0.0, 5.0, 1.0)
- n_samples: :ref:`configurator-analysis-IntegerConfigurator` default=50000
- n_vectors: :ref:`configurator-analysis-IntegerConfigurator` default=100
- force_equal_weights: :ref:`configurator-analysis-BooleanConfigurator` default=False
- width: :ref:`configurator-analysis-FloatConfigurator` default=1.0


.. _qvectors-reference-SphericalQVectors:

SphericalQVectors
~~~~~~~~~~~~~~~~~

Generates vectors randomly on a sphere.

Most calculations will produce one data point for :math:`|Q|` by averaging the
results over all vectors in the shell.

The vector lengths in a single shell assume a normal distribution with the
FWHM of 'width'/2 and limited to the range of (q - width/2, q + width/2)
around the shell centre defined by the 'shells' input.

Inputs:

- seed: :ref:`configurator-analysis-IntegerConfigurator` default=0
- shells: :ref:`configurator-analysis-RangeConfigurator` default=(0.0, 5.0, 1.0)
- n_vectors: :ref:`configurator-analysis-IntegerConfigurator` default=50
- width: :ref:`configurator-analysis-FloatConfigurator` default=1.0

