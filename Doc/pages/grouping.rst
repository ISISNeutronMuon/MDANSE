
.. _grouping:


Results Grouping
================

Atom Grouping
^^^^^^^^^^^^^

With the default settings, MDANSE will group results by atom type, so that
partial results are summed into datasets, with one dataset per atom type
present in the system. The total result is calculated from these partial
results using the :ref:`weighting-scheme`. Let's
consider a system consisting of a mixture of water and ethanol. With atom grouping,
the partial coherent intermediate scattering
functions are obtained for each unique pair of atoms in the system:
CC, CH, CO, HH, HO, and OO. For example, the C and H partial coherent
intermediate scattering functions is

.. math::
   :label: atompartial1

   F_{\text{coh},\text{CH}}(\mathbf{q},t) =  \frac{1}{N \sqrt{c_{\text{C}}c_{\text{H}}}} \sum\limits_{j \in \text{C}} \sum\limits_{k \in \text{H}} \mathrm{Re}\left[F_{jk}(\mathbf{q},t)\right],

.. math::
   :label: atompartial1_1

   F_{jk}{(\mathbf{q},t) = \left\langle {\exp\left\lbrack {{- i}\mathbf{q}\cdot\mathbf{r}_{j}\left( 0 \right)} \right\rbrack\exp\left\lbrack {i\mathbf{q}\cdot\mathbf{r}_{k}\left( t \right)} \right\rbrack} \right\rangle}

so the summations run over all carbon and hydrogen atoms in the system.
The total is a weighted sum of all partial components

.. math::
   :label: atompartial2

    F_{\text{coh}}(\mathbf{q},t) = W_{\text{CC}} F_{\text{coh}, \text{CC}}(\mathbf{q},t) + W_{\text{CH}} F_{\text{coh}, \text{CH}}(\mathbf{q},t) + \cdots.

Similarly the partial incoherent intermediate
scattering functions are obtained for each unique atom in the system e.g.
C, H, and O. For exmaple, the C partial incoherent
intermediate scattering functions is

.. math::
   :label: atompartial3

   F_{\text{inc},\text{C}}(\mathbf{q},t ) = \frac{1}{Nc_{\text{C}}} \sum\limits_{j \in \text{C}} \mathrm{Re}\left[F_{jj}(\mathbf{q},t)\right]

so the summation run over all carbon atoms and the total is a weight sum
of all partial components

.. math::
   :label: atompartial4

    F_{\text{inc}}(\mathbf{q},t) = W_{\text{C}} F_{\text{inc}, \text{C}}(\mathbf{q},t) + W_{\text{H}} F_{\text{inc}, \text{H}}(\mathbf{q},t) + W_{\text{O}} F_{\text{inc}, \text{O}}(\mathbf{q},t),

see :ref:`weighting-scheme` for further details.

Molecule Grouping
^^^^^^^^^^^^^^^^^

MDANSE can also group results by molecule type, so that they are summed for
all atoms of each type on each type of molecule, again we will consider
a system of water and ethanol. With molecule grouping, the partial
coherent intermediate scattering functions are obtained for each
unique pair of molecules and their atoms types:
[EtOH][EtOH]_CC, [EtOH][EtOH]_CH, [EtOH][H2O]_HO, and etc. Where
[EtOH][H2O]_HO are all pairs of H and O atoms where H are the hydrogen
atoms in ethanol and O are the oxygen atoms in water. The [EtOH][H2O]_HO
partial coherent intermediate scattering function is

.. math::
   :label: moleculepartial1

   F_{\text{coh},\text{HO}}^{[\text{EtOH}][\text{H2O}]}{(\mathbf{q},t) =  \frac{1}{N \sqrt{c_{\text{H}}^{\text{EtOH}}c_{\text{O}}^{\text{H2O}}}}} \sum\limits_{j \in (\text{EtOH}\, \cap\, \text{H})} \sum\limits_{k \in (\text{H2O}\, \cap\, \text{O})} \mathrm{Re}\left[F_{jk}(\mathbf{q},t)\right]

where :math:`c_{\text{H}}^{\text{EtOH}} = N_{\text{H}}^{\text{EtOH}} / N` and
:math:`c_{\text{O}}^{\text{H2O}} = N_{\text{O}}^{\text{H2O}} / N`. Here,
:math:`N_{\text{H}}^{\text{EtOH}}` and :math:`N_{\text{O}}^{\text{H2O}}` are
the total number of atoms of hydrogen in ethanol and oxygen in water respectively,
and :math:`N` is the total number of atom in the system. The molecular
coherent intermediate scattering functions between ethanol and water is
proportional to the weighted sum of the partial terms

.. math::
   :label: moleculepartial2

   \sqrt{c_{\text{EtOH}} c_{\text{H2O}}}F_{\text{coh}}^{[\text{EtOH}][\text{H2O}]}(\mathbf{q},t) =  &W_{\text{CH}}^{[\text{EtOH}][\text{H2O}]} F_{\text{coh},\text{CH}}^{[\text{EtOH}][\text{H2O}]}(\mathbf{q},t) \\\\
    &+ W_{\text{CO}}^{[\text{EtOH}][\text{H2O}]} F_{\text{coh},\text{CO}}^{[\text{EtOH}][\text{H2O}]}(\mathbf{q},t) + \cdots

where :math:`c_{\text{EtOH}} = N_{\text{EtOH}} / N` and
:math:`c_{\text{H2O}} = N_{\text{H2O}} / N`. Here, :math:`N_{\text{EtOH}}`
and :math:`N_{\text{H2O}}` are the total number of atoms in ethanol and
water respectively. For coherent scattering lengths

