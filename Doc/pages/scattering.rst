
This section is dealing with specific types of analysis performed by
MDANSE. If you are not sure where these fit into the general workflow
of data analysis, please read :ref:`workflow-of-analysis`.

Analysis: Scattering
====================

This section contains background theory for following plugins:

-  :ref:`current-correlation-function`
-  :ref:`dynamic-coherent-structure-factor`
-  :ref:`dynamic-incoherent-structure-factor`
-  :ref:`elastic-incoherent-structure-factor`
-  :ref:`gaussian-dynamic-incoherent-structure-factor`
-  :ref:`neutron-dynamic-total-structure-factor`
-  :ref:`structure-factor-from-scattering-function`

This section discusses plugins used
to calculate neutron spectroscopy observables from the trajectory.
These plugins will be explored in depth in further sections, however,
before that, it is important to understand how MDANSE performs these
analyses. A part of that depends on how the :math:`\mathbf{q}`-vectors
are used to perform these analyses, see Section :ref:`qvector-generation`
for details.

.. _scattering_theory:

Scattering Background
'''''''''''''''''''''
**Dynamic Structure Factor** :math:`S(\mathbf{q}, \omega)`: This is a central
concept in neutron scattering experiments. This factor characterizes how
scattering intensity changes with alterations in momentum :math:`\mathbf{q}` and energy :math:`\hbar\omega`
during scattering events. It is instrumental in unraveling the atomic and
molecular structures of materials.

**Double Differential Cross-Section**: The dynamic structure factor is closely related to the
double differential cross-section, which is a vital measurement in neutron
scattering. The double differential cross-section, :math:`{\mathrm{d}^{2}{\sigma/\mathit{\mathrm{d}\Omega
\mathrm{d}E}}}`, is defined as the number of
neutrons scattered per unit time into the solid angle interval
:math:`{\left\lbrack {\Omega, {\Omega + \mathrm{d}}\Omega} \right\rbrack}` with an
energy in the interval :math:`{\left\lbrack {E, {E + \mathrm{d}}E} \right\rbrack}`. To make meaningful comparisons, the double differential cross-section
is normalized by :math:`\mathrm{d}\Omega`, :math:`\mathrm{d}E`, and the flux of the incoming neutrons. The relationship
between the double differential cross-section and the dynamic structure factor
is given by

.. math::
   :label: scattering1

   {{\frac{\mathrm{d}^{2}\sigma}{\mathrm{d}\Omega\mathrm{d}E} = N}\frac{k_{\mathrm{f}}}{k_{\mathrm{i}}}S\left( {\mathbf{q},\omega} \right).}

This equation relates the double differential cross-section, which represents
the number of neutrons scattered per unit time into specific solid angle and
energy intervals, to the dynamic structure factor, :math:`S(\mathbf{q}, \omega)`. It includes terms
related to the number of atoms :math:`N` and wavenumbers of scattered :math:`k_{\mathrm{f}}` and
incident :math:`k_{\mathrm{i}}` neutrons. They are related to the corresponding neutron energies by

.. math::
   :label: scattering2
   
   E_{\mathrm{f}} = \hbar^{2} k_{\mathrm{f}}^{2} / 2m_{\mathrm{n}} \qquad \text{and} \qquad E_{\mathrm{i}} = \hbar^{2}k_{\mathrm{i}}^{2} / 2m_{\mathrm{n}}.

These equations relate the neutron energies, :math:`E_{\mathrm{f}}` and :math:`E_{\mathrm{i}}`,
to their respective wavenumbers, :math:`k_{\mathrm{f}}` and :math:`k_{\mathrm{i}}`,
using the mass of the neutron :math:`m_{\mathrm{n}}`. They are fundamental for
connecting energy and momentum in neutron scattering.

**Momentum and Energy Transfer**: These equations below define the
momentum :math:`\mathbf{q}` and energy transfer :math:`\hbar\omega`
based on the incident and scattered wavevectors and energies

.. math::
   :label: scattering3

   \mathbf{q} = \mathbf{k}_{\mathrm{i}} - \mathbf{k}_{\mathrm{f}} \qquad \text{and} \qquad \hbar\omega = E_{\mathrm{i}} - E_{\mathrm{f}}.

The square modulus of the momentum transfer can be expressed in terms of a scattering
angle and the energies of the incident and scattered neutrons

.. math::
   :label: scattering4

   q^2 = \frac{2 m_{\mathrm{n}}}{\hbar^2} \left\{ E_{\mathrm{i}} + E_{\mathrm{f}} - 2\left(E_{\mathrm{i}}E_{\mathrm{f}} \right)^{1/2} \cos(\phi) \right\}.


**Intermediate Scattering Function** :math:`F(\mathbf{q}, t)`:
This equation defines the dynamic structure factor :math:`S(\mathbf{q}, \omega)` as a Fourier
transform of the intermediate scattering function :math:`F(\mathbf{q}, t)` with respect to
time :math:`t`. It captures information about the structure and dynamics of the
scattering system [Ref16]_ and can be written as

.. math::
   :label: scattering5

   {S{\left( {\mathbf{q},\omega} \right) = \frac{1}{2\pi}}{\int\mathrm{d}t \, } F\left( {\mathbf{q},t} \right) e^{-i \omega t}}

and

.. math::
   :label: scattering6

   {\text{F}{\left( {\mathbf{q},t} \right) = \frac{1}{N} {\sum\limits_{jk}{\Gamma_{jk}\left\langle {\exp\left\lbrack {{- i}\mathbf{q}\cdot\hat{\mathbf{r}}_{j}\left( 0 \right)} \right\rbrack\exp\left\lbrack {i\mathbf{q}\cdot\hat{\mathbf{r}}_{k}\left( t \right)} \right\rbrack} \right\rangle}}},}

.. math::
   :label: scattering7

   {{\Gamma_{jk} = }{\overline{b_{j}^{\dagger}}{\overline{b_{k}} + \delta_{jk}}( {\overline{\vert b_{j}\vert^{2}} - {\vert\overline{b_{j}}}\vert^{2}} )}}

where :math:`\hat{\mathbf{r}}_{j}(t)` are the position
operators of the nuclei in the Heisenberg picture. The quantities
:math:`b_{j}` are the scattering lengths of the nuclei
which depend on the isotope and
the relative orientation of the spin of the neutron and the spin of the
scattering nucleus. If the spins of the nuclei and the neutron are not
prepared in a special orientation one can assume a random relative
orientation and that spin and position of the nuclei are uncorrelated.
The overlines in Eq. :math:numref:`scattering7`
denotes that an average over isotopes and relative spin orientations of
neutron and nucleus is made.

**Coherent and Incoherent Scattering**:
Usually, one splits the intermediate scattering function and the dynamic
structure factor into their *coherent* and *incoherent* parts which
describe collective and single particle motions, respectively. By defining

.. math::
   :label: scattering8

   b_{\mathrm{coh},j} = \overline{b_{j}} \qquad \text{and} \qquad b_{\mathrm{inc},j} = \sqrt{\overline{\vert b_{j}\vert^{2}} - {\vert\overline{b_{j}}}\vert^{2}}

the coherent and incoherent intermediate scattering functions can be
written. They are expressed as sums over pairs of nuclei, with different
treatments for coherent and incoherent scattering lengths

.. math::
   :label: scattering9

   {\text{F}_{\text{coh}}{\left( {q,t} \right) = \frac{1}{N}}{\sum\limits_{jk}b_{\mathrm{coh},j}}b_{\mathrm{coh},k}\left\langle {\exp\left\lbrack {{- i}\mathbf{q}\cdot\hat{\mathbf{r}}_{j}\left( 0 \right)} \right\rbrack\exp\left\lbrack {i\mathbf{q}\cdot\hat{\mathbf{r}}_{k}\left( t \right)} \right\rbrack} \right\rangle,}

.. math::
   :label: scattering10

   {\text{F}_{\text{inc}}{\left( {q,t} \right) = \frac{1}{N}}{\sum\limits_{j}{b_{\mathrm{inc},j}^{2}\left\langle {\exp\left\lbrack {{- i}\mathbf{q}\cdot\hat{\mathbf{r}}_{j}\left( 0 \right)} \right\rbrack\exp\left\lbrack {i\mathbf{q}\cdot\hat{\mathbf{r}}_{j}\left( t \right)} \right\rbrack} \right\rangle}}.}


**Classical Framework and Corrections**:
In the classical framework the intermediate scattering functions are
interpreted as classical time correlation functions. The position
operators are replaced by time-dependent vector functions and quantum
thermal averages are replaced by classical *ensemble averages*. It is
well known that this procedure leads to a loss of the universal detailed
balance relation

.. math::
   :label: scattering11

   S(\mathbf{q},\omega) = \exp(\beta\hbar\omega) S( - \mathbf{q} , - \omega)

and also to a loss of all odd moments

.. math::
   :label: scattering12

   {\left\langle \omega^{2{n + 1}} \right\rangle = {\int{\mathrm{d}\omega}}\, \omega^{2{n + 1}}S\left( {\mathbf{q},\omega} \right).}

The odd moments vanish since the classical dynamic structure factor is
even in :math:`\omega`, assuming invariance of the scattering process with respect to
reflections in space. The first moment is also universal. For an atomic
liquid, containing only one type of atom

.. math::
   :label: scattering13

   {{\left\langle \omega \right\rangle = \frac{\hbar q^{2}}{2M}}}

where :math:`M` is the mass of the atom.

**Recoil Moment**: Eq. :math:numref:`scattering13` shows that the
first moment is given by the average kinetic energy (in units of
:math:`\hbar`) of a particle which receives a momentum transfer
:math:`\hbar q`. Therefore, :math:`\langle\omega\rangle`
is called the *recoil moment*. A number of "recipes" has been suggested
to correct classical dynamic structure factors for detailed balance and
to describe recoil effects in an approximate way. The most popular one
has been suggested by Schofield [Ref17]_

.. math::
   :label: scattering14

   {{S\left( {\mathbf{q},\omega} \right)\approx\exp(\beta\hbar\omega / 2)} S_{\mathrm{cl}}\left( {\mathbf{q},\omega} \right)}.

One can easily verify that the resulting dynamic structure factor
fulfils the relation of detailed balance. Formally, the correction :math:numref:`scattering14`
is correct to first order in :math:`\hbar` and cannot be used
for large :math:`\mathbf{q}`-values which correspond to large momentum transfers
:math:`\hbar q`. This is actually true for all correction
methods which have suggested so far. For more details we refer to [Ref18]_.


.. _current-correlation-function:

Current Correlation Function
''''''''''''''''''''''''''''

