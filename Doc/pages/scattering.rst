
This section is dealing with specific types of analysis performed by
MDANSE. If you are not sure where these fit into the general workflow
of data analysis, please read :ref:`workflow-of-analysis`.

Analysis Theory: Scattering
===========================

This section contains the following plugins:

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
analyses. A part of that are :ref:`param-q-vectors`, which
are used to perform these analyses. An in-depth discussion of this
aspect is present in `Appendix 2 <#_Appendix_2>`__.

.. _scattering_theory:

Theory and background
'''''''''''''''''''''
**Dynamic Structure Factor S(q, ω):** This is a central
concept in neutron scattering experiments. This factor characterizes how
scattering intensity changes with alterations in momentum (:math:`q`) and energy (:math:`\omega`)
during scattering events. It is instrumental in unraveling the atomic and
molecular structures of materials.

**Double Differential Cross-Section:** :math:`S(q, \omega)` is closely related to the
double differential cross-section [7], which is a vital measurement in neutron
scattering. The double differential cross-section, :math:`{d^{2}{\sigma/\mathit{d\Omega
dE}}}`, is defined as the number of
neutrons scattered per unit time into the solid angle interval
:math:`{\left\lbrack {\Omega, {\Omega + d}\Omega} \right\rbrack}` with an
energy in the interval :math:`{\left\lbrack {E, {E + d}E} \right\rbrack}`. To make meaningful comparisons, the double differential cross-section
is normalized by :math:`d\Omega`, :math:`dE`, and the flux of the incoming neutrons. The relationship
between the double differential cross-section and the dynamic structure factor
is given by:

.. math::
   :label: pfx55

   {{\frac{d^{2}\sigma}{d\Omega\mathit{dE}} = N}\cdot\frac{k}{k_{0}}S\left( {q,\omega} \right).}

This equation relates the double differential cross-section, which represents
the number of neutrons scattered per unit time into specific solid angle and
energy intervals, to the dynamic structure factor, :math:`S(q, \omega)`. It includes terms
related to the number of atoms (:math:`N`) and wave numbers of scattered (:math:`k`) and
incident (:math:`k_0`) neutrons.

They are related to the corresponding neutron energies by

.. math::
   :label: pfx56
   
   {E = \hbar^{2}}k^{2}\text{/}2m

\ and

.. math::
   :label: pfx57
   
   {E_{0} = \hbar^{2}}k_{0}^{2}\text{/}2m


These equations relate the neutron energies (:math:`E` and :math:`E_0`) to their respective wave
numbers (:math:`k` and :math:`k_0`) using the mass of the neutron (:math:`m`). They are fundamental for
connecting energy and momentum in neutron scattering.

**Dimensionless Momentum and Energy Transfer:** These equations below define the
dimensionless momentum (:math:`q`, dynamic structure factor) and energy (:math:`\omega`) transfer in
units of the reduced Planck constant (:math:`\hbar`) based on the incident and scattered
wave numbers and energies:

.. math::
   :label: pfx58

   {{q = \frac{k_{0} - k}{\hbar}},}

.. math::
   :label: pfx59

   {{\omega = \frac{E_{0} - E}{\hbar}}.}

The modulus of the momentum transfer can be expressed in terms of a scattering
angle, energy transfer, and incident neutron energy. See equation below:

.. math::
   :label: pfx60

   {{\vert q \vert = \vert k_{0} \vert \sqrt{{2 - \frac{\mathit{\hbar\omega}}{E_{0}} - 2}\cos{\theta\sqrt{1 - \frac{\mathit{\hbar\omega}}{E_{0}}}}}}.}


**Intermediate Scattering Function F(q, t):**
This equation defines the dynamic structure factor, :math:`S(q, \omega)`, as a Fourier
transform of the intermediate scattering function, :math:`F(q, t)`, with respect to
time, :math:`t`. It captures information about the structure and dynamics of the
scattering system [Ref16]_. It can be written as:

.. math::
   :label: pfx61

   {S{\left( {q,\omega} \right) = \frac{1}{2\pi}}{\int\limits_{- \infty}^{+ \infty}\mathit{dt}}\exp\left\lbrack {{- i}\omega t} \right\rbrack F\left( {q,t} \right).}

:math:`F(q, t)` is called the *intermediate scattering function* and is defined as

.. math::
   :label: pfx62

   {\text{F}{\left( {q,t} \right) = {\sum\limits_{\alpha,\beta}{\Gamma_{\mathit{\alpha\beta}}\left\langle {\exp\left\lbrack {{- i}q\cdot\hat{R}_{\alpha}(0)} \right\rbrack\exp\left\lbrack {iq\cdot\hat{R}_{\beta}(t)} \right\rbrack} \right\rangle}}},}

.. math::
   :label: pfx63

   {{\Gamma_{\mathit{\alpha\beta}} = \frac{1}{N}}\left\lbrack {\overline{b_{\alpha}}{\overline{b_{\beta}} + \delta_{\mathit{\alpha\beta}}}\left( {\overline{b_{\alpha}^{2}} - {\overline{b_{\alpha}}}^{2}} \right)} \right\rbrack.}

The operators :math:`\hat{R}_{\alpha}(t)`
in Eq. :math:numref:`pfx62` are the position
operators of the nuclei in the sample. The brackets
:math:`\langle\ldots\rangle`
denote a quantum thermal average and the time dependence of the position
operators is defined by the Heisenberg picture. The quantities
:math:`b_{\alpha}` are the scattering lengths of the nuclei
which depend on the isotope and
the relative orientation of the spin of the neutron and the spin of the
scattering nucleus. If the spins of the nuclei and the neutron are not
prepared in a special orientation one can assume a random relative
orientation and that spin and position of the nuclei are uncorrelated.
The overbars :math:`\overline{...}` appearing in :math:`{\Gamma_{\mathit{\alpha\beta}}}`
denotes an average over isotopes and relative spin orientations of
neutron and nucleus.

**Coherent and Incoherent Scattering:**
Usually, one splits the intermediate scattering function and the dynamic
structure factor into their *coherent* and *incoherent* parts which
describe collective and single particle motions, respectively. Defining

.. math::
   :label: pfx65

   {b_{\alpha,\mathrm{coh}}\doteq\overline{b_{\alpha}},}

.. math::
   :label: pfx66

   {b_{\alpha,\mathrm{inc}}\doteq\sqrt{\overline{b_{\alpha}^{2}} - {\overline{b_{\alpha}}}^{2}},}

the coherent and incoherent intermediate scattering functions can be
written. They are expressed as sums over pairs of nuclei, with different
treatments for coherent and incoherent scattering lengths.

.. math::
   :label: pfx67

   {\text{F}_{\text{coh}}{\left( {q,t} \right) = \frac{1}{N}}{\sum\limits_{\alpha,\beta}b_{\alpha,\mathrm{coh}}}b_{\beta,\mathrm{coh}}\left\langle {\exp\left\lbrack {{- i}q\cdot\hat{R}_{\alpha}(0)} \right\rbrack\exp\left\lbrack {iq\cdot\hat{R}_{\beta}(t)} \right\rbrack} \right\rangle,}

.. math::
   :label: pfx68

   {\text{F}_{\text{inc}}{\left( {q,t} \right) = \frac{1}{N}}{\sum\limits_{\alpha}{b_{\alpha,\mathrm{inc}}^{2}\left\langle {\exp\left\lbrack {{- i}q\cdot\hat{R}_{\alpha}(0)} \right\rbrack\exp\left\lbrack {iq\cdot\hat{R}_{\alpha}(t)} \right\rbrack} \right\rangle}}.}

*MDANSE* introduces the partial terms, this consider different species :math:`(I, J)` and their contributions to the scattering process.

.. math::
   :label: pfx69

   {\text{F}_{\text{coh}}{\left( {q,t} \right) = \sum\limits_{I,J\geq I}^{N_{\mathrm{species}}}}\sqrt{n_{I}n_{J}\omega_{I,\text{coh}}\omega_{J,\text{coh}}}F_{\mathit{IJ},\text{coh}}\left( {q,t} \right),}

.. math::
   :label: pfx70

   {\text{F}_{\text{inc}}{\left( {q,t} \right) = {\sum\limits_{I = 1}^{N_{\mathrm{species}}}{n_{I}\omega_{I,\text{inc}}F_{I,\text{inc}}\left( {q,t} \right)}}}}

where:

.. math::
   :label: pfx71

   {\text{F}_{\mathit{IJ},\text{coh}}{\left( {q,t} \right) = \frac{1}{\sqrt{n_{I}n_{J}}}}{\sum\limits_{\alpha}^{n_{I}}{\sum\limits_{\beta}^{n_{J}}\left\langle {\exp\left\lbrack {{- i}q\cdot\hat{R}_{\alpha}\left( t_{0} \right)} \right\rbrack\exp\left\lbrack {iq\cdot\hat{R}_{\beta}\left( {t_{0} + t} \right)} \right\rbrack} \right\rangle_{t_{0}}}},}

.. math::
   :label: pfx72

   {\text{F}_{I,\text{inc}}{\left( {q,t} \right) = \frac{1}{n_{I}}}{\sum\limits_{\alpha = 1}^{n_{I}}\left\langle {\exp\left\lbrack {{- i}q\cdot\hat{R}_{\alpha}\left( t_{0} \right)} \right\rbrack\exp\left\lbrack {iq\cdot\hat{R}_{\alpha}\left( {t_{0} + t} \right)} \right\rbrack} \right\rangle_{t_{0}}}.}

where :math:`n_I`, :math:`n_J`, :math:`n_{\mathrm{species}}`, :math:`\omega_{I,(\mathrm{coh}/\mathrm{inc})}`
and :math:`\omega_{J,(\mathrm{coh}/\mathrm{inc})}` are defined in Section :ref:`target_CN`. The corresponding dynamic structure factors are obtained by performing
the Fourier transformation defined in Eq. :math:numref:`pfx61`.


**Classical Framework and Corrections:**
In the classical framework the intermediate scattering functions are
interpreted as classical time correlation functions. The position
operators are replaced by time-dependent vector functions and quantum
thermal averages are replaced by classical *ensemble averages*. It is
well known that this procedure leads to a loss of the universal detailed
balance relation,

.. math::
   :label: pfx74

   {\text{S}{\left( {q,\omega} \right) = \exp}\left\lbrack {\beta\hbar\omega} \right\rbrack\text{S}\left( {{- q}{, - \omega}} \right),}

and also to a loss of all odd moments

.. math::
   :label: pfx75

   {\left\langle \omega^{2{n + 1}} \right\rangle\doteq{\int\limits_{- \infty}^{+ \infty}{d\omega}}\, \omega^{2{n + 1}}S\left( {q,\omega} \right) \qquad {n = 1,2},\ldots.}

The odd moments vanish since the classical dynamic structure factor is
even in :math:`\omega`, assuming invariance of the scattering process with respect to
reflections in space. The first moment is also universal. For an atomic
liquid, containing only one sort of atoms, it reads

.. math::
   :label: pfx76

   {{\left\langle \omega \right\rangle = \frac{\hbar q^{2}}{2M}},}

where :math:`M` is the mass of the atoms.

**Recoil Moment:** Formula :math:numref:`pfx76` shows that the
first moment is given by the average kinetic energy (in units of
:math:`\hbar`) of a particle which receives a momentum transfer
:math:`\hbar q`. Therefore, :math:`\langle\omega\rangle`
is called the *recoil moment*. A number of 'recipes' has been suggested
to correct classical dynamic structure factors for detailed balance and
to describe recoil effects in an approximate way. The most popular one
has been suggested by Schofield [Ref17]_

.. math::
   :label: pfx77

   {{\text{S}\left( {q,\omega} \right)\approx\exp\left\lbrack \frac{\beta\hbar\omega}{2} \right\rbrack}_{}\text{S}_{\mathrm{cl}}\left( {q,\omega} \right)}

One can easily verify that the resulting dynamic structure factor
fulfils the relation of detailed balance. Formally, the correction :math:numref:`pfx77`
is correct to first order in :math:`\hbar`. Therefore, it cannot be used
for large :math:`q`-values which correspond to large momentum transfers
:math:`\hbar q`. This is actually true for all correction
methods which have suggested
so far. For more details we refer to Ref.
[Ref18]_.


**Static Structure Factor S(q):** An important quantity describing structural properties of liquids is the
static structure factor. :math:`S(q)` as an integral involving the
dynamic structure factor which is also the coherent intermediate scattering function
at zero time delay :math:`t = 0`.

.. math::
   :label: pfx73

   {\text{S}(q)\doteq{\int\limits_{- \infty}^{+ \infty}{d\omega}}\,\text{S}_{\mathrm{coh}}\left( {q,\omega} \right) = \text{F}_{\mathrm{coh}}\left( {q,0} \right).}

**Total Structure Factors:** MDANSE computes the partial :math:`S(Q)` as the Fourier transform of the
partial pair distribution function :math:`g(r)`, corresponding to the Faber-Ziman definition:

.. math::
   :label: pfx78
   
   {S_{\alpha\beta}(Q) = 1 + \frac{4\pi\rho_0}{Q}\int\limits_{0}^{\infty}{dr \, r \sin(Qr) \left\lbrack {g_{\alpha\beta}}(r)-1 \right\rbrack}}

The total :math:`S(Q)` is computed as a weighted sum similar to the one used for
the total :math:`g(r)`. In the case of the analysis 'X-ray Static structure
factor', the :math:`Q`-dependence of the atomic form factors is taken into
account in this weighted sum.

**X-ray Observable Normalization:** Again, Soper has provided experimental data (table 4 in *ISRN Physical
Chemistry*, 279463 (2013), given in file soper13_fx.dat). Here a source
of confusion is that the data can be normalized in different ways (see
Soper's paper). Using the normalization II in that reference we have
that:

.. math::
   :label: pfx79
   
    D_{x}{(Q) = \frac{\sum\limits_{\mathit{\alpha\beta}\geq\alpha}{\left( {2 - \delta_{\mathit{\alpha\beta}}} \right) c_{\alpha}c_{\beta}f_{\alpha}{(Q)}f_{\beta}{(Q)}\left\lbrack {S_{\mathit{\alpha\beta}}{(Q) - 1}} \right\rbrack}}{\sum\limits_{\alpha}{c_{\alpha}f_{\alpha}^{2}{(Q)}}} = \left\lbrack {S{(Q) - 1}} \right\rbrack}\frac{\sum\limits_{\mathit{\alpha\beta}}{c_{\alpha}c_{\beta}f_{\alpha}{(Q)}f_{\beta}{(Q)}}}{\sum\limits_{\alpha}{c_{\alpha}f_{\alpha}^{2}{(Q)}}}

Where :math:`S(Q)` would be the static structure factor (going to :math:`1` at large :math:`Q`)
computed by MDANSE. Therefore, even after using MDANSE we should
recalculate the x-ray observable using the atomic factors.

.. _current-correlation-function:

Current Correlation Function
''''''''''''''''''''''''''''

