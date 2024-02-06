
This section is dealing with specific types of analysis performed by
MDANSE. If you are not sure where these fit into the general workflow
of data analysis, please read :ref:`workflow-of-analysis`.

Analysis: Scattering
====================

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
**Dynamic Structure Factor (S(q, ω)):** S(**q**, :math:`\omega`) is a central
concept in neutron scattering experiments. This factor characterizes how
scattering intensity changes with alterations in momentum (q) and energy (ω)
during scattering events. It is instrumental in unraveling the atomic and
molecular structures of materials.

**Double Differential Cross-Section:** (S(q, ω) is closely related to the
Double Differential Cross-Section[7], which is a vital measurement in neutron
scattering. The double differential cross-section is defined as the number of
neutrons scattered per unit time into the solid angle interval
:math:`{\left\lbrack {\Omega,{\Omega + d}\Omega} \right\rbrack}` and into the
energy interval (energy interval E). :math:`{d^{2}{\sigma/\mathit{d\Omega
dE}}}`. To make meaningful comparisons, the double differential cross-section
is normalized by d, dE, and the flux of the incoming neutrons. The relationship
between the double differential cross-section and the dynamic structure factor
is given by:

.. math::
   :label: pfx55

   {{\frac{d^{2}\sigma}{d\Omega\mathit{dE}} = N}\cdot\frac{k}{k_{0}}S\left( {q,\omega} \right).}

This equation relates the double differential cross-section, which represents
the number of neutrons scattered per unit time into specific solid angle and
energy intervals, to the dynamic structure factor, S(q, ω). It includes terms
related to the number of atoms (N) and wave numbers of scattered (k) and
incident (k0) neutrons.

They are related to the corresponding neutron energies by

.. math::
   :label: pfx56
   
   {E = \hslash^{2}}k^{2}\text{/}2m

\ and

.. math::
   :label: pfx57
   
   {E_{0} = \hslash^{2}}k_{0}^{2}\text{/}2m


These equations relate the neutron energies (E and E0) to their respective wave
numbers (k and k0) using the mass of the neutron (m). They are fundamental for
connecting energy and momentum in neutron scattering.

**Dimensionless Momentum and Energy Transfer:** These equations below define the
dimensionless momentum (q, dynamic structure factor) and energy (ω) transfer in
units of the reduced Planck constant (ħ) based on the incident and scattered
wave numbers and energies:

.. math::
   :label: pfx58

   {{q = \frac{k_{0} - k}{\hslash}},}

.. math::
   :label: pfx59

   {{\omega = \frac{E_{0} - E}{\hslash}}.}

Then, Expresses the modulus of the momentum transfer in terms of scattering
angle, energy transfer, and incident neutron energy. See equations below:

.. math::
   :label: pfx60

   {{q = \sqrt{{2 - \frac{\mathit{\hslash\omega}}{E_{0}} - 2}\cos{\theta\sqrt{2 - \frac{\mathit{\hslash\omega}}{E_{0}}}}}}.}



**Intermediate Scattering Function (F(q, t)):**

This equation defines the dynamic structure factor (S(q, ω)) as a Fourier
transform of the intermediate scattering function (F(q, t)) with respect to
time (t). It captures information about the structure and dynamics of the
scattering system [Ref16]_. It can be written as:

.. math::
   :label: pfx61

   {S{\left( {q,\omega} \right) = \frac{1}{2\pi}}{\int\limits_{- \infty}^{+ \infty}\mathit{dt}}\exp\left\lbrack {{- i}\omega t} \right\rbrack F\left( {q,t} \right).}

F(**q**, t) is called the *intermediate scattering function* and is defined as

.. math::
   :label: pfx62

   {\text{F}{\left( {q,t} \right) = {\sum\limits_{\alpha,\beta}{\Gamma_{\mathit{\alpha\beta}}\left\langle {\exp\left\lbrack {{- i}q\cdot\hat{R_{\alpha}}(0)} \right\rbrack\exp\left\lbrack {iq\cdot\hat{R_{\beta}}(t)} \right\rbrack} \right\rangle}}},}

.. math::
   :label: pfx63

   {{\Gamma_{\mathit{\alpha\beta}} = \frac{1}{N}}\left\lbrack {\overline{b_{\alpha}}{\overline{b_{\beta}} + \delta_{\mathit{\alpha\beta}}}\left( {\overline{b_{\alpha}^{2}} - {\overline{b_{\alpha}}}^{2}} \right)} \right\rbrack.}

The operators :math:`\hat{R_{\alpha}}(t)`
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
The symbol :math:`\overline{...}` appearing in :math:`{\Gamma_{\mathit{\alpha\beta}}}`
denotes an average over isotopes and relative spin orientations of
neutron and nucleus.

**Coherent and Incoherent Scattering:**
Usually, one splits the intermediate scattering function and the dynamic
structure factor into their *coherent* and *incoherent* parts which
describe collective and single particle motions, respectively. Defining

.. math::
   :label: pfx65

   {b_{\alpha,\mathit{coh}}\doteq\overline{b_{\alpha}},}

.. math::
   :label: pfx66

   {b_{\alpha,\mathit{inc}}\doteq\sqrt{\overline{b_{\alpha}^{2}} - {\overline{b_{\alpha}}}^{2}},}

the coherent and incoherent intermediate scattering functions can be
cast in the form. They are expressed as sums over pairs of nuclei, with different treatments for coherent and incoherent scattering lengths.

.. math::
   :label: pfx67

   {\text{F}_{\text{coh}}{\left( {q,t} \right) = \frac{1}{N}}{\sum\limits_{\alpha,\beta}b_{\alpha,\mathit{coh}}}b_{\beta,\mathit{coh}}\left\langle {\exp\left\lbrack {{- i}q\cdot\hat{R_{\alpha}}(0)} \right\rbrack\exp\left\lbrack {iq\cdot\hat{R_{\beta}}(t)} \right\rbrack} \right\rangle,}

.. math::
   :label: pfx68

   {\text{F}_{\text{inc}}{\left( {q,t} \right) = \frac{1}{N}}{\sum\limits_{\alpha}{b_{\alpha,\mathit{inc}}^{2}\left\langle {\exp\left\lbrack {{- i}q\cdot\hat{R_{\alpha}}(0)} \right\rbrack\exp\left\lbrack {iq\cdot\hat{R_{\alpha}}(t)} \right\rbrack} \right\rangle}}.}

Rewriting these formulas, *MDANSE* introduces the partial terms, this consider different species (I, J) and their contributions to the scattering process.

.. math::
   :label: pfx69

   {\text{F}_{\text{coh}}{\left( {q,t} \right) = \sum\limits_{I,J\geq I}^{N_{\mathit{species}}}}\sqrt{n_{I}n_{J}\omega_{I,\text{coh}}\omega_{J,\text{coh}}}F_{\mathit{IJ},\text{coh}}\left( {q,t} \right),}

.. math::
   :label: pfx70

   {\text{F}_{\text{inc}}{\left( {q,t} \right) = {\sum\limits_{I = 1}^{N_{\mathit{species}}}{n_{I}\omega_{I,\text{inc}}F_{I,\text{inc}}\left( {q,t} \right)}}}}

where:

.. math::
   :label: pfx71

   {\text{F}_{\mathit{IJ},\text{coh}}{\left( {q,t} \right) = \frac{1}{\sqrt{n_{I}n_{J}}}}{\sum\limits_{\alpha}^{n_{I}}{\sum\limits_{\beta}^{n_{J}}\left\langle {\exp\left\lbrack {{- i}q\cdot\hat{R_{\alpha}}\left( t_{0} \right)} \right\rbrack\exp\left\lbrack {iq\cdot\hat{R_{\beta}}\left( {t_{0} + t} \right)} \right\rbrack} \right\rangle_{t_{0}}}},}

.. math::
   :label: pfx72

   {\text{F}_{I,\text{inc}}{\left( {q,t} \right) = \frac{1}{n_{I}}}{\sum\limits_{\alpha = 1}^{n_{I}}\left\langle {\exp\left\lbrack {{- i}q\cdot\hat{R_{\alpha}}\left( t_{0} \right)} \right\rbrack\exp\left\lbrack {iq\cdot\hat{R_{\alpha}}\left( {t_{0} + t} \right)} \right\rbrack} \right\rangle_{t_{0}}}.}

where n\ :sub:`I`, n\ :sub:`J`, N\ :sub:`species`, :math:`\omega`\ :sub:`I,coh,inc`
and :math:`\omega`\ :sub:`J,coh,inc` are defined in Section :ref:`target_CN`.

The corresponding dynamic structure factors are obtained by performing
the Fourier transformation defined in Eq. :math:numref:`pfx61`.

**Static Structure Factor (S(q)):**
An important quantity describing structural properties of liquids is the static structure factor, which is defined above. (S(q)) as an integral involving the dynamic structure factor and the coherent intermediate scattering function at zero time delay (t = 0).

.. math::
   :label: pfx73

   {\text{S}(q)\doteq{\int\limits_{- \infty}^{+ \infty}{d\omega}}\text{S}_{\mathit{coh}}\left( {q,\omega} \right)\text{F}_{\mathit{coh}}\left( {q,0} \right).}

**Classical Framework and Corrections:**
In the classical framework the intermediate scattering functions are
interpreted as classical time correlation functions. The position
operators are replaced by time-dependent vector functions and quantum
thermal averages are replaced by classical *ensemble averages*. It is
well known that this procedure leads to a loss of the universal detailed
balance relation,

.. math::
   :label: pfx74

   {\text{S}{\left( {q,\omega} \right) = \exp}\left\lbrack {\beta\hslash\omega} \right\rbrack\text{S}\left( {{- q}{, - \omega}} \right),}

and also to a loss of all odd moments

.. math::
   :label: pfx75

   {\left\langle \omega^{2{n + 1}} \right\rangle\doteq{\int\limits_{- \infty}^{+ \infty}{d\omega}}\omega^{2{n + 1}}S\left( {q,\omega} \right),{n = 1,2},\ldots.}

The odd moments vanish since the classical dynamic structure factor is
even in :math:`\omega`, assuming invariance of the scattering process with respect to
reflections in space. The first moment is also universal. For an atomic
liquid, containing only one sort of atoms, it reads

.. math::
   :label: pfx76

   {{\left\langle \omega \right\rangle = \frac{\hslash q^{2}}{2M}},}

where M is the mass of the atoms. 

**Recoil Moment:** Formula :math:numref:`pfx76` shows that the
first moment is given by the average kinetic energy (in units of
:math:`\hslash`) of a particle which receives a momentum transfer
:math:`\hslash q`. Therefore,
:math:`\langle\omega\rangle`
is called the *recoil moment*. A number of 'recipes' has been suggested
to correct classical dynamic structure factors for detailed balance and
to describe recoil effects in an approximate way. The most popular one
has been suggested by Schofield [Ref17]_

.. math::
   :label: pfx77

   {{\text{S}\left( {q,\omega} \right)\approx\exp\left\lbrack \frac{\beta\hslash\omega}{2} \right\rbrack}_{}\text{S}_{\mathit{cl}}\left( {q,\omega} \right)}

One can easily verify that the resulting dynamic structure factor
fulfils the relation of detailed balance. Formally, the correction :math:numref:`pfx77`
is correct to first order in :math:`\hslash`. Therefore, it cannot be used
for large *q*-values which correspond to large momentum transfers
:math:`\hslash q`. This is actually true for all correction
methods which have suggested
so far. For more details we refer to Ref.
[Ref18]_.

**Total Structure Factors:**

MDANSE computes the partial S(Q)'s as the Fourier transform of the
partial g(r), corresponding to the Faber-Ziman definition:

.. math::
   :label: pfx78
   
   {S_{\alpha\beta}(Q) = 1 + \frac{4\pi\rho_0}{Q}\int\limits_{0}^{\infty}{r\left\lbrack {g_\alpha\beta}(r)-1 \right\rbrack\text{sin}(Qr)dr}}

The total S(Q) is computed as a weighted sum similar to the one used for
the total g(r). In the case of the analysis 'X-ray Static structure
factor', the Q-dependence of the atomic form factors is taken into
account in this weighted sum.

**X-ray Observable Normalization:** Again, Soper has provided experimental data (table 4 in *ISRN Physical
Chemistry*, 279463 (2013), given in file soper13_fx.dat). Here a source
of confusion is that the data can be normalized in different ways (see
Soper's paper). Using the normalization II in that reference we have
that:

.. math::
   :label: pfx79
   
   {D_{x}{(Q) = \frac{\sum\limits_{\mathit{\alpha\beta}\geq\alpha}{\left( {2 - \delta_{\mathit{\alpha\beta}}} \right)\times c_{\alpha}c_{\beta}f_{\alpha}{(Q)}f_{\beta}{(Q)}\left\lbrack {S_{\mathit{\alpha\beta}}{(Q) - 1}} \right\rbrack}}{\sum\limits_{\alpha}{c_{\alpha}f_{\alpha}^{2}{(Q)}}} = \left\lbrack {S{(Q) - 1}} \right\rbrack}\times\frac{\sum\limits_{\mathit{\alpha\beta}}{c_{\alpha}c_{\beta}f_{\alpha}{(Q)}f_{\beta}{(Q)}}}{\sum\limits_{\alpha}{c_{\alpha}f_{\alpha}^{2}{(Q)}}}}

Where S(Q) would be the static structure factor (going to 1 at large Q)
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

**Coherent Intermediate Scattering Function Calculation**
*MDANSE* computes the coherent intermediate scattering function on a
rectangular grid of equidistantly spaced points along the time-and the
q-axis, respectively:

.. math::
   :label: pfx80
   
   {{F}_{\text{coh}}\left( {q_{m},k\cdot\Delta t} \right)\doteq{\sum\limits_{{I = 1},J\geq I}^{N_{\mathit{species}}}\sqrt{n_{I}n_{J}\omega_{I,\text{com}}\omega_{I,\text{com}}}}{\overline{\left\langle {\rho_{I}\left( {{-q},0} \right)\rho_{J}\left( {q,k\cdot\Delta t} \right)} \right\rangle}}^{q},} \\
   {{k = 0}\ldots{N_{t} - 1},{m = 0}\ldots{N_{q} - 1.}}

Equation defines the computation of the coherent intermediate scattering function in terms of particle densities, species, and time steps.

**Fourier-Transformed Particle Density** where N\ :sub:`t` is the number of time steps in the coordinate time
series, N\ :sub:`q` is a user-defined number of *q*-shells,
N\ :sub:`species` is the number of selected species, n\ :sub:`I` the
number of atoms of species *I*, :math:`\omega`\ :sub:`I` the weight for species *I*
(see Section :ref:`target_CN` for more details) and :math:`{\rho_{I}\left( {q,k\cdot\Delta t} \right)}`
Below defines the Fourier-transformed particle density for species I.

.. math::
   :label: pfx83

   {\rho_{I}{\left( {q,k\cdot\Delta t} \right) = \sum\limits_{\alpha}^{n_{I}}}\exp\left\lbrack {\mathit{iq}\cdot R_{\alpha}\left( {k\cdot\Delta t} \right)} \right\rbrack.}

The symbol :math:`{\overline{...}}^{q}` in Eq. :math:numref:`pfx80` denotes an average
over *q*-vectors having *approximately* the same modulus

**q-Vectors on a Reciprocal Lattice ** Below describes the selection of q-vectors on a lattice reciprocal to the MD box lattice.

.. math::
   :label: pfx85
   
   {{q_{m} = {q_{\mathit{\min}} + m}}\cdot\Delta q}


The particle density must not change if jumps in the particle
trajectories due to periodic boundary conditions occur. In addition, the
*average* particle density, :math:`N/V` , must not change. 

**Position Vector in the MD Cell** This can be achieved by choosing *q*-vectors on a
lattice which is reciprocal to the lattice defined by the *MD* box. Let
**b**\ :sub:`1`, **b**\ :sub:`2`, **b**\ :sub:`3` be the basis vectors
which span the *MD* cell. Any position vector in the *MD* cell can be
written as

.. math::
   :label: pfx86

   {{R = x^{'}}{b_{1} + y^{'}}{b_{2} + z^{'}}b_{3},}

Eq defines the position vector in the MD cell.

** Dual Basis Vectors** with x', y', z' having values between 0 and 1. The primes indicate that
the coordinates are box coordinates. A jump due to periodic boundary
conditions causes x', y', z' to jump by :math:`\pm1`. The set of dual basis
vectors **b**\ :sup:`1`, **b**\ :sup:`2`, **b**\ :sup:`3` is defined by
the relation

.. math::
   :label: pfx87

   {b_{i}{b^{j} = \delta_{i}^{j}}.}

Eq defines the dual basis vectors and their relation to the basis vectors.

**Selection of q-Vectors with Phase Changes ** If the q-vectors are now chosen as

.. math::
   :label: pfx88

   {{q = 2}\pi\left( {k{b^{1} + l}{b^{2} + m}b^{3}} \right),}

Describes the selection of q-vectors with phase changes for handling jumps in particle trajectories

where *k,l,m* are integer numbers, jumps in the particle trajectories
produce phase changes of multiples of :math:`2\pi` in the Fourier transformed
particle density, i.e. leave it unchanged. One can define a grid of
*q*-shells or a grid of *q*-vectors along a given direction or on a
given plane, giving in addition a *tolerance* for *q*. *MDANSE* looks
then for *q*-vectors of the form given in Eq. 61 whose moduli
deviate within the prescribed tolerance from the equidistant *q*-grid.
From these *q*-vectors only a maximum number per grid-point (called
generically *q*-shell also in the anisotropic case) is kept.

**Negative Coherent Scattering Lengths** The *q*-vectors can be generated isotropically, anisotropically or along
user-defined directions. The :math:`\sqrt{\omega_{I}}` may be negative
if they represent normalized coherent scattering
lengths, i.e.

.. math::
   :label: pfx89

   {{\sqrt{\omega_{I}} = \frac{b_{I,\text{coh}}}{\sqrt{\sum\limits_{I = 1}^{N_{\mathit{species}}}{n_{I}b_{I,\text{coh}}^{2}}}}}.}

Defines the use of negative coherent scattering lengths for hydrogenous materials.

Negative coherent scattering lengths occur in hydrogenous materials
since :math:`b_{\mathit{coh},H}` is negative [Ref20]_. The density-density
correlation is computed via the *FCA* technique described in the section
:ref:`appendix-fca`.

When the default value of weights (:math:`b_{coherent}`) is chosen for this
analysis, the result will correspond to that of the equation :math:numref:`ntdsf-eq6`
from the :ref:`analysis-ndtsf`.


Dynamic Incoherent Structure Factor
'''''''''''''''''''''''''''''''''''
                      
In this analysis, *MDANSE* proceeds in two steps. First, it computes
the partial and total intermediate incoherent scattering function
F\ :sub:`inc`\ (**q**, t) using equation :math:numref:`pfx69`. Then, the
partial and total dynamic incoherent structure factors are obtained by
performing the Fourier Transformation, defined in Eq. :math:numref:`pfx61`,
respectively on the total and partial intermediate incoherent
scattering function.

**Computation of Incoherent Intermediate Scattering Function**

*MDANSE* computes the incoherent intermediate scattering function on a
rectangular grid of equidistantly spaced points along the time-and the
*q*-axis, respectively:

.. math::
   :label: pfx90

   {\text{F}_{\text{inc}}\left( {q_{m},k\cdot\Delta t} \right)\doteq{\sum\limits_{I = 1}^{N_{\mathit{species}}}{n_{I}\omega_{I,\text{inc}}}}\text{F}_{I,\text{inc}}\left( {q_{m},k\cdot\Delta t} \right),\\
   {k = 0}\ldots{N_{t} - 1},{m = 0}\ldots{N_{q} - 1.}}

Eq: Incoherent Intermediate Scattering Function Calculation

where N\ :sub:`t` is the number of time steps in the coordinate time
series, N\ :sub:`q` is a user-defined number of *q*-shells,
N\ :sub:`species` is the number of selected species, n\ :sub:`I` the
number of atoms of species *I*, :math:`\omega`\ :sub:`I` the weight for species *I*
(see Section :ref:`target_CN` for more details) and :math:`{F_{I,\text{inc}}\left( {q_{m},k\cdot\Delta t} \right)}`
is defined as:

.. math::
   :label: pfx92

   {\text{F}_{I,\mathit{inc},\alpha}{\left( {q_{m},k\cdot\Delta t} \right) = \sum\limits_{\alpha = 1}^{n_{I}}}{\overline{\left\langle {\exp\left\lbrack {{-i}q\cdot R_{\alpha}(0)} \right\rbrack\exp\left\lbrack {iq\cdot R_{\alpha}(t)} \right\rbrack} \right\rangle}}^{q}.}

Eq: Definition of F_{I,inc,alpha}(q_m, k * Δt)

The symbol :math:`{\overline{...}}^{q}` in Eq. :math:numref:`pfx92`
denotes an average
over *q*-vectors having *approximately* the same modulus
:math:`{{q_{m} = {q_{\mathit{\min}} + m}}\cdot\Delta q}`. The
particle density must not change if jumps in the particle
trajectories due to periodic boundary conditions occur. 


*Selection of q-Vectors on a Reciprocal Lattice* In addition, the
*average* particle density, N/V, must not change. This can be achieved
by choosing *q*-vectors on a lattice which is reciprocal to the lattice
defined by the *MD* box. Let **b**\ :sub:`1`, **b**\ :sub:`2`,
**b**\ :sub:`3` be the basis vectors which span the *MD* cell. Any
position vector in the *MD* cell can be written as

.. math::
   :label: pfx94

   {{R = x^{'}}{b_{1} + y^{'}}{b_{2} + z^{'}}b_{3},}

Eq: Position Vector in the MD Cell


with x', y', z' having values between 0 and 1. The primes indicate that
the coordinates are box coordinates. A jump due to periodic boundary
conditions causes x', y', z' to jump by :math:`\pm 1`. The set of dual basis
vectors **b**\ :sup:`1`, **b**\ :sup:`2`, **b**\ :sup:`3` is defined by
the relation

.. math::
   :label: pfx95

   {b_{i}{b^{j} = \delta_{i}^{j}}.}

Eq: Dual Basis Vectors

If the q-vectors are now chosen as

.. math::
   :label: pfx96

   {{q = 2}\pi\left( {k{b^{1} + l}{b^{2} + m}b^{3}} \right),}

Eq: Selection of q-Vectors with Phase Changes   

where *k,l,m* are integer numbers, jumps in the particle trajectories
produce phase changes of multiples of 2π in the Fourier transformed
particle density, i.e. leave it unchanged. One can define a grid of
*q*-shells or a grid of *q*-vectors along a given direction or on a
given plane, giving in addition a *tolerance* for *q*. *MDANSE* looks
then for *q*-vectors of the form given in Eq. :math:numref:`pfx96` whose moduli
deviate within the prescribed tolerance from the equidistant *q*-grid.
From these *q*-vectors only a maximum number per grid-point (called
generically *q*-shell also in the anisotropic case) is kept.

The *q*-vectors can be generated isotropically, anisotropically or along
user-defined directions.

**Computation of Correlation Functions**
The correlation functions defined in :math:numref:`pfx92`
are computed via the *FCA* technique described in the section :ref:`appendix-fca`.
Although the efficient *FCA* technique is used to compute the atomic time correlation
functions, the program may consume a considerable amount of CPU-time
since the number of time correlation functions to be computed equals the
number of atoms times the total number of *q*-vectors. This analysis is
actually one of the most time-consuming among all the analysis available
in *MDANSE*.

When the default value of weights (:math:`{b^{2}}_{incoherent}`) is chosen for this
analysis, the result will correspond to that of the equation :math:numref:`ntdsf-eq7`
from the :ref:`analysis-ndtsf`.



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

**Van Hove Self-correlation Function**

The Elastic Incoherent Structure Factor (*EISF*) is defined as the limit
of the incoherent intermediate scattering function for infinite time,

.. math::
   :label: pfx97

   {\mathit{EISF}(q)\doteq\lim\limits_{t\rightarrow\infty}\text{F}_{\mathit{inc}}\left( {q,t} \right).}

Using the above definition of the EISF one can decompose the incoherent
intermediate scattering function as follows:

.. math::
   :label: pfx98

   {\text{F}_{\text{inc}}{\left( {q,t} \right) = \mathit{EISF}}{(q) + \text{F}_{\text{inc}}^{'}}\left( {q,t} \right),}

where F\ :sub:`inc`\ '(**q**,t) decays to zero for infinite time. Taking
now the Fourier transform it follows immediately that

.. math::
   :label: pfx99

   {\text{S}_{\text{inc}}{\left( {q,\omega} \right) = \mathit{EISF}}(q)\delta{(\omega) + \text{S}_{\text{inc}}^{'}}\left( {q,\omega} \right).}

The *EISF* appears as the amplitude of the *elastic* line in the neutron
scattering spectrum. Elastic scattering is only present for systems in
which the atomic motion is confined in space, as for solids. To
understand which information is contained in the *EISF* we consider for
simplicity a system where only one sort of atoms is visible to the
neutrons. To a very good approximation this is the case for all systems
containing a large amount of hydrogen atoms, as biological systems.
Incoherent scattering from hydrogen dominates by far all other
contributions. Using the definition of the van Hove self-correlation
function G\ :sub:`s`\ (r, t) [Ref20]_,

.. math::
   :label: pfx100

   {b_{\text{inc}}^{2}G_{s}\left( {r,t} \right)\doteq\frac{1}{2\pi^{3}}{\int d^{3}}q\exp\left\lbrack {{- i}q\cdot r} \right\rbrack\text{F}_{\mathit{inc}}\left( {q,t} \right),}

which can be interpreted as the conditional probability to find a tagged
particle at the position **r** at time t, given it started at **r** = 0,
one can write:

.. math::
   :label: pfx101

   {\mathit{EISF}{(q) = b_{\text{inc}}^{2{\int d^{3}}}}r\exp\left\lbrack {\mathit{iq}\cdot r} \right\rbrack G_{s}\left( {r,{t = \infty}} \right).}

The *EISF* gives the sampling distribution of the points in space in the
limit of infinite time. In a real experiment this means times longer
than the time which is observable with a given instrument. The *EISF*
vanishes for all systems in which the particles can access an infinite
volume since G\ :sub:`s`\ (r, t) approaches 1/V for large times. This is
the case for molecules in liquids and gases.

**EISF Computation**

For computational purposes it is convenient to use the following
representation of the *EISF* [Ref21]_:

.. math::
   :label: pfx102

   {\mathit{EISF}{(q) = {\sum\limits_{I = 1}^{N_{\mathit{species}}}{n_{I}\omega_{I,\text{inc}}\mathit{EIS}F_{I}(q)}}}}

where N\ :sub:`species` is the number of selected species, n\ :sub:`I`
the number of atoms of species *I*, :math:`\omega`\ :sub:`I,inc` the weight for
species *I* (see Section :ref:`target_CN` for more details) and for each species the
following expression for the elastic incoherent scattering function is

.. math::
   :label: pfx103

   {\mathit{EIS}F_{I}{(q) = \frac{1}{n_{I}}}{\sum\limits_{\alpha}^{n_{I}}\left\langle {|{\exp\left\lbrack {\mathit{iq}\cdot R_{\alpha}} \right\rbrack\left. {} \right|^{2}}} \right\rangle}.}

This expression is derived from definition :math:numref:`pfx97`
of the *EISF* and expression :math:numref:`pfx70` for the
intermediate scattering function, using that for infinite time the
relation

.. math::
   :label: pfx104
   
   {\left\langle {\mathit{ex}p\left\lbrack {{- \mathit{iq}}\cdot R_{\alpha}(0)} \right\rbrack\mathit{ex}p\left\lbrack {\mathit{iq}\cdot R_{\alpha}(t)} \right\rbrack} \right\rangle = \left\langle {|{\mathit{ex}p\left\lbrack {\mathit{iq}\cdot R_{\alpha}} \right\rbrack\left. {} \right|^{2}}} \right\rangle}

holds. In this way the computation of the *EISF* is reduced to the
computation of a static thermal average. We remark at this point that
the length of the *MD* trajectory from which the *EISF* is computed
should be long enough to allow for a representative sampling of the
conformational space.

**Grid Computation**

*MDANSE* allows one to compute the elastic incoherent structure factor
on a grid of equidistantly spaced points along the *q*-axis:

.. math::
   :label: pfx105

   {\mathit{EISF}\left( q_{m} \right)\doteq{\sum\limits_{I = 1}^{N_{\mathit{species}}}{n_{I}\omega_{I}\mathit{EIS}F_{I}\left( q_{m} \right)}},{m = 0}\ldots{N_{q} - 1.}}

where N\ :sub:`q` is a user-defined number of *q*-shells, the values for
q\ :sub:`m` are defined as

.. math::
   :label: pfx106
   
   {{q_{m} = {q_{\mathit{\min}} + m}}\cdot\Delta q}

, and for each species the following expression for the elastic
incoherent scattering function is:

.. math::
   :label: pfx107

   {\mathit{EIS}F_{I}{\left( q_{m} \right) = \frac{1}{n_{I}}}{\sum\limits_{\alpha}^{n_{I}}{\overline{\left\langle {|{\exp\left\lbrack {\mathit{iq}\cdot R_{\alpha}} \right\rbrack\left. {} \right|^{2}}} \right\rangle}}^{q}}.}

Here the symbol :math:`{\overline{...}}^{q}`
denotes an average over the *q*-vectors having the same modulus
q\ :sub:`m`. The program corrects the atomic input trajectories for
jumps due to periodic boundary conditions.


Gaussian Dynamic Incoherent Structure Factor
''''''''''''''''''''''''''''''''''''''''''''
                      
The Gaussian Dynamic Incoherent Structure Factor is a concept used to study how
particles or atoms move independently within materials over time, with a focus
on their distribution. It's valuable in materials science and condensed matter
physics for understanding dynamic behavior at the atomic level.

**MSD Calculation**

The *MSD* can be related to the incoherent intermediate scattering
function via the cumulant expansion [Ref11]_,
[Ref22]_

.. math::
   :label: pfx108

   {\text{F}_{\text{inc}}^{g}{\left( {q,t} \right) = {\sum\limits_{I = 1}^{N_{\mathit{species}}}{n_{I}\omega_{I,\text{inc}}}}}\text{F}_{I,\text{inc}}^{g}\left( {q,t} \right)}

where N\ :sub:`species` is the number of selected species, n\ :sub:`I`
the number of atoms of species *I*, :math:`\omega`\ :sub:`I,inc` the weight for
species *I* (see Section :ref:`target_CN` for more details) and

.. math::
   :label: pfx109

   {\text{F}_{I,\text{inc}}^{g}{\left( {q,t} \right) = \frac{1}{n_{I}}}\sum\limits_{\alpha}^{n_{I}}\exp\left\lbrack {{- q^{2}}\rho_{\alpha,1}{(t) + q^{4}}\rho_{\alpha,2}(t)\mp\ldots} \right\rbrack.}


**The cumulants**

.. math::
   :label: pfx110
   
   {\rho_{\alpha,k}(t)}

\ are identified as

.. math::
   :label: pfx111

   {\rho_{\alpha,1}{(t) = \left\langle {d_{\alpha}^{2}\left( {t;n_{q}} \right)} \right\rangle}}

.. math::
   :label: pfx112

   {\rho_{\alpha,2}{(t) = \frac{1}{4!}}\left\lbrack {{\left\langle {d_{\alpha}^{4}\left( {t;n_{q}} \right)} \right\rangle - 3}\left\langle {d_{\alpha}^{2}\left( {t;n_{q}} \right)} \right\rangle^{2}} \right\rbrack}

.. math::
   
   {\vdots}

**Gaussian Approximation**

The vector nq is the unit vector in the direction of q. In the Gaussian
approximation the above expansion is truncated after the
q\ :sup:`2`-term. For certain model systems like the ideal gas, the
harmonic oscillator, and a particle undergoing Einstein diffusion, this
is exact. For these systems the incoherent intermediate scattering
function is completely determined by the *MSD*. *MDANSE* allows one to
compute the total and partial incoherent intermediate scattering
function in the *Gaussian approximation* by discretizing equation
:math:numref:`pfx108`:

.. math::
   :label: pfx113

   {\text{F}_{\text{inc}}^{g}\left( {q_{m},k\cdot\Delta t} \right)\doteq{\sum\limits_{I = 1}^{N_{\mathit{species}}}{n_{I}\omega_{I,\text{inc}}\text{F}_{I,\text{inc}}^{g}\left( {q_{m},k\cdot\Delta t} \right)}},{k = 0}\ldots{N_{t} - 1},{m = 0}\ldots{N_{q} - 1.}}

**Intermediate Scattering Function**

with for each species the following expression for the intermediate
scattering function:

.. math::
   :label: pfx114

   {\text{F}_{I,\alpha,\text{inc}}^{g}{\left( {q_{m},k\cdot\Delta t} \right) = \frac{1}{n_{I}}}\sum\limits_{\alpha}^{n_{I}}\exp\left\lbrack {\frac{- \left( q_{m} \right)^{2}}{6}\Delta_{\alpha}^{2}\left( {k\cdot\Delta t} \right)} \right\rbrack\mathit{isotropic}\mathit{system}}

.. math::
   :label: pfx115

   {\text{F}_{I,\alpha,\text{inc}}^{g}{\left( {q_{m},k\cdot\Delta t} \right) = \frac{1}{n_{I}}}\sum\limits_{\alpha}^{n_{I}}\exp\left\lbrack {\frac{- \left( q_{m} \right)^{2}}{2}\Delta_{\alpha}^{2}\left( {k\cdot\Delta t;n} \right)} \right\rbrack\mathit{isotropic}\mathit{system}}

N\ :sub:`t` is the total number of time steps in the coordinate time
series and N\ :sub:`q` is a user-defined number of *q*-shells. The (q,
t)-grid is the same as for the calculation of the intermediate
incoherent scattering function (see `Dynamic Incoherent Structure
Factor <#_Dynamic_Incoherent_Structure>`__). The quantities

.. math::
   :label: pfx116
   
   {\Delta_{\alpha}^{2}(t)}

\ and

.. math::
   :label: pfx117
   
   {\Delta_{\alpha}^{2}\left( {t;n} \right)}

are the mean-square displacements, defined in Equations :math:numref:`pfx14`
and :math:numref:`pfx15`, respectively.
They are computed by using the algorithm described in the `Mean Square
Displacement <#_Theory_and_implementation_2>`__ section. *MDANSE*
corrects the atomic input trajectories for jumps due to periodic
boundary conditions. It should be noted that the computation of the
intermediate scattering function in the Gaussian approximation is much
'cheaper' than the computation of the full intermediate scattering
function, F\ :sub:`inc`\ (q, t), since no averaging over different
*q*-vectors needs to be performed. It is sufficient to compute a single
mean-square displacement per atom.



Neutron Dynamic Total Structure Factor
''''''''''''''''''''''''''''''''''''''

The Neutron Dynamic Total Structure Factor is a term used in scientific
research, especially in neutron scattering experiments, to investigate how
particles or atoms within a material contribute to its overall structure and
dynamics. This factor provides valuable insights into how these components move
and interact over time.

**Calculation of Partial Coherent Intermediate Scattering Functions and Dynamic Structure Factors**


This is a combination of the Dynamic Coherent and the Dynamic Incoherent
Structure Factors. It is a fully neutron-specific analysis, where the
coherent part of the intermediate scattering function is calculated
using the atomic coherent neutron scattering lengths
:math:`b_{coherent}` and
the incoherent one is calculated using the square of the atomic
incoherent neutron scattering lengths :math:`{b^{2}}_{incoherent}`. Therefore, in
this analysis the weights option is not available.

The partial coherent intermediate scattering functions
:math:`I_{\alpha\beta}^{coh}(Q,t)` (and their corresponding Fourier
transforms giving the partial coherent dynamic structure factors,
:math:`S_{\alpha\beta}^{coh}(Q,\omega)`) are calculated exactly in the
same way as in the DCSF analysis, i.e.:

.. math::
   :label: ntdsf-eq1
   
   I_{\alpha\beta}^{coh}(Q,t) = \left| \frac{1}{\sqrt{N_{\alpha}N_{\beta}}}\sum_{i \in \alpha,j \in \beta}^{N_{\alpha},N_{\beta}}\left\langle e^{- i\mathbf{Q}\mathbf{r}_{i}(t_{0})}e^{i\mathbf{Q}\mathbf{r}_{j}(t_{0} + t)} \right\rangle \right|_{\mathbf{Q}}

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
:math:`I_{\alpha}^{inc}(Q,t)` and the partial incoherent dynamic
structure factors :math:`S_{\alpha}^{inc}(Q,\omega)` are obtained as in
the DISF analysis:

.. math::
   :label: ntdsf-eq2
   
   I_{\alpha}^{inc}(Q,t) = \left| \frac{1}{N_{\alpha}}\sum_{i \in \alpha}^{N_{\alpha}}\left\langle e^{- i\mathbf{Q}\mathbf{r}_{i}(t_{0})}e^{i\mathbf{Q}\mathbf{r}_{i}(t_{0} + t)} \right\rangle \right|_{\mathbf{Q}}


**Combination of Partial Contributions**

The main difference between this analysis and the DCSF and DISF
analyses, apart from the fact that the coherent and incoherent
contributions are calculated simultaneously, is the way the different
partial contributions are combined. In this analysis the total
incoherent, total coherent and total (coherent + incoherent) signals are
calculated as:

.. math::
   :label: ntdsf-eq3
   
   I^{inc}(Q,t) = \sum_{\alpha}^{N_{\alpha}}{c_{\alpha}b_{\alpha,\text{inc}}^{2}}I_{\alpha}^{inc}(Q,t)

.. math::
   :label: ntdsf-eq4
   
   I^{coh}(Q,t) = \sum_{\alpha,\beta}^{N_{\alpha},N_{\beta}}{\sqrt{c_{\alpha}c_{\beta}}b_{\alpha,\text{coh}}b_{\beta,\text{coh}}I_{\alpha\beta}^{coh}(Q,t)}

.. math::
   :label: ntdsf-eq5
   
   I^{tot}(Q,t) = I^{inc}(Q,t) + I^{coh}(Q,t) = \sum_{\alpha}^{N_{\alpha}}{c_{\alpha}b_{\alpha,\text{inc}}^{2}}I_{\alpha}^{inc}(Q,t) + \sum_{\alpha,\beta}^{N_{\alpha},N_{\beta}}{\sqrt{c_{\alpha}c_{\beta}}b_{\alpha,\text{coh}}b_{\beta,\text{coh}}I_{\alpha\beta}^{coh}(Q,t)}

where :math:`c_{\alpha} = \frac{N_{\alpha}}{N}` and
:math:`c_{\beta} = \frac{N_{\beta}}{N}` are the concentration numbers
for elements :math:`\alpha` and :math:`\beta`, respectively.

These expressions correspond to the formalism and equations given in
[Ref47]_, chapter 1: “An introduction to neutron scattering” .

**Units Conversion**

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
   
   I^{coh}(Q,t) = \frac{\sum_{\alpha\beta}^{n}{c_{\alpha}c_{\beta}b_{\alpha,coh}b_{\beta,coh}I_{\alpha\beta}^{coh}(Q,t)}}{\sum_{\alpha\beta}^{n}{c_{\alpha}c_{\beta}b_{\alpha,coh}b_{\beta,coh}}}

And the incoherent intermedicate scattering function given by the DISF
analysis is (assuming that the chosen weights are b_incoherent2):

.. math::
   :label: ntdsf-eq7
   
   I^{inc}(Q,t) = \frac{\sum_{\alpha}^{n}{c_{\alpha}b_{\alpha,inc}^{2}I_{\alpha}^{inc}(Q,t)}}{\sum_{\alpha}^{n}{c_{\alpha}b_{\alpha,inc}^{2}}}

Naturally, similar expressions apply to the dynamic structure factors,
:math:`S_{\alpha\beta}^{coh}(Q,\omega)` and
:math:`S_{\alpha}^{inc}(Q,\omega)`.


Structure Factor From Scattering Function
'''''''''''''''''''''''''''''''''''''''''

-  available for analysis results only

The "Structure Factor From Scattering Function" is a concept used in scientific research, particularly in the field of neutron scattering experiments. It relates to how particles or atoms within a material contribute to its overall structural properties based on their scattering behavior. This concept provides valuable insights into the material's internal structure, dynamics, and interactions. Researchers use the Structure Factor From Scattering Function to better understand the atomic-level details of materials, which has applications in diverse areas, including materials science and condensed matter physics