The current correlation functions :math:`J_{\mu\nu}(\mathbf{q}, t)` and its Fourier transform :math:`J_{\mu\nu}(\mathbf{q}, \omega)`
are closely related to the intermediate scattering function :math:`F(\mathbf{q}, t)`
and the dynamics structure factor :math:`S(\mathbf{q}, \omega)` respectively. The intermediate
scattering function :math:`F(\mathbf{q}, t)` is a correlation function of the Fourier components of
particle density whereas the current correlation function :math:`J_{\mu\nu}(\mathbf{q}, t)`
is the correlation function of the Fourier components of the particle current

.. math::
   :label: ccf1

    J_{\mu\nu}(\mathbf{q}, t) = \sum_{\alpha}\sum_{\beta \geq \alpha} W_{\alpha\beta} J_{\alpha\beta\mu\nu}(\mathbf{q}, t),

.. math::
   :label: ccf2

    J_{\alpha\beta\mu\nu}(\mathbf{q}, t) = \frac{1}{N \sqrt{c_{\alpha} c_{\beta}}} \langle j_{\alpha\mu}(-\mathbf{q}, 0) j_{\beta\nu}(\mathbf{q}, t) \rangle

where :math:`\mu` and  :math:`\nu` are the cartesian directions
:math:`x`, :math:`y` or :math:`z` and

