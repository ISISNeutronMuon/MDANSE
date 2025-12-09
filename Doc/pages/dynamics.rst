
This section is dealing with specific types of analysis performed by
MDANSE. If you are not sure where these fit into the general workflow
of data analysis, please read :ref:`workflow-of-analysis`.

Analysis: Dynamics
==================

This section contains background theory for following plugins:

-  :ref:`analysis-dos`
-  :ref:`analysis-msd`
-  :ref:`analysis-pcf`
-  :ref:`analysis-pps`
-  :ref:`analysis-rtcf`
-  :ref:`root-mean-square-deviation`
-  :ref:`root-mean-square-fluctuation`
-  :ref:`analysis-vhf`
-  :ref:`analysis-vcf`


.. _analysis-dos:

Density of States
'''''''''''''''''

.. _theory-and-implementation-1:

MDANSE calculates the power spectrum of the velocity correlation function (see the
section on :ref:`analysis-vcf`), which includes the Fourier transform of the
cartesian products of the velocity correlation function such as
the Fourier transform of the time correlation between the :math:`x` and
:math:`y` components of the velocity

.. math::
   :label: dos1

   C_{v_x v_y\alpha\alpha}(\omega) = \frac{1}{Nc_{\alpha}} \sum_{j \in \alpha} \frac{1}{2\pi} \int\mathrm{d}t \, \left\langle v_{x,j}\left( 0 \right)\cdot v_{y,j}\left( t \right) \right\rangle e^{-i\omega t}

where :math:`C_{v_x v_y\alpha\alpha}\left( \omega \right)`
is the Fourier transform of the of the velocity correlation function average
over atoms of type :math:`\alpha`, and :math:`v_{x,j}` and :math:`v_{y,j}` are
the :math:`x` and :math:`y` components of the velocity of atom :math:`j`.

The Fourier transform of the mass-weighted velocity
autocorrelation function (average of the diagonal terms of the
mass-weighted velocity correlation function) for a harmonic system is the
vibrational DOS

.. math::
   :label: dos2

   \mathrm{DOS}(\omega) = \sum\limits_{\alpha} W_{\alpha} C_{\mathbf{vv}\alpha\alpha}\left( \omega \right),

.. math::
   :label: dos3

   C_{\mathbf{vv}\alpha\alpha}(\omega) = \frac{1}{Nc_{\alpha}} \sum_{j \in \alpha} \frac{1}{6\pi} \int\mathrm{d}t \, \left\langle \mathbf{v}_{j}\left( 0 \right)\cdot \mathbf{v}_{j}\left( t \right) \right\rangle e^{-i\omega t}.

where :math:`W_{\alpha}` is the weighting factor of atom type :math:`\alpha`.
Since the DOS is computed from the unnormalized velocity autocorrelation function,
the DOS at :math:`\omega=0` gives an approximate value for the diffusion
constant (see Eq. :math:numref:`vacf6`) when an equal weighting scheme is used.
The DOS can be smoothed by, for example, a Gaussian window applied in the time
domain [Ref10]_ (see the section :ref:`correlation-frames`); the diffusion
constant obtained from this DOS is biased due to the spectral smoothing
procedure.

MDANSE computes the density of states starting from atomic
velocities. In the case that velocities are not available, the velocities will be
computed by numerical differentiation of the coordinate trajectories
correcting first for possible jumps due to periodic boundary conditions.

The DOS is also related to the DISF, since for isotropic systems

.. math::
   :label: dos3

   \mathrm{DOS}(\omega) = \lim_{q  \rightarrow 0} \frac{1}{3} \frac{\omega^2}{q^2} S_{\text{inc}}(q, \omega)

so that DOS result relevant to neutron experiment measuring the vibrational (or phonon)
density of states can be calculated by using the ``b_incoherent`` weight setting.


.. _analysis-msd:

Mean Square Displacement
''''''''''''''''''''''''

.. _theory-and-implementation-2:

.. _figure-one:

.. figure:: ./Pictures/10000000000001BC00000163C18A769B32940652.png
   :align: center
   :width: 11.748cm
   :height: 9.393cm

   MSD calculated for a 100 ps MD simulation of 256 water
   molecules using NPT condition at 1 bar and 300 K.

Molecules in liquids and gases do not stay in the same place but move
constantly. This process is called diffusion and it happens quite
naturally in fluids at equilibrium. During this process, the motion of
an individual molecule does not follow a simple path. As it travels, the
molecule undergoes some collisions with other molecules which prevent it
from following a straight line. If the path is examined in close detail,
it will be seen to be a good approximation to a random walk.
Mathematically, a random walk is a series of steps where each step is
taken in a completely random direction from the one before. This kind of
path was famously analysed by Albert Einstein in a study of Brownian
motion. He showed that the Mean-Square Displacement (MSD) of a
particle following a random walk is proportional to the time elapsed.
The :numref:`figure-one` shows an example of an MSD analysis
performed on a water box of 768 water molecules. To get the diffusion
coefficient out of this plot, the slope of the linear part of the plot
should be calculated.

By defining :math:`\mathbf{d}_{j}(t) = \mathbf{r}_{j}(t) - \mathbf{r}_{j}(0)`
the MSD of particle :math:`j` can be written as

.. math::
   :label: msd1

   \Delta_{j}^{2}{(t) = \left\langle {d_{j}^{2}( {t} )} \right\rangle}

where :math:`\mathbf{r}_{j}(0)` and :math:`\mathbf{r}_{j}(t)` are
the position of particle :math:`j` at times :math:`0` and :math:`t`
and :math:`d_{j}( t ) = \vert \mathbf{d}_{j}(t) \vert`.
One can introduce an MSD with respect to a given axis :math:`\mathbf{n}`

.. math::
   :label: msd2

   \Delta_{j}^{2}(\hat{\mathbf{n}}, t) = \left\langle {d_{j}^{2}(\hat{\mathbf{n}}, t)} \right\rangle, \qquad d_{j}(\hat{\mathbf{n}}, t) = \hat{\mathbf{n}} \cdot \mathbf{d}_{j}(t)

where :math:`\hat{\mathbf{n}}` is a unit vector along :math:`\mathbf{n}`.

The calculation of MSD is the standard way to obtain diffusion
coefficients from MD simulations.
Assuming Einstein-diffusion in the long time limit one has for isotropic systems

.. math::
   :label: msd3

   {D_{j} = {\lim\limits_{t\rightarrow\infty}{\frac{1}{6t}\mathrm{\Delta}_{j}^{2}(t)}}}.

There exists also a well-known relation between the MSD and the
velocity autocorrelation function. One can show (see e.g. [Ref11]_) that

.. math::
   :label: msd4
   
   \mathbf{d}_{j}{(t) = {\int\limits_{0}^{t}{\mathrm{d}t' \, \mathbf{v}_{j}(t')}}} \qquad \text{and} \qquad \mathrm{\Delta}_{j}^{2}{(t) = 6}{\int\limits_{0}^{t}{\mathrm{d}t' \, ( t - t' )C_{\mathbf{vv}jj}(t')}}

where :math:`C_{\mathbf{vv}jj}(t)` is the velocity autocorrelation function of the particle :math:`j`.
Using now the definition of the diffusion
coefficient Eq. :math:numref:`msd3` one obtains the relations

.. math::
   :label: msd5

   {{D_{j} = {\int\limits_{0}^{\infty}{\mathrm{d}t \, C_{\mathbf{vv}jj}(t)}}} = \pi C_{\mathbf{vv}jj}(\omega=0).}


Computationally, the MSD is calculated by calculating the position autocorrelation since
from Eq. :math:numref:`msd1`

.. math::
   :label: msd6

   \Delta_{j}^{2}(t) = \left\langle [\mathbf{r}_{j}( t ) - \mathbf{r}_{j}(0)]^2 \right\rangle = \left\langle \mathbf{r}_{j}^{2}(t) \right\rangle + \left\langle \mathbf{r}_{j}^{2}( 0 ) \right\rangle - 2\left\langle \mathbf{r}_{j}(t )\mathbf{r}_{j}(0) \right\rangle

where the last part on the right side Eq. :math:numref:`msd6` is the position autocorrelation of the particle :math:`j`.


.. _analysis-pcf:

Position Correlation Function
'''''''''''''''''''''''''''''''''