.. math::
   :label: moleculepartial3

   W_{\text{HO}}^{[\text{EtOH}][\text{H2O}]} = 2\frac{\sqrt{c_{\text{H}}^{\text{EtOH}}c_{\text{O}}^{\text{H2O}}} \ \mathrm{Re} \left[ b_{\mathrm{coh},\text{H}}^{\dagger} b_{\mathrm{coh},\text{O}}\right] }{c_{\text{C}}^{\text{EtOH}}c_{\text{C}}^{\text{EtOH}}  b_{\mathrm{coh},\text{C}}^{\dagger} b_{\mathrm{coh},\text{C}} + \cdots}.

The total coherent intermediate scattering functions
is a weighted sum of all molecular terms

.. math::
   :label: moleculepartial4

   F_{\text{coh}}(\mathbf{q},t) = \sqrt{c_{\text{EtOH}} c_{\text{EtOH}}}F_{\text{coh}}^{[\text{EtOH}][\text{EtOH}]}(\mathbf{q},t) + \sqrt{c_{\text{EtOH}} c_{\text{H2O}}}F_{\text{coh}}^{[\text{EtOH}][\text{H2O}]}(\mathbf{q},t) + \cdots

where the weights are simply the square roots of the product of the
atom concentrations.

Similarly the partial incoherent intermediate
scattering functions are obtained for each molecule and its atom types:
[EtOH]_C, [EtOH]_H, [EtOH]_O, [H2O]_H, and [H2O]_O. For example,
the partial incoherent intermediate scattering functions for ethanol's
carbon atoms is

.. math::
   :label: moleculepartial5

   F_{\text{inc},\text{C}}^{\text{EtOH}}(\mathbf{q},t ) = \frac{1}{Nc_{\text{C}}^{\text{EtOH}}} \sum\limits_{j \in (\text{EtOH}\, \cap \, \text{C})} \mathrm{Re}\left[F_{jj}(\mathbf{q},t)\right]

and the molecular incoherent intermediate scattering functions for ethanol
is

.. math::
   :label: moleculepartial6

   c_{\text{EtOH}}F_{\text{inc},\text{EtOH}}(\mathbf{q},t ) = W^{\text{EtOH}}_{\text{C}} F_{\text{inc},\text{C}}^{\text{EtOH}}(\mathbf{q},t ) + W^{\text{EtOH}}_{\text{H}}F_{\text{inc},\text{H}}^{\text{EtOH}}(\mathbf{q},t ) + \cdots.

with incoherent scattering length weights of

.. math::
   :label: moleculepartial7

   W_{\text{C}}^{\text{EtOH}} = \frac{c_{\text{C}}^{\text{EtOH}}\vert b_{\text{inc},\text{C}} \vert^{2}}{c_{\text{C}}^{\text{EtOH}}\vert b_{\text{inc},\text{C}} \vert^{2} + \cdots}.

The total incoherent intermediate scattering functions
is a weighted sum of all molecular terms

.. math::
    :label: moleculepartial8

    F_{\text{inc}}(\mathbf{q},t ) = c_{\text{EtOH}}F_{\text{inc},\text{EtOH}}(\mathbf{q},t ) + c_{\text{H2O}}F_{\text{inc},\text{H2O}}(\mathbf{q},t )

where the weight are the atom concentrations of the atoms in ethanol
and water. Similarly to the atom grouping, the total results with molecule
grouping are a weighted sum of atomic or molecular terms. In MDANSE, either
scaled or unscaled results can be plotted and may be more useful for the
specific results that has been calculated.


Other Groupings Schemes
^^^^^^^^^^^^^^^^^^^^^^^

In this section includes some analysis calculations with a group
setting which does follow the above mechanism.

.. _grouping-rmsd:

Root Mean Square Deviation
~~~~~~~~~~~~~~~~~~~~~~~~~~

Grouping in the root mean squared deviation (RMSD) analysis calculation
works similarly to the above mechanism. In the RMSD calculation, grouping
is done before the square root function is applied to the mean square
displacement. This means that grouping with the RMSD analysis will
gives the same result as the RMSD analysis when only those atom in the
group selected. For our water and ethanol system the molecule grouping
the RMSD of water is

.. math::
    :label: RMSDPart1

    \text{RMSD}_{\text{H2O}}(t) = \sqrt{ \frac{1}{Nc_{\text{H2O}}} \sum\limits_{j \in \text{H2O}} \vert \mathbf{r}_{j}(t) - \mathbf{r}_{j}(t_{\mathrm{ref}}) \vert^{2} }

and RMSD of the hydrogen atoms in water is

.. math::
    :label: RMSDPart2

    \text{RMSD}^{\text{H2O}}_{\text{H}}(t) = \sqrt{ \frac{1}{Nc^{\text{H2O}}_{\text{H}}} \sum\limits_{j \in (\text{H}\, \cap \, \text{H2O})} \vert \mathbf{r}_{j}(t) - \mathbf{r}_{j}(t_{\mathrm{ref}}) \vert^{2} }.


.. _grouping-rmsf:

Root Mean Square Fluctuation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The root mean square fluctuation (RMSF) analysis does not average
results but instead calculates them for individual atoms and groups them together.
With the ``atom`` option, the RMSF results will be split up into datasets,
with one dataset per each atom type. With the ``molecule`` option, the RMSF
results will be split up into groups of datasets, with one group per molecule type.
A group will contain results for each atom type in the molecule,
as well as the results for all atoms in the molecule.