.. math::
   :label: ccf3

   j_{\alpha\mu}(\mathbf{q}, t) = \sum_{k \in \alpha} v_{k\mu}(t) \exp(i\mathbf{q} \cdot \mathbf{r}_{k}(t)).

The particle currents can be projected onto
longitudinal and transverse components of the :math:`\mathbf{q}`-vector. The
longitudinal and transverse particle current are

.. math::
   :label: ccf4

    \mathbf{j}^{\mathrm{L}}_{\alpha}(\mathbf{q}, t) = \sum_{k \in \alpha} \hat{\mathbf{q}} \left[\mathbf{v}_{k}(t) \cdot \hat{\mathbf{q}}\right]\exp(i \mathbf{q}\cdot \mathbf{r}_k(t)),

.. math::
   :label: ccf5

    \mathbf{j}^{\mathrm{T}}_{\alpha}(\mathbf{q}, t) = \sum_{k \in \alpha} \left\{\mathbf{v}_{k}(t) - \hat{\mathbf{q}}\left[\mathbf{v}_{k}(t) \cdot \hat{\mathbf{q}}\right] \right\}\exp(i \mathbf{q}\cdot \mathbf{r}_k(t))

where :math:`\hat{\mathbf{q}}` are unit vectors of :math:`\mathbf{q}`. The
partial longitudinal and transverse current correlation functions are