The position correlation function (PCF) is similar to the
velocity correlation function in :ref:`analysis-vcf`. In MDANSE the PCF
is calculated relative to the atoms average position over the entire
trajectory. The position autocorrelation function (average of the
diagonal terms of the PCF) of atom type :math:`\alpha` is

.. math::
   :label: pcf1

   \mathrm{PACF}_{\alpha}(t) = \frac{1}{3}\frac{1}{Nc_{\alpha}} \sum_{j \in \alpha}  \left\langle {\Delta \mathbf{r}_{j}(0)\cdot \Delta  \mathbf{r}_{j}(t)} \right\rangle

where

.. math::
   :label: pcf2

   \Delta \mathbf{r}_{j}\left( t \right) = \mathbf{r}_{j}(t) - \langle \mathbf{r}_{j} \rangle

so that the origin dependence of the position autocorrelation function is removed.


.. _analysis-pps:

Position Power Spectrum
'''''''''''''''''''''''

The position power spectrum is similar to the density of states
calculation in :ref:`analysis-dos` but is instead a Fourier transform of the
PCF. The average of the diagonal terms of the PPS is

.. math::
   :label: pps1

   \mathrm{PPS}_{\alpha}(\omega) =  \int\mathrm{d}t \ \mathrm{PACF}_{\alpha}(t) e^{-i\omega t}

and is related to the vibrational DOS via the expresssion

.. math::
   :label: pps2

   \mathrm{DOS}_{\alpha}(\omega) = \omega^2 \mathrm{PPS}_{\alpha}(\omega).

.. _analysis-rtcf:

Reorientational Time Correlation Function
'''''''''''''''''''''''''''''''''''''''''

