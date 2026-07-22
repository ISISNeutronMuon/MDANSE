
.. |modq| replace:: :math:`|\mathbf{q}|`
.. |q| replace:: :math:`\mathbf{q}`

.. _qvector-generation:

q-Vector Generation
~~~~~~~~~~~~~~~~~~~

A complete list of q-vector generators can be found in :ref:`vector-generator-list`.
However, please keep in mind that for the typical neutron scattering calculations
it is necessary to choose a lattice vector generator to get correct results of
for the spatial correlations between pairs of atoms (as in e.g. Dynamic Coherent
Structure Factor), and a spherical vector generator to simulate the random orientation
of the simulated objects in respect to the beam. This means that the
:ref:`qvectors-reference-SphericalLatticeQVectors` generator should be the best
choice for most users, unless you are simulating a highly ordered sample with a
well known orientation (e.g. a single crystal). Typically, higher levels of order
impose more restrictions on the generated q vectors. :ref:`qvectors-reference-LinearQVectors` can be
used for planar (i.e. 2D order) systems, and :ref:`qvectors-reference-CircularQVectors`
for nematic or axially aligned systems (i.e. 1D order).

For properties such as :ref:`analysis-reference-DynamicIncoherentStructureFactor` there is
no restriction on which vectors can be used in the calculations. In principle,
:ref:`qvectors-reference-SphericalQVectors` generator *could* be used in this case.
However, the matching :ref:`analysis-reference-DynamicCoherentStructureFactor` calculation
imposes the additional requirement of only lattice vectors being used in the calculation.
In order to be able to combine the results of the two calculations into the 
total dynamic structure factor (e.g. using the :ref:`analysis-reference-NeutronDynamicTotalStructureFactor`
analysis), lattice vectors should be used for both parts of the calculation.


Reciprocal Lattice q-Vectors
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Let :math:`\mathbf{a}`, :math:`\mathbf{b}`, :math:`\mathbf{c}` be the basis vectors
which span the MD cell. Any position vector in the MD cell can be
written as

.. math::
   :label: qvector1

   {{\mathbf{r} = x'}{\mathbf{a} + y'}{\mathbf{b} + z'}\mathbf{c}}

so that it defines the position vector in the MD cell.
With :math:`x'`, :math:`y'`, :math:`z'` having
values between :math:`0` and :math:`1` if :math:`\mathbf{r}` is in the unit cell.
The primes indicate that the coordinates are fractional coordinates. A jump due
to periodic boundary conditions can cause :math:`x'`, :math:`y'`,
:math:`z'` to jump by :math:`\pm1`. The set of dual basis
vectors :math:`\mathbf{a}^*`, :math:`\mathbf{b}^*`, :math:`\mathbf{c}^*`
where

.. math::
   :label: qvector2

   \mathbf{a}^* = \frac{2 \pi}{V} \mathbf{b} \times \mathbf{c}, \qquad \mathbf{b}^* = \frac{2 \pi}{V} \mathbf{c} \times \mathbf{a}, \qquad \mathbf{c}^* = \frac{2 \pi}{V} \mathbf{a} \times \mathbf{b}.

If the |q|-vectors are now chosen as

.. math::
   :label: qvector3

   \mathbf{q} =  h\mathbf{a}^* + k\mathbf{b}^* + l\mathbf{c}^*

so that this selection of |q|-vectors produces phase changes for
handling jumps in particle trajectories. Here :math:`h`, :math:`k`, and :math:`l`
are integers, jumps in the particle trajectories
produce phase changes of multiples of :math:`2\pi` in the Fourier transformed
particle density, i.e. leave it unchanged.


Random sampling of reciprocal space
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The current implementation of the lattice vector generators 
:ref:`qvectors-reference-SphericalLatticeQVectors`,
:ref:`qvectors-reference-CircularLatticeQVectors` and
:ref:`qvectors-reference-LinearLatticeQVectors` assumes
that different vectors can have different weights. This
is meant to approximate a spherical distribution of vectors
in low-symmetry systems where lattice vectors are not uniformly
spaced, and also to give preference to vectors with |modq|
close to the nominal value for a specific shell. This behaviour
is different from MDANSE 1.5, where the shell population was
deterministic for shells containing less lattice vectors than
the requested number, and stochastic with binary (0 or 1) weights
for other shells.

If you prefer to revert to the original weights scheme of MDANSE 1.5,
you can set the variable :code:`force_equal_weights=True` for these
vector generators. You can also save the value of this variable in your
instrument profiles, so it is set to :code:`True` every time you set
the vector parameters using these profiles.

If you use the currently recommended setting of :code:`force_equal_weights=False`,
the lattice vector generator will randomly create :code:`n_vectors` vectors
commensurate with the reciprocal lattice defined by the simulation box.
It will then generate :code:`n_samples` reciprocal space points within
the same vector shell. Each random point will contribute to the weight
of the lattice vector which is the nearest. As a result, the lattice vectors
in the areas of reciprocal space containing many lattice vectors close to
each other will contribute less to the calculation results than the vectors
from the reciprocal space regions containing few lattice vectors. This is meant
to produce a better approximation of spherical sampling with a uniform distribution
of angles. Additionally, the random points used for sampling follow a normal distribution
in |q|, assigning a larger weight to the vectors close to the
nominal |q| value of the shell.

The MDANSE GUI offers a preview dialog, visualising the vector distribution that
should be created based on the input parameters. Additionally, the same
detailed information about the vectors that have been generated
and used in the calculation is written into a separate data group or file,
depending on the format used. In the case of .mda files, a data group
called :code:`/vector_generator` is written into the file. Information about
viewing the vector information can be found in the plotting documentation,
section :ref:`plotting-vectors`.