.. math::
   :label: ccf6

    J^{\mathrm{L}}_{\alpha\beta}(\mathbf{q}, t) = \frac{1}{N \sqrt{c_{\alpha} c_{\beta}}} \langle \mathbf{j}^{\mathrm{L}}_{\alpha}(-\mathbf{q}, 0) \cdot \mathbf{j}^{\mathrm{L}}_{\beta}(\mathbf{q}, t) \rangle,

.. math::
   :label: ccf7

    J^{\mathrm{T}}_{\alpha\beta}(\mathbf{q}, t) = \frac{1}{N \sqrt{c_{\alpha} c_{\beta}}} \langle \mathbf{j}^{\mathrm{T}}_{\alpha}(-\mathbf{q}, 0) \cdot \mathbf{j}^{\mathrm{T}}_{\beta}(\mathbf{q}, t) \rangle.


From the continuity equation we can obtain a relation between the
longitudinal current correlation and the dynamic structure factor

.. math::
   :label: ccf8

    J^{\mathrm{L}}_{\alpha\beta}(\mathbf{q}, \omega) = \frac{\omega^2}{q^2} S_{\alpha\beta}(\mathbf{q}, \omega).

.. _dynamic-coherent-structure-factor:

Dynamic Coherent Structure Factor
'''''''''''''''''''''''''''''''''
In MDANSE the dynamic coherent structure factor (DCSF) and coherent
intermediate scattering function is a weighted sum of the partial term

.. math::
   :label: dcsf1

    S_{\text{coh}}(\mathbf{q},\omega) = \sum_{\alpha}\sum_{\beta \geq \alpha} W_{\alpha\beta} S_{\text{coh},\alpha\beta}(\mathbf{q},\omega),

.. math::
   :label: dcsf2

    F_{\text{coh}}(\mathbf{q},t) = \sum_{\alpha}\sum_{\beta \geq \alpha} W_{\alpha\beta} F_{\text{coh},\alpha\beta}(\mathbf{q},t)

where

.. math::
   :label: dcsf3

   F_{\text{coh},\alpha\beta}{(\mathbf{q},t) = \frac{1}{N \sqrt{c_{\alpha} c_{\beta}}}}{\sum\limits_{j \in \alpha}{\sum\limits_{k \in \beta}\left\langle {\exp\left\lbrack {{- i}\mathbf{q}\cdot\mathbf{r}_{j}\left( 0 \right)} \right\rbrack\exp\left\lbrack {i\mathbf{q}\cdot\mathbf{r}_{k}\left( t \right)} \right\rbrack} \right\rangle}}

and

.. math::
   :label: dcsf4

    S_{\text{coh},\alpha\beta}(\mathbf{q},\omega) = \int\mathrm{d}t  \,  F_{\text{coh},\alpha\beta}(\mathbf{q},t) e^{-i\omega t}.

To obtain results relevant to neutron scattering, the
``b_coherent`` weight setting should be used so that the weight will be
generated using the coherent scattering lengths.


.. _dynamic-incoherent-structure-factor:

Dynamic Incoherent Structure Factor
'''''''''''''''''''''''''''''''''''
In MDANSE the dynamic incoherent structure factor (DISF) and incoherent
intermediate scattering function is a weighted sum of the partial term