Reorientational Time-Correlation Function (RTCF) describes
the change in orientation of a specific direction axis within a molecule.
This axis is usually defined as a vector between two specific atoms in
the molecule, or between one atom and the molecule's centre of mass.

Reorientational time-correlation functions can be Legendre
polynomials of different order. At the moment, this analysis will calculate
all the orders up the maximum Legendre polynomial order specified as one
of the input parameters.

Angle at time :math:`t` is calculated as the following:

.. math::
    \hat{\mathbf{n}}(t) =  \frac{\mathbf{r}_{i}(t) - \mathbf{r}_{j}(t)}{\vert \mathbf{r}_{i}(t) - \mathbf{r}_{j}(t) \vert}

.. math::
    \phi(t = t_{1}-t_{0}) = \arccos( \hat{\mathbf{n}}(t_{1}) \cdot \hat{\mathbf{n}}(t_{0}))

The general result is :math:`C_{l}(t) = \langle P_{l}[\cos(\phi(t))] \rangle`,
where :math:`P_{l}[x]` is the Legendre polynomial of the order :math:`l`.


.. _root-mean-square-deviation:

Root Mean Square Deviation
''''''''''''''''''''''''''
                         
The root mean-square deviation (RMSD) is perhaps the most popular estimator
of structural similarity. It quantifies differences between two structures by
measuring the root mean-square of atomic position differences, revealing
insights into their structural dissimilarities. It is a numerical measure of
the difference between two structures. Typically, RMSD is used to quantify
the structural evolution of the system during the simulation. It can be used
to verify if the simulated system has reached equilibrium or,
conversely, if major structural changes occurred during the simulation.
The RMSD for the atom of type :math:`\alpha` can be defined as

.. math::
   :label: rmsd1

   \mathrm{RMSD}_{\alpha}(t) = \sqrt{ \frac{1}{Nc_{\alpha}} \sum\limits_{j \in \alpha} \vert \mathbf{r}_{j}(t) - \mathbf{r}_{j}(t_{\mathrm{ref}}) \vert^{2} }

where :math:`\mathbf{r}_{j}(t)` and :math:`\mathbf{r}_{j}(t_{\mathrm{ref}})`
are respectively the position of atom :math:`j` at time :math:`t`
and :math:`t_{\mathrm{ref}}` where :math:`t_{\mathrm{ref}}` is a reference
time usually chosen as the zeroth time of the simulation. As with other
analysis jobs in MDANSE, the RMSD results can be grouped. The grouping is slightly
different to all other analysis calculations; see :ref:`grouping-rmsd` for
more details.

.. _root-mean-square-fluctuation:

Root Mean Square Fluctuation
''''''''''''''''''''''''''''

The root mean square fluctuation (RMSF) measures the average magnitude of
deviations or fluctuations in atomic positions from their mean positions during
a simulation. RMSF analysis is valuable for understanding the flexibility and
stability of different components of the system, providing insights into regions
where atoms or groups of atoms exhibit significant fluctuations. This information
can be crucial for studying the dynamic behavior of biomolecules, protein-ligand
interactions, or any molecular systems subject to temporal variations. Unlike
other job types in MDANSE, the RMSF is only calculated for each atom

.. math::
   :label: rmsf1

   \mathrm{RMSF}_{j} = \sqrt{\langle \vert \mathbf{r}_{j} - \langle \mathbf{r}_{j} \rangle \vert^2 \rangle}

so that :math:`\mathrm{RMSF}_{j}` is the RMSF for the atom :math:`j`. As with other
analysis jobs in MDANSE, the RMSF results can be grouped. This grouping is slightly
different to all other analysis calculations; see :ref:`grouping-rmsf` for more
details.

.. _analysis-vhf:

Van Hove Function
'''''''''''''''''
The van Hove function describes the probability of finding a particle
:math:`k` at time :math:`t` with a displacement of :math:`\mathbf{r}` from a
particle :math:`j` at a time :math:`0`. In MDANSE the van Hove function is
written as a weighted sum of partial terms which are divided by the density

.. math::
   :label: vanhove1

    G(\mathbf{r}, t) = \sum_{\alpha}\sum_{\beta \geq \alpha} W_{\alpha\beta}G_{\alpha\beta}(\mathbf{r}, t),

.. math::
   :label: vanhove2

    G_{\alpha\beta}(\mathbf{r}, t) = \frac{1}{Nc_{\alpha}c_{\beta}}  \frac{1}{\rho} \sum_{j \in \alpha} \sum_{k \in \beta} \left\langle \delta [\mathbf{r} - \mathbf{r}_{k}(t) + \mathbf{r}_{j}(0)] \right\rangle.

The van Hove function is related to the intermediate scattering
function via a Fourier transform and the dynamic structure factor
via a double Fourier transform

.. math::
   :label: vanhove3

    F_{\alpha\beta}(\mathbf{q}, t) = \rho \int \mathrm{d}\mathbf{r} \, G_{\alpha\beta}(\mathbf{r},t) e^{i \mathbf{q} \cdot \mathbf{r}},

.. math::
   :label: vanhove4

    S_{\alpha\beta}(\mathbf{q}, \omega) = \rho \int \mathrm{d}t \int \mathrm{d}\mathbf{r}  \, G_{\alpha\beta}(\mathbf{r},t) e^{i \mathbf{q} \cdot \mathbf{r} - i \omega t}

and can be split into distinct and self parts where

.. math::
   :label: vanhove5

    G_{\alpha\beta}^{\mathrm{d}}(\mathbf{r}, t) = \frac{1}{Nc_{\alpha}c_{\beta}}  \frac{1}{\rho} \sum_{j \in \alpha} \sum_{\substack{k \in \beta \\ k \neq j}} \left\langle \delta [\mathbf{r} - \mathbf{r}_{k}(t) + \mathbf{r}_{j}(0)] \right\rangle,

.. math::
   :label: vanhove6

    G^{\mathrm{s}}_{\alpha}(\mathbf{r}, t) = \frac{1}{Nc_{\alpha}}  \frac{1}{\rho} \sum_{j \in \alpha} \left\langle \delta [\mathbf{r} - \mathbf{r}_{j}(t) + \mathbf{r}_{j}(0)] \right\rangle.

At :math:`t = 0` distinct-part of the van Hove function reduces to the
pair distribution function while the self-part of the van Hove function
becomes a delta function

.. math::
   :label: vanhove7

    G_{\alpha\beta}^{\mathrm{d}}(\mathbf{r}, 0) = g_{\alpha\beta}(\mathbf{r}), \qquad\qquad G^{\mathrm{s}}_{\alpha}(\mathbf{r}, 0) =   \frac{1}{\rho} \delta(\mathbf{r})

where :math:`g_{\alpha\beta}(\mathbf{r})` is the partial pair distribution function.
For liquid or gaseous systems,

.. math::
   :label: vanhove8

    \lim_{t \rightarrow \infty } G_{\alpha\beta}^{\mathrm{d}}(\mathbf{r}, t) = \lim_{\mathbf{r} \rightarrow \infty } G_{\alpha\beta}^{\mathrm{d}}(\mathbf{r}, t) = 1,

.. math::
   :label: vanhove9

    \lim_{t \rightarrow \infty } G^{\mathrm{s}}_{\alpha}(\mathbf{r}, t) = N^{-1}

where in the thermodynamic limit :math:`N \rightarrow \infty`.

.. _analysis-vcf:

Velocity Correlation Function
'''''''''''''''''''''''''''''''''

.. _theory-and-implementation-4:

The Velocity Correlation Function (VCF) is a property describing the dynamics
of a molecular system. It reveals the underlying nature of the forces acting on
the system. For a harmonic system, the Fourier transform of the average of the
diagonal components, the velocity autocorrelation function (VACF), is related to
the vibrational density of states.

In a molecular system that would be made of non-interacting particles,
the velocities would be constant and the VACF would have
a constant value. Now, if we think about a system with small
interactions such as in a gas-phase, the magnitude and direction of the
velocity of a particle will change gradually over time due to its
collision with the other particles of the molecular system. In such a
system, the VACF will be represented by a decaying exponential.

In the case of solid phase, the interactions are much stronger and, as a
results, the atoms are bound to a given position from which they will
move backwards and forwards oscillating between positive and negative
values of their velocity. The oscillations will not be of equal
magnitude however, but will decay in time, because there are still
perturbative forces acting on the atoms to disrupt the perfection of
their oscillatory motion. So, in that case the VACF will look like a
damped harmonic motion.

Finally, in the case of liquid phase, the atoms have more freedom than
in solid phase and because of the diffusion process, the oscillatory
motion seen in solid phase will be cancelled quite rapidly depending on
the density of the system. So, the VACF will just have one very damped
oscillation before decaying to zero. This decaying time can be
considered as the average time for a collision between two atoms to
occur before they diffuse away.

The VCF of atom :math:`j` in an atomic or molecular system is defined as
between the :math:`x` and :math:`y` components of the velocity is
defined as

.. math::
   :label: vacf0

   C_{v_x v_y jj}(t) = \frac{1}{3}\left\langle v_{x,j}(0) v_{y,j}( t ) \right\rangle

while the VACF of atom :math:`j` in an atomic or molecular system is defined as

.. math::
   :label: vacf1

   {C_{\mathbf{vv}jj}(t) = \frac{1}{3}\left\langle {\mathbf{v}_{j}( 0 )\cdot \mathbf{v}_{j}( t )} \right\rangle.}

In some cases, e.g. for non-isotropic systems, it is useful to define
VACF along a given axis,

.. math::
   :label: vacf2

   {C_{\mathbf{vv}jj}(\hat{\mathbf{n}}, t) = \frac{1}{3}\left\langle {v_{j}(\hat{\mathbf{n}}, 0) v_{j}(\hat{\mathbf{n}}, t)} \right\rangle, \qquad v_{j}(\hat{\mathbf{n}}, t) =   \hat{\mathbf{n}} \cdot \mathbf{v}_{j}(t)}

where the vector :math:`\hat{\mathbf{n}}` is a unit vector defining a space-fixed
axis. The VACF of the particles in a many-body system can be related to the
incoherent dynamic structure factor by the relation

.. math::
   :label: vacf3

   {\lim\limits_{q\rightarrow 0}\frac{1}{3}\frac{\omega^{2}}{q^{2}}S_{\mathrm{inc}}{(\mathbf{q},\omega) = \mathrm{DOS}}(\hat{\mathbf{q}}, \omega)}

where :math:`\hat{\mathbf{q}}` is the unit vector in the direction of :math:`\mathbf{q}`.
Here the total density of states is a weighted sum of the Fourier transform of
the projected VACF

.. math::
   :label: vacf4

   \mathrm{DOS}(\hat{\mathbf{q}}, \omega) = \sum\limits_{\alpha} W_{\alpha} C_{\mathbf{vv}\alpha\alpha}(\hat{\mathbf{q}}, \omega),

.. math::
   :label: vacf5

   {C_{\mathbf{vv}\alpha\alpha}{(\hat{\mathbf{q}}, \omega) = \frac{1}{2\pi}} \frac{1}{Nc_{\alpha}}\sum_{j \in \alpha} {\int\mathrm{d} t \,} C_{\mathbf{vv}jj}(\hat{\mathbf{q}}, t) e^{-i \omega t}}.

Provided the VACF decays to zero at long time, the function may be
integrated mathematically to calculate the diffusion coefficient :math:`D`, as in:

.. math:: 
   :label: vacf6
   
   D = \frac{1}{3}\int\limits_{0}^{\infty}\mathrm{d} t \, \langle \mathbf{v}(0) \cdot \mathbf{v}(t) \rangle.

This is a special case of a more general relationship between the VACF and the
mean square displacement, and belongs to a class of properties known as the
Green-Kubo relations, which relate correlation functions to so-called transport
coefficients.