The correlation function is a fundamental concept in the study of dynamical
processes in various physical systems, including disordered materials. It
provides insights into how fluctuations or excitations propagate through a
system over time. In the context of disordered systems, understanding the
correlation function can help reveal the behavior of particles or components
in a disordered environment, such as a disordered solid or a supercooled
liquid.

In the context of MDANSE, researchers calculate two essential components
of the correlation function:

- **Longitudinal Component:** This component is associated with density
  fluctuations, offering insights into how particle or atom densities change
  at specific locations within the disordered system over time.

- **Transverse Component:** The transverse component is linked to propagating
  shear modes, helping researchers comprehend the relative displacements of
  neighboring particles or atoms and the propagation of these shear modes
  throughout the disordered material.

.. _dynamic-coherent-structure-factor:

Dynamic Coherent Structure Factor
'''''''''''''''''''''''''''''''''
In materials science and condensed matter physics, dynamic coherent structure
factors are crucial. They enable a comprehensive understanding of complex
particle or atom movements and interactions over time. These factors provide
invaluable insights into the dynamic behavior of materials, aiding researchers in
deciphering particle evolution and characterizing properties such as diffusion
rates, elasticity, and phase transitions. They play a pivotal role in enhancing
our understanding of system dynamics and significantly benefit research in these
fields.

In this analysis, MDANSE proceeds in two steps. First, it computes the partial
and total intermediate coherent scattering function using equation
:math:numref:`pfx69`. Then, the partial and total dynamic coherent structure
factors are obtained by performing the Fourier Transformation, defined in Eq.
:math:numref:`pfx61`, respectively on the total and partial intermediate
coherent scattering functions.

**Coherent Intermediate Scattering Function Calculation:**
*MDANSE* computes the coherent intermediate scattering function on a
rectangular grid of equidistantly spaced points along the time-and the
:math:`q`-axis, respectively:

.. math::
   :label: pfx80
   
   {{F}_{\text{coh}}\left( {q_{m},k\cdot\Delta t} \right)\doteq{\sum\limits_{{I = 1},J\geq I}^{N_{\mathrm{species}}}\sqrt{n_{I}n_{J}\omega_{I,\text{com}}\omega_{I,\text{com}}}}{\overline{\left\langle {\rho_{I}\left( {{-q},0} \right)\rho_{J}\left( {q,k\cdot\Delta t} \right)} \right\rangle}}^{q},}

where :math:`{k = 0}, \ldots, {N_{t} - 1}` and :math:`{m = 0}, \ldots, {N_{q} - 1}`.
:math:`N_t` is the number of time steps in the coordinate time series,
:math:`N_q` is a user-defined number of :math:`q`-shells,
:math:`N_{\mathrm{species}}` is the number of selected species, :math:`n_{I}`
is the number of atoms of species :math:`I`, :math:`\omega_{I}` the weight
for species :math:`I` (see Section :ref:`target_CN` for more details)
and :math:`{\rho_{I}( {q,k\cdot\Delta t})}`. The overbar
:math:`{\overline{...}}^{q}` in Eq. :math:numref:`pfx80` denotes an average
over :math:`q`-vectors having *approximately* the same modulus

**Fourier-Transformed Particle Density:** Below defines
the Fourier-transformed particle density for species :math:`I`:

.. math::
   :label: pfx83

   {\rho_{I}{\left( {q,k\cdot\Delta t} \right) = \sum\limits_{\alpha}^{n_{I}}}\exp\left\lbrack {\mathit{iq}\cdot R_{\alpha}\left( {k\cdot\Delta t} \right)} \right\rbrack.}


**q-Vectors on a Reciprocal Lattice:** Below describes the selection of q-vectors on a lattice reciprocal to the MD box lattice.

.. math::
   :label: pfx85
   
   {{q_{m} = {q_{\mathit{\min}} + m}}\cdot\Delta q}


The particle density must not change if jumps in the particle
trajectories due to periodic boundary conditions occur. In addition, the
*average* particle density, :math:`N/V` , must not change. 

**Position Vector in the MD Cell** This can be achieved by choosing :math:`q`-vectors on a
lattice which is reciprocal to the lattice defined by the *MD* box. Let
:math:`b_1`, :math:`b_2`, :math:`b_3` be the basis vectors
which span the *MD* cell. Any position vector in the *MD* cell can be
written as

.. math::
   :label: pfx86

   {{R = x^{'}}{b_{1} + y^{'}}{b_{2} + z^{'}}b_{3},}

Eq. :math:numref:`pfx86` defines the position vector in the MD cell.

**Dual Basis Vectors:** with :math:`x'`, :math:`y'`, :math:`z'` having
values between :math:`0` and :math:`1` if :math:`R` is in the unit cell.
The primes indicate that the coordinates are box coordinates. A jump due
to periodic boundary conditions can cause :math:`x'`, :math:`y'`,
:math:`z'` to jump by :math:`\pm1`. The set of dual basis
vectors :math:`b^1`, :math:`b^2`, :math:`b^3` is defined by
the relation

.. math::
   :label: pfx87

   {b_{i}{b^{j} = \delta_{i}^{j}}.}

Eq. :math:numref:`pfx87` defines the dual basis vectors and
their relation to the basis vectors.

**Selection of q-Vectors with Phase Changes:** If the q-vectors are now chosen as

.. math::
   :label: pfx88

   {{q = 2}\pi\left( {k{b^{1} + l}{b^{2} + m}b^{3}} \right),}

Describes the selection of :math:`q`-vectors with phase changes for
handling jumps in particle trajectories

where :math:`k`, :math:`l`, :math:`m` are integer numbers, jumps in the particle trajectories
produce phase changes of multiples of :math:`2\pi` in the Fourier transformed
particle density, i.e. leave it unchanged. One can define a grid of
:math:`q`-shells or a grid of :math:`q`-vectors along a given direction or on a
given plane, giving in addition a *tolerance* for :math:`q`. *MDANSE* looks
then for :math:`q`-vectors of the form given in Eq. :math:numref:`pfx88` whose moduli
deviate within the prescribed tolerance from the equidistant :math:`q`-grid.
From these :math:`q`-vectors only a maximum number per grid-point (called
generically :math:`q`-shell also in the anisotropic case) is kept.

**Negative Coherent Scattering Lengths:** The :math:`q`-vectors can be generated isotropically, anisotropically or along
user-defined directions. The :math:`\sqrt{\omega_{I}}` may be negative
if they represent normalized coherent scattering
lengths, i.e.

.. math::
   :label: pfx89

   {{\sqrt{\omega_{I}} = \frac{b_{I,\text{coh}}}{\sqrt{\sum\limits_{I = 1}^{N_{\mathrm{species}}}{n_{I}b_{I,\text{coh}}^{2}}}}}.}

Defines the use of negative coherent scattering lengths for hydrogenous materials.
Negative coherent scattering lengths occur in hydrogenous materials
since :math:`b_{\mathrm{coh},H}` is negative [Ref20]_.

When the default value of weights (:math:`b_{\mathrm{coherent}}`) is chosen for this
analysis, the result will correspond to that of the equation :math:numref:`ntdsf-eq6`
from the :ref:`analysis-ndtsf`.

.. _dynamic-incoherent-structure-factor:

Dynamic Incoherent Structure Factor
'''''''''''''''''''''''''''''''''''
                      