.. math::
   :label: disf1

    S_{\text{inc}}(\mathbf{q},\omega) = \sum_{\alpha}\sum_{\beta \geq \alpha} W_{\alpha\beta} S_{\text{inc},\alpha\beta}(\mathbf{q},\omega),

.. math::
   :label: disf2

    F_{\text{inc}}(\mathbf{q},t) = \sum_{\alpha}\sum_{\beta \geq \alpha} W_{\alpha\beta} F_{\text{inc},\alpha\beta}(\mathbf{q},t)

where

.. math::
   :label: disf3

   F_{\text{inc},\alpha\beta}{(\mathbf{q},t) = \frac{1}{N c_{\alpha} }}{\sum\limits_{j \in \alpha}{\left\langle {\exp\left\lbrack {{- i}\mathbf{q}\cdot\mathbf{r}_{j}\left( 0 \right)} \right\rbrack\exp\left\lbrack {i\mathbf{q}\cdot\mathbf{r}_{j}\left( t \right)} \right\rbrack} \right\rangle}}

and

.. math::
   :label: disf4

    S_{\text{inc},\alpha\beta}(\mathbf{q},\omega) = \int\mathrm{d}t  \,  F_{\text{inc},\alpha\beta}(\mathbf{q},t) e^{-i\omega t}.

To obtain results relevant to neutron scattering, the
``b_incoherent2`` weight setting should be used so that the weight will be
generated using the coherent scattering lengths.


.. _elastic-incoherent-structure-factor:

Elastic Incoherent Structure Factor
'''''''''''''''''''''''''''''''''''

The elastic incoherent structure factor (EISF) appears as the amplitude of
the *elastic* line in the neutron scattering spectrum. Elastic scattering is
only present for systems in which the atomic motion is confined in space, as
for solids. To understand which information is contained in the EISF we consider
for simplicity a system where only one sort of atoms is visible to the neutrons.
To a very good approximation this is the case for all systems containing a large
amount of hydrogen atoms, as for biological systems. Incoherent scattering from
hydrogen dominates by far all other contributions.

**The Van Hove Function**: The EISF is defined as the limit of the
incoherent intermediate scattering function for infinite time

.. math::
   :label: eisf1

   {\mathrm{EISF}(\mathbf{q}) = \lim\limits_{t\rightarrow\infty} F_{\mathrm{inc}}( {\mathbf{q},t} ).}

Using the above definition of the EISF one can decompose the incoherent
intermediate scattering function as follows

.. math::
   :label: eisf2

   {F_{\text{inc}}{( {\mathbf{q},t} ) = \mathrm{EISF}}{(\mathbf{q}) + F_{\text{inc}}'}( {\mathbf{q},t} )}

where :math:`F_{\mathrm{inc}}'(\mathbf{q}, t)` decays to zero for infinite time. Taking
now the Fourier transform it follows immediately that

.. math::
   :label: eisf3

   {S_{\text{inc}}{( {\mathbf{q},\omega} ) = \mathrm{EISF}}(\mathbf{q})\delta{(\omega) + S_{\text{inc}}'}( {\mathbf{q},\omega} ).}

Using the definition of the self-part of the van Hove function

.. math::
   :label: eisf4

   \rho G_{\mathrm{s}} (\mathbf{r},t) = \frac{1}{2\pi^{3}} \int \mathrm{d} \mathbf{q} \, F_{\mathrm{inc}}(\mathbf{q},t) e^{-i\mathbf{q}\cdot\mathbf{r}}

which can be interpreted as the conditional probability to find a tagged
particle at the position :math:`\mathbf{r}` at time :math:`t`, given it
started at the origin, one can write

.. math::
   :label: eisf5

   {\mathrm{EISF}(\mathbf{q}) = {\int \mathrm{d}}\mathbf{r} \,  G_{\mathrm{s}}( {\mathbf{r},{t = \infty}} )e^{-i\mathbf{q}\cdot\mathbf{r}}.}

The EISF gives the sampling distribution of the points in space in the
limit of infinite time. In a real experiment this means times longer
than the time which is observable with a given instrument. The EISF
vanishes for all systems in which the particles can access an infinite
volume since :math:`G_{\mathrm{s}}(r, t)` approaches :math:`N^{-1}` for large times,
this is the case for molecules in liquids and gases.

**EISF Computation**: For computational purposes it is convenient to use the following
representation of the EISF

.. math::
   :label: eisf6

   \mathrm{EISF}(\mathbf{q}) = \sum\limits_{\alpha} W_{\alpha} \mathrm{EISF}_{\alpha}(\mathbf{q}), \qquad \mathrm{EISF}_{\alpha}(\mathbf{q}) = \frac{1}{Nc_{\alpha}} \sum\limits_{j \in \alpha}  \left\vert \left\langle \exp[i \mathbf{q} \cdot \mathbf{r}_{j}] \right\rangle \right\vert^{2}

where :math:`\mathrm{EISF}_{\alpha}(\mathbf{q})` is the EISF of atom-types :math:`\alpha`. This
expression is derived from definition Eq. :math:numref:`eisf1`
of the EISF and expression Eq. :math:numref:`disf3` for the
intermediate scattering function, using that for infinite time the
relation

.. math::
   :label: eisf7
   
   \lim\limits_{t\rightarrow\infty}{\left\langle {\exp\left\lbrack {{- i\mathbf{q}}\cdot \mathbf{r}_{j}(0)} \right\rbrack\exp\left\lbrack { i\mathbf{q}\cdot \mathbf{r}_{j}(t)} \right\rbrack} \right\rangle = \left\langle \exp[-i \mathbf{q} \cdot \mathbf{r}_{j}(0)] \right\rangle \left\langle \exp[i \mathbf{q} \cdot \mathbf{r}_{j}(t)] \right\rangle}

holds. In this way the computation of the EISF is reduced to the
computation of a static thermal average. We remark at this point that
the length of the MD trajectory from which the EISF is computed
should be long enough to allow for a representative sampling of the
conformational space.

.. _gaussian-dynamic-incoherent-structure-factor:

Gaussian Dynamic Incoherent Structure Factor
''''''''''''''''''''''''''''''''''''''''''''

**Cumulant Expansion**: The MSD can be related to the incoherent intermediate scattering
function via the cumulant expansion [Ref11]_, [Ref22]_

.. math::
   :label: gdisf1

   F_{\text{inc}}(\mathbf{q},t ) = \sum\limits_{\alpha} W_{\alpha} F_{\text{inc},\alpha}( \mathbf{q},t),

.. math::
   :label: gdisf2

   F_{\text{inc},\alpha}(\mathbf{q},t) = \frac{1}{N c_{\alpha} } \sum\limits_{j \in \alpha} \exp\left[ -q^2 p_{1,j}(t) + q^4 p_{2,j}(t) + \cdots \right].

The cumulants :math:`p_{n,j}(t)` are identified as

.. math::
   :label: gdisf3

   p_{1,j}(\hat{\mathbf{q}},t){ = \frac{1}{2!}\left\langle d_{j}^{2}(\hat{\mathbf{q}}, t) \right\rangle},

.. math::
   :label: gdisf4

   p_{2,j}(\hat{\mathbf{q}},t){ = \frac{1}{4!}}\left\lbrack {{\left\langle {d_{j}^{4}(\hat{\mathbf{q}}, t)} \right\rangle - 3}\left\langle {d_{j}^{2}(\hat{\mathbf{q}}, t)} \right\rangle^{2}} \right\rbrack

where

.. math::
   :label: gdisf5

    \Delta_{j}^{2}(\hat{\mathbf{q}},t) = \langle d_{j}^{2}(\hat{\mathbf{q}}, t) \rangle = \langle \left\vert \hat{\mathbf{q}} \cdot [\mathbf{r}_{j}(t) - \mathbf{r}_{j}(0)] \right\vert^2 \rangle

is the means squared displacement of atom :math:`j` along the
axis :math:`\hat{\mathbf{q}}`.

**Gaussian Approximation**: In the Gaussian
approximation the above expansion is truncated after the
:math:`q^2`-term

.. math::
   :label: gdisf6

   F_{\text{inc},\alpha}(\mathbf{q},t) \approx F_{\text{inc},\alpha}^{\text{G}}(\mathbf{q},t) = \frac{1}{N c_{\alpha} } \sum\limits_{j \in \alpha} \exp\left[ -q^2 p_{1,j}(\hat{\mathbf{q}}, t) \right].

For certain model systems like the ideal gas, the
harmonic oscillator, and a particle undergoing Einstein diffusion, this
is exact. For these systems the incoherent intermediate scattering
function is completely determined by the MSD.

.. _neutron-dynamic-total-structure-factor:

Neutron Dynamic Total Structure Factor
''''''''''''''''''''''''''''''''''''''
This is a combines the coherent and incoherent intermediate scattering
functions and corresponding dynamic structure factors. It is a fully
neutron-specific analysis, so that coherent neutron scattering
lengths ``b_coherent`` and the square of the atomic
incoherent neutron scattering lengths ``b_incoherent2`` are used to
weight the corresponding coherent and incoherent signals.

In this analysis the total incoherent, total coherent and total
(coherent + incoherent) signals are calculated as

.. math::
   :label: ndtsf1
   
   F_{\mathrm{inc}}(\mathbf{q},t) = \sum_{\alpha} c_{\alpha}b_{\text{inc},\alpha}^{2} F_{\mathrm{inc},\alpha}(\mathbf{q},t),

.. math::
   :label: ndtsf2
   
   F_{\mathrm{coh}}(\mathbf{q},t) = \sum_{\alpha\beta} \sqrt{c_{\alpha}c_{\beta}} b_{\text{coh},\alpha}b_{\text{coh},\beta} F_{\mathrm{coh},\alpha\beta}(\mathbf{q},t),

.. math::
   :label: ndtsf3
   
   F(q,t) = F_{\mathrm{inc}}(\mathbf{q},t) + F_{\mathrm{coh}}(\mathbf{q},t).

These expressions correspond to the formalism and equations given in
[Ref47]_ - Chapter 1: “An introduction to neutron scattering” .


.. _structure-factor-from-scattering-function:

Structure Factor From Scattering Function
'''''''''''''''''''''''''''''''''''''''''
Calculates the static structure factor from the coherent intermediate
scattering function via the following expression

.. math::
   :label: sffsf1

   S_{\alpha\beta}(q) = \delta_{\alpha\beta} + \sqrt{c_{\alpha}c_{\beta}} \left[ F_{\mathrm{coh},\alpha\beta}(q, 0) - 1 \right].

To obtain the total results MDANSE will use the same weights that were
used in the DCSF calculation.
