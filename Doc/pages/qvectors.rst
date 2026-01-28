
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
well known orientation (e.g. a single crystal).

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

If the :math:`\mathbf{q}`-vectors are now chosen as

.. math::
   :label: qvector3

   \mathbf{q} =  h\mathbf{a}^* + k\mathbf{b}^* + l\mathbf{c}^*

so that this selection of :math:`\mathbf{q}`-vectors produces phase changes for
handling jumps in particle trajectories. Here :math:`h`, :math:`k`, and :math:`l`
are integers, jumps in the particle trajectories
produce phase changes of multiples of :math:`2\pi` in the Fourier transformed
particle density, i.e. leave it unchanged.