In this analysis, *MDANSE* proceeds in two steps. First, it computes
the partial and total intermediate incoherent scattering function
:math:`F_{\mathrm{inc}}(q, t)` using equation :math:numref:`pfx70`. Then, the
partial and total dynamic incoherent structure factors are obtained by
performing the Fourier Transformation, defined in Eq. :math:numref:`pfx61`,
respectively on the total and partial intermediate incoherent
scattering function.

**Computation of Incoherent Intermediate Scattering Function:** *MDANSE* computes the incoherent intermediate scattering function on a
rectangular grid of equidistantly spaced points along the time-and the
:math:`q`-axis, respectively:

.. math::
   :label: pfx90

   {\text{F}_{\text{inc}}\left( {q_{m},k\cdot\Delta t} \right)\doteq{\sum\limits_{I = 1}^{N_{\mathrm{species}}}{n_{I}\omega_{I,\text{inc}}}}\text{F}_{I,\text{inc}}\left( {q_{m},k\cdot\Delta t} \right)}


where :math:`{k = 0}, \ldots, {N_{t} - 1}` and :math:`{m = 0}, \ldots, {N_{q} - 1}`. :math:`N_t`
is the number of time steps in the coordinate time series, :math:`N_q`
is a user-defined number of :math:`q`-shells, :math:`N_{\mathrm{species}}`
is the number of selected species, :math:`n_I` the
number of atoms of species :math:`n_I`, :math:`\omega_{I}` the weight for species :math:`I`
(see Section :ref:`target_CN` for more details) and :math:`{F_{I,\text{inc}}\left( {q_{m},k\cdot\Delta t} \right)}`
is defined as:

.. math::
   :label: pfx92

   {\text{F}_{I,\mathrm{inc}}{\left( {q_{m},k\cdot\Delta t} \right) = \sum\limits_{\alpha = 1}^{n_{I}}}{\overline{\left\langle {\exp\left\lbrack {{-i}q\cdot R_{\alpha}(0)} \right\rbrack\exp\left\lbrack {iq\cdot R_{\alpha}(t)} \right\rbrack} \right\rangle}}^{q}.}

The overbar :math:`{\overline{...}}^{q}` in Eq. :math:numref:`pfx92`
denotes an average
over :math:`q`-vectors having *approximately* the same modulus
:math:`{{q_{m} = {q_{\mathit{\min}} + m}}\cdot\Delta q}`. The
particle density must not change if jumps in the particle
trajectories due to periodic boundary conditions occur. 


**Selection of q-Vectors on a Reciprocal Lattice:** In addition, the
*average* particle density, :math:`N/V`, must not change. This can be achieved
by choosing :math:`q`-vectors on a lattice which is reciprocal to the lattice
defined by the *MD* box. Let :math:`b_1`, :math:`b_2`,
:math:`b_3` be the basis vectors which span the *MD* cell. Any
position vector in the *MD* cell can be written as

.. math::
   :label: pfx94

   {{R = x^{'}}{b_{1} + y^{'}}{b_{2} + z^{'}}b_{3},}

with :math:`x'`, :math:`y'`, :math:`z'` having values between :math:`0` and :math:`1`
if :math:`R` is in the unit cell. The primes indicate that
the coordinates are box coordinates. A jump due to periodic boundary
conditions causes :math:`x'`, :math:`y'`, :math:`z'` to jump by :math:`\pm 1`.
The set of dual basis vectors :math:`b^1`, :math:`b^2`, :math:`b^3` is defined by
the relation

.. math::
   :label: pfx95

   {b_{i}{b^{j} = \delta_{i}^{j}}.}

If the :math:`q`-vectors are now chosen as

.. math::
   :label: pfx96

   {{q = 2}\pi\left( {k{b^{1} + l}{b^{2} + m}b^{3}} \right),}

where :math:`k`, :math:`l`, :math:`m`,  are integer numbers, jumps in the particle trajectories
produce phase changes of multiples of :math:`2\pi` in the Fourier transformed
particle density, i.e. leave it unchanged. One can define a grid of
:math:`q`-shells or a grid of :math:`q`-vectors along a given direction or on a
given plane, giving in addition a *tolerance* for :math:`q`. *MDANSE* looks
then for :math:`q`-vectors of the form given in Eq. :math:numref:`pfx96` whose moduli
deviate within the prescribed tolerance from the equidistant :math:`q`-grid.
From these :math:`q`-vectors only a maximum number per grid-point (called
generically :math:`q`-shell also in the anisotropic case) is kept.
The :math:`q`-vectors can be generated isotropically, anisotropically or along
user-defined directions.

When the default value of weights (:math:`{b^{2}}_{\mathrm{incoherent}}`) is chosen for this
analysis, the result will correspond to that of the equation :math:numref:`ntdsf-eq7`
from the :ref:`analysis-ndtsf`.

.. _elastic-incoherent-structure-factor:

Elastic Incoherent Structure Factor
'''''''''''''''''''''''''''''''''''

The *EISF* appears as the amplitude of the *elastic* line in the neutron
scattering spectrum. Elastic scattering is only present for systems in which the
atomic motion is confined in space, as for solids. To understand which information
is contained in the *EISF* we consider for simplicity a system where only one
sort of atoms is visible to the neutrons. To a very good approximation this is
the case for all systems containing a large amount of hydrogen atoms, as biological
systems. Incoherent scattering from hydrogen dominates by far all other
contributions.

**Van Hove Self-correlation Function:** The Elastic Incoherent Structure
Factor (*EISF*) is defined as the limit of the incoherent intermediate
scattering function for infinite time,

.. math::
   :label: pfx97

   {\mathrm{EISF}(q)\doteq\lim\limits_{t\rightarrow\infty}\text{F}_{\mathrm{inc}}\left( {q,t} \right).}

Using the above definition of the *EISF* one can decompose the incoherent
intermediate scattering function as follows:

.. math::
   :label: pfx98

   {\text{F}_{\text{inc}}{\left( {q,t} \right) = \mathrm{EISF}}{(q) + \text{F}_{\text{inc}}^{'}}\left( {q,t} \right),}

where :math:`F^{'}_{\mathrm{inc}}(q, t)` decays to zero for infinite time. Taking
now the Fourier transform it follows immediately that

.. math::
   :label: pfx99

   {\text{S}_{\text{inc}}{\left( {q,\omega} \right) = \mathrm{EISF}}(q)\delta{(\omega) + \text{S}_{\text{inc}}^{'}}\left( {q,\omega} \right).}

The *EISF* appears as the amplitude of the *elastic* line in the neutron
scattering spectrum. Elastic scattering is only present for systems in
which the atomic motion is confined in space, as for solids. To
understand which information is contained in the *EISF* we consider for
simplicity a system where only one sort of atoms is visible to the
neutrons. To a very good approximation this is the case for all systems
containing a large amount of hydrogen atoms, as biological systems.
Incoherent scattering from hydrogen dominates by far all other
contributions. Using the definition of the van Hove self-correlation
function :math:`G_{\mathrm{s}}(r, t)` [Ref20]_,

.. math::
   :label: pfx100

   {b_{\text{inc}}^{2}G_{\mathrm{s}}\left( {r,t} \right)\doteq\frac{1}{2\pi^{3}}{\int d^{3}}q\exp\left\lbrack {{- i}q\cdot r} \right\rbrack\text{F}_{\mathrm{inc}}\left( {q,t} \right),}

which can be interpreted as the conditional probability to find a tagged
particle at the position :math:`r` at time :math:`t`, given it started at :math:`r = 0`,
one can write:

.. math::
   :label: pfx101

   {\mathrm{EISF}(q) = b_{\text{inc}}^{2}{\int d^{3}}r\exp\left\lbrack {\mathit{iq}\cdot r} \right\rbrack G_{\mathrm{s}}\left( {r,{t = \infty}} \right).}

The *EISF* gives the sampling distribution of the points in space in the
limit of infinite time. In a real experiment this means times longer
than the time which is observable with a given instrument. The *EISF*
vanishes for all systems in which the particles can access an infinite
volume since :math:`G_{\mathrm{s}}(r, t)` approaches :math:`1/V` for large times. This is
the case for molecules in liquids and gases.

**EISF Computation:** For computational purposes it is convenient to use the following
representation of the *EISF* [Ref21]_:

.. math::
   :label: pfx102

   {\mathrm{EISF}{(q) = {\sum\limits_{I = 1}^{N_{\mathrm{species}}}{n_{I}\omega_{I,\text{inc}}\mathrm{EISF}_{I}(q)}}}}

where :math:`N_{\mathrm{species}}` is the number of selected species, :math:`n_I`
the number of atoms of species :math:`I`, :math:`\omega_{I,\mathrm{inc}}` the weight for
species :math:`I` (see Section :ref:`target_CN` for more details) and for each species the
following expression for the elastic incoherent scattering function is

.. math::
   :label: pfx103

   {\mathrm{EISF}_{I}{(q) = \frac{1}{n_{I}}}{\sum\limits_{\alpha}^{n_{I}}\left\langle {|{\exp\left\lbrack {\mathit{iq}\cdot R_{\alpha}} \right\rbrack\left. {} \right|^{2}}} \right\rangle}.}

This expression is derived from definition :math:numref:`pfx97`
of the *EISF* and expression :math:numref:`pfx70` for the
intermediate scattering function, using that for infinite time the
relation

.. math::
   :label: pfx104
   
   {\left\langle {\exp\left\lbrack {{- \mathit{iq}}\cdot R_{\alpha}(0)} \right\rbrack\exp\left\lbrack {\mathit{iq}\cdot R_{\alpha}(t)} \right\rbrack} \right\rangle = \left\langle {|{\exp\left\lbrack {\mathit{iq}\cdot R_{\alpha}} \right\rbrack\left. {} \right|^{2}}} \right\rangle}

holds. In this way the computation of the *EISF* is reduced to the
computation of a static thermal average. We remark at this point that
the length of the *MD* trajectory from which the *EISF* is computed
should be long enough to allow for a representative sampling of the
conformational space.

**Grid Computation:** *MDANSE* allows one to compute the elastic incoherent structure factor
on a grid of equidistantly spaced points along the *q*-axis:

.. math::
   :label: pfx105

   {\mathrm{EISF}\left( q_{m} \right)\doteq{\sum\limits_{I = 1}^{N_{\mathit{species}}}{n_{I}\omega_{I}\mathrm{EISF}_{I}\left( q_{m} \right)}} \qquad {m = 0}, \ldots, {N_{q} - 1.}}

where :math:`N_q` is a user-defined number of :math:`q`-shells, the values for
:math:`q_m` are defined as

.. math::
   :label: pfx106
   
   {{q_{m} = {q_{\mathit{\min}} + m}}\cdot\Delta q}

and for each species the following expression for the elastic
incoherent scattering function is:

.. math::
   :label: pfx107

   {\mathrm{EISF}_{I}{\left( q_{m} \right) = \frac{1}{n_{I}}}{\sum\limits_{\alpha}^{n_{I}}{\overline{\left\langle {|{\exp\left\lbrack {\mathit{iq}\cdot R_{\alpha}} \right\rbrack\left. {} \right|^{2}}} \right\rangle}}^{q}}.}

Here the symbol :math:`{\overline{...}}^{q}`
denotes an average over the *q*-vectors having the same modulus
:math:`q_m`. The program corrects the atomic input trajectories for
jumps due to periodic boundary conditions.

.. _gaussian-dynamic-incoherent-structure-factor:

Gaussian Dynamic Incoherent Structure Factor
''''''''''''''''''''''''''''''''''''''''''''
                      
The Gaussian Dynamic Incoherent Structure Factor is a concept used to study how
particles or atoms move independently within materials over time, with a focus
on their distribution. It's valuable in materials science and condensed matter
physics for understanding dynamic behavior at the atomic level.

**MSD Calculation:** The *MSD* can be related to the incoherent intermediate scattering
function via the cumulant expansion [Ref11]_, [Ref22]_

.. math::
   :label: pfx108

   {\text{F}_{\text{inc}}^{\mathrm{g}}{\left( {q,t} \right) = {\sum\limits_{I = 1}^{N_{\mathrm{species}}}{n_{I}\omega_{I,\text{inc}}}}}\text{F}_{I,\text{inc}}^{\mathrm{g}}\left( {q,t} \right)}

where :math:`N_{\mathrm{species}}` is the number of selected species, :math:`n_I`
the number of atoms of species :math:`I`, :math:`\omega_{I,\mathrm{inc}}` the weight for
species \mathrm{I} (see Section :ref:`target_CN` for more details) and

.. math::
   :label: pfx109

   {\text{F}_{I,\text{inc}}^{\mathrm{g}}{\left( {q,t} \right) = \frac{1}{n_{I}}}\sum\limits_{\alpha}^{n_{I}}\exp\left\lbrack {{- q^{2}}\rho_{\alpha,1}{(t) + q^{4}}\rho_{\alpha,2}(t)\mp\ldots} \right\rbrack.}


The cumulants :math:`\rho_{\alpha,k}(t)` are identified as

.. math::

   {\rho_{\alpha,1}{(t) = \left\langle {d_{\alpha}^{2}\left( {t;n_{q}} \right)} \right\rangle}}

.. math::

   {\rho_{\alpha,2}{(t) = \frac{1}{4!}}\left\lbrack {{\left\langle {d_{\alpha}^{4}\left( {t;n_{q}} \right)} \right\rangle - 3}\left\langle {d_{\alpha}^{2}\left( {t;n_{q}} \right)} \right\rangle^{2}} \right\rbrack}

.. math::
   :label: pfx112
   {\vdots}

**Gaussian Approximation:** The vector :math:`nq` is the unit vector
in the direction of :math:`q`. In the Gaussian
approximation the above expansion is truncated after the
:math:`q^2`-term. For certain model systems like the ideal gas, the
harmonic oscillator, and a particle undergoing Einstein diffusion, this
is exact. For these systems the incoherent intermediate scattering
function is completely determined by the *MSD*. *MDANSE* allows one to
compute the total and partial incoherent intermediate scattering
function in the *Gaussian approximation* by discretizing equation
:math:numref:`pfx108`:

.. math::
   :label: pfx113

   {\text{F}_{\text{inc}}^{\mathrm{g}}\left( {q_{m},k\cdot\Delta t} \right)\doteq{\sum\limits_{I = 1}^{N_{\mathit{species}}}{n_{I}\omega_{I,\text{inc}}\text{F}_{I,\text{inc}}^{\mathrm{g}}\left( {q_{m},k\cdot\Delta t} \right)}}}

where :math:`{k = 0}\ldots{N_{t} - 1}` and :math:`{m = 0}\ldots{N_{q} - 1}`.

**Intermediate Scattering Function:** for each species the
following expression for the intermediate scattering function

.. math::
   :label: pfx114

   {\text{F}_{I,\alpha,\text{inc}}^{\mathrm{g}}{\left( {q_{m},k\cdot\Delta t} \right) = \frac{1}{n_{I}}}\sum\limits_{\alpha}^{n_{I}}\exp\left\lbrack {\frac{- \left( q_{m} \right)^{2}}{6}\Delta_{\alpha}^{2}\left( {k\cdot\Delta t} \right)} \right\rbrack \quad \mathrm{isotropic\ system}}

.. math::
   :label: pfx115

   {\text{F}_{I,\alpha,\text{inc}}^{\mathrm{g}}{\left( {q_{m},k\cdot\Delta t} \right) = \frac{1}{n_{I}}}\sum\limits_{\alpha}^{n_{I}}\exp\left\lbrack {\frac{- \left( q_{m} \right)^{2}}{2}\Delta_{\alpha}^{2}\left( {k\cdot\Delta t;n} \right)} \right\rbrack \quad \mathrm{isotropic\ system}}

:math:`N_t` is the total number of time steps in the coordinate time
series and :math:`N_q` is a user-defined number of :math:`q`-shells. The (:math:`q`,
:math:`t`)-grid is the same as for the calculation of the intermediate
incoherent scattering function (see `Dynamic Incoherent Structure
Factor <#_Dynamic_Incoherent_Structure>`__). The quantities :math:`\Delta_{\alpha}^{2}(t)`
and :math:`\Delta_{\alpha}^{2}\left( {t;n} \right)` are the mean-square
displacements, defined in Equations :math:numref:`pfx14`
and :math:numref:`pfx15`, respectively.
They are computed by using the algorithm described in the `Mean Square
Displacement <#_Theory_and_implementation_2>`__ section. *MDANSE*
corrects the atomic input trajectories for jumps due to periodic
boundary conditions. It should be noted that the computation of the
intermediate scattering function in the Gaussian approximation is much
'cheaper' than the computation of the full intermediate scattering
function, :math:`F_{\mathrm{inc}}(q, t)`, since no averaging over different
:math:`q`-vectors needs to be performed. It is sufficient to compute a single
mean-square displacement per atom.

.. _neutron-dynamic-total-structure-factor:

Neutron Dynamic Total Structure Factor
''''''''''''''''''''''''''''''''''''''

The Neutron Dynamic Total Structure Factor is a term used in scientific
research, especially in neutron scattering experiments, to investigate how
particles or atoms within a material contribute to its overall structure and
dynamics. This factor provides valuable insights into how these components move
and interact over time.

**Calculation of Partial Coherent Intermediate Scattering Functions and Dynamic Structure Factors:**
this is a combination of the dynamic coherent and the dynamic incoherent
structure factors. It is a fully neutron-specific analysis, where the
coherent part of the intermediate scattering function is calculated
using the atomic coherent neutron scattering lengths
:math:`b_{\mathrm{coherent}}` and
the incoherent one is calculated using the square of the atomic
incoherent neutron scattering lengths :math:`{b^{2}}_{\mathrm{incoherent}}`. Therefore, in
this analysis the weights option is not available.

The partial coherent intermediate scattering functions
:math:`I_{\alpha\beta}^{\mathrm{coh}}(Q,t)` (and their corresponding Fourier
transforms giving the partial coherent dynamic structure factors,
:math:`S_{\alpha\beta}^{\mathrm{coh}}(Q,\omega)`) are calculated exactly in the
same way as in the DCSF analysis, i.e.:

.. math::
   :label: ntdsf-eq1
   
   I_{\alpha\beta}^{\mathrm{coh}}(Q,t) = \left| \frac{1}{\sqrt{N_{\alpha}N_{\beta}}}\sum_{i \in \alpha,j \in \beta}^{N_{\alpha},N_{\beta}}\left\langle e^{- i\mathbf{Q}\mathbf{r}_{i}(t_{0})}e^{i\mathbf{Q}\mathbf{r}_{j}(t_{0} + t)} \right\rangle \right|_{\mathbf{Q}}

where :math:`\alpha` and :math:`\beta` refer to the chemical elements,
:math:`N_{\alpha}` and :math:`N_{\beta}` are the respective number of
atoms of each type, :math:`i` and :math:`j` are two specific atoms of
type :math:`\alpha` and :math:`\beta`, respectively, and
:math:`\mathbf{r}_{i}(0)` and :math:`\mathbf{r}_{j}(t)` are their
positions at the time origin and at the time :math:`t`, respectively.
The notation :math:`\left\langle \ldots \right\rangle` indicates an
average over all possible time origins :math:`t_{0}` and
:math:`|\ldots|_{\mathbf{Q}}` represents an average over all the
:math:`\mathbf{Q}` vectors contributing to the corresponding
:math:`Q`-bin.

Similarly, the partial incoherent intermediate scattering functions
:math:`I_{\alpha}^{\mathrm{inc}}(Q,t)` and the partial incoherent dynamic
structure factors :math:`S_{\alpha}^{\mathrm{inc}}(Q,\omega)` are obtained as in
the DISF analysis:

.. math::
   :label: ntdsf-eq2
   
   I_{\alpha}^{\mathrm{inc}}(Q,t) = \left| \frac{1}{N_{\alpha}}\sum_{i \in \alpha}^{N_{\alpha}}\left\langle e^{- i\mathbf{Q}\mathbf{r}_{i}(t_{0})}e^{i\mathbf{Q}\mathbf{r}_{i}(t_{0} + t)} \right\rangle \right|_{\mathbf{Q}}


**Combination of Partial Contributions:** The main difference between
this analysis and the DCSF and DISF
analyses, apart from the fact that the coherent and incoherent
contributions are calculated simultaneously, is the way the different
partial contributions are combined. In this analysis the total
incoherent, total coherent and total (coherent + incoherent) signals are
calculated as:

.. math::
   :label: ntdsf-eq3
   
   I^{\mathrm{inc}}(Q,t) = \sum_{\alpha}^{N_{\alpha}}{c_{\alpha}b_{\alpha,\text{inc}}^{2}}I_{\alpha}^{\mathrm{inc}}(Q,t)

.. math::
   :label: ntdsf-eq4
   
   I^{\mathrm{coh}}(Q,t) = \sum_{\alpha,\beta}^{N_{\alpha},N_{\beta}}{\sqrt{c_{\alpha}c_{\beta}}b_{\alpha,\text{coh}}b_{\beta,\text{coh}}I_{\alpha\beta}^{\mathrm{coh}}(Q,t)}

.. math::
   :label: ntdsf-eq5
   
   I^{\mathrm{tot}}(Q,t) = I^{\mathrm{inc}}(Q,t) + I^{\mathrm{coh}}(Q,t)

where :math:`c_{\alpha} = N_{\alpha} / N` and
:math:`c_{\beta} =  N_{\beta} / N` are the concentration numbers
for elements :math:`\alpha` and :math:`\beta`, respectively.

These expressions correspond to the formalism and equations given in
[Ref47]_, chapter 1: “An introduction to neutron scattering” .

**Units Conversion:**
As in the MDANSE database the coherent and incoherent neutron scattering
lengths are given in Å, the total intermediate scattering functions
above will be given in Å\ :sup:`2`/sterad/atom. Therefore, multiplying
the output from MDANSE by a factor 10\ :sup:`8` we can obtain these
neutron observables in barn/sterad/atom and compare them directly to the
experimental results (assuming the later have been properly normalized
and presented in absolute units).

On the other hand, the DISF and DCSF analyses use the standard weight
normalization procedure implemented in MDANSE (see :ref:`param-normalize`).
Therefore the total coherent intermediate scattering function
returned by the DCSF analysis is (assuming that the chosen weights are
b_coherent):

.. math::
   :label: ntdsf-eq6
   
   I^{\mathrm{coh}}(Q,t) = \frac{\sum_{\alpha\beta}^{n}{c_{\alpha}c_{\beta}b_{\alpha,\mathrm{coh}}b_{\beta,\mathrm{coh}}I_{\alpha\beta}^{\mathrm{coh}}(Q,t)}}{\sum_{\alpha\beta}^{n}{c_{\alpha}c_{\beta}b_{\alpha,\mathrm{coh}}b_{\beta,\mathrm{coh}}}}

and the incoherent intermedicate scattering function given by the DISF
analysis is (assuming that the chosen weights are b_incoherent2):

.. math::
   :label: ntdsf-eq7
   
   I^{\mathrm{inc}}(Q,t) = \frac{\sum_{\alpha}^{n}{c_{\alpha}b_{\alpha,\mathrm{inc}}^{2}I_{\alpha}^{\mathrm{inc}}(Q,t)}}{\sum_{\alpha}^{n}{c_{\alpha}b_{\alpha,\mathrm{inc}}^{2}}}

Naturally, similar expressions apply to the dynamic structure factors,
:math:`S_{\alpha\beta}^{\mathrm{coh}}(Q,\omega)` and
:math:`S_{\alpha}^{\mathrm{inc}}(Q,\omega)`.

.. _structure-factor-from-scattering-function:

Structure Factor From Scattering Function
'''''''''''''''''''''''''''''''''''''''''
The "Structure Factor From Scattering Function" is a concept used in
scientific research, particularly in the field of neutron scattering
experiments. It relates to how particles or atoms within a material
contribute to its overall structural properties based on their scattering
behavior. This concept provides valuable insights into the material's
internal structure, dynamics, and interactions. Researchers use the Structure
Factor From Scattering Function to better understand the atomic-level details
of materials, which has applications in diverse areas, including materials
science and condensed matter physics
