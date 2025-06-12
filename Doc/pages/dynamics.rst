
This section is dealing with specific types of analysis performed by
MDANSE. If you are not sure where these fit into the general workflow
of data analysis, please read :ref:`workflow-of-analysis`.

Analysis: Dynamics
==================

This section contains background theory for following plugins:

-  :ref:`analysis-angular-correlation`
-  :ref:`analysis-dos`
-  :ref:`analysis-msd`
-  :ref:`analysis-op`
-  :ref:`analysis-pacf`
-  :ref:`analysis-vhf`
-  :ref:`analysis-vacf`

.. _analysis-angular-correlation:

Angular Correlation
'''''''''''''''''''
.. note::

    **This job is under development and may change in future versions
    of MDANSE. The documentation here is out-dated and only left here
    for referencing purposes.**

    The angular correlation analysis computes the autocorrelation of a set
    of vectors describing the extent of a molecule in three orthogonal
    directions. This kind of analysis can be useful when trying to highlight
    the fact that a molecule is constrained in a given direction.

    For a given triplet of non-colinear atoms :math:`g=(a_1,a_2,a_3)`, one can
    derive an orthonormal set of three vectors :math:`v_1`, :math:`v_2`, :math:`v_3` using the
    following scheme:

    -  :math:`v_{1} = (n_{1} + n_{2}) / \left| {n_{1} + n_{2}} \right|`
       where :math:`n_1` and :math:`n_2` are respectively the
       normalized vectors along (:math:`a_1`, :math:`a_2`) and (:math:`a_1`, :math:`a_3`) directions.
    -  :math:`v_2` is defined as the clockwise normal vector orthogonal to :math:`v_1` that
       belongs to the plane defined by :math:`a_1`, :math:`a_2` and :math:`a_3` atoms
    -  :math:`v_{3} = v_{1}\times v_{2}`

    Thus, one can define the following autocorrelation functions for the
    vectors :math:`v_1`, :math:`v_2` and :math:`v_3` defined on triplet :math:`i`:

    .. math::

       {\mathrm{AC}_{g,i}{(t) = \left\langle {v_{g,i}(0)\cdot v_{g,i}(t)} \right\rangle} \qquad {i = 1,2,3}}

    and the angular correlation averaged over all triplets is:

    .. math::

       {\mathrm{AC}_{i}{(t) = {\sum\limits_{g = 1}^{N_{\mathrm{triplets}}}{\mathrm{AC}_{g,i}(t)}}} \qquad {i = 1,2,3}}

    where :math:`N_{\mathrm{triplets}}` is the number of selected triplets.


.. _analysis-dos:

Density of States
'''''''''''''''''

.. _theory-and-implementation-1:

MDANSE calculates the power spectrum of the VACF (see the
section on :ref:`analysis-vacf`), which in case of
the mass-weighted VACF defines the phonon discrete DOS as

.. math::
   :label: dos1

   \mathrm{DOS}(\omega) = \sum\limits_{\alpha} W_{\alpha} C_{\mathbf{vv}\alpha\alpha}\left( \omega \right),

.. math::
   :label: dos2

   C_{\mathbf{vv}\alpha\alpha}(\omega) = \frac{1}{Nc_{\alpha}} \sum_{j \in \alpha} \frac{1}{6\pi} \int\mathrm{d}t \, \left\langle \mathbf{v}_{j}\left( 0 \right)\cdot \mathbf{v}_{j}\left( t \right) \right\rangle e^{-i\omega t}

where :math:`C_{\mathbf{vv}\alpha\alpha}\left( \omega \right)`
is the Fourier transform of the velocity autocorrelation function average over atoms of type :math:`\alpha`,
:math:`W_{\alpha}` is the weighting factor of atom type :math:`\alpha`.
The DOS can be computed either for the isotropic case or with respect to a
user-defined axis.

Since the DOS is computed from the unnormalized VACF, the DOS at :math:`\omega=0` gives an
approximate value for the diffusion constant (see Eq. :math:numref:`pfx7`)
when an equal weighting scheme is used. The DOS can be
smoothed by, for example, a Gaussian window applied in the time domain
[Ref10]_ (see the section :ref:`correlation-frames`); the diffusion
constant obtained from this DOS is biased due to the spectral smoothing
procedure since the VACF is weighted by this window Gaussian function.

MDANSE computes the density of states starting from atomic
velocities. In the case that velocities are not available, the velocities will be
computed by numerical differentiation of the coordinate trajectories
correcting first for possible jumps due to periodic boundary conditions.

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

.. _analysis-op:

Order Parameter
'''''''''''''''

.. _theory-and-implementation-3:
                         
.. note::

    **This job is currently not available.
    The documentation here is out-dated and only left here for referencing
    purposes.**

    Adequate and accurate cross comparison of the NMR and MD simulation
    data is of crucial importance in versatile studies conformational
    dynamics of proteins. NMR relaxation spectroscopy has proven to be a
    unique approach for a site-specific investigation of both global
    tumbling and internal motions of proteins. The molecular motions
    modulate the magnetic interactions between the nuclear spins and lead
    for each nuclear spin to a relaxation behaviour which reflects its
    environment. Since its first applications to the study of protein
    dynamics, a wide variety of experiments has been proposed to investigate
    backbone as well as side chain dynamics. Among them, the heteronuclear
    relaxation measurement of amide backbone :sup:`15`\ N nuclei is one of
    the most widespread techniques. The relationship between microscopic
    motions and measured spin relaxation rates is given by Redfield's theory
    [Ref13]_. Under the hypothesis that
    :sup:`15`\ N relaxation occurs through dipole-dipole interactions with
    the directly bonded :sup:`1`\ H atom and chemical shift anisotropy
    (CSA), and assuming that the tensor describing the CSA is axially
    symmetric with its axis parallel to the N-H bond, the relaxation rates
    of the :sup:`15`\ N nuclei are determined by a time correlation
    function,

    .. math::

       {C_{\mathit{ii}}{(t) = \left\langle {P_{2}\left( {\mu_{i}(0)\cdot\mu_{i}(t)} \right)} \right\rangle}}

    which describes the dynamics of a unit vector :math:`\mu_{i}(t)` pointing
    along the :sup:`15`\ N-:sup:`1`\ H bond of the residue :math:`i` in the
    laboratory frame. Here :math:`P_{2}(x)` is the second order Legendre
    polynomial. The Redfield theory shows that relaxation measurements probe
    the relaxation dynamics of a selected nuclear spin only at a few
    frequencies. Moreover, only a limited number of independent observables
    are accessible. Hence, to relate relaxation data to protein dynamics one
    has to postulate either a dynamical model for molecular motions or a
    functional form for :math:`C_{ii}(t)`, yet depending on a limited number
    of adjustable parameters. Usually, the tumbling motion of proteins in
    solution is assumed isotropic and uncorrelated with the internal
    motions, such that:

    .. math::

       {C_{\mathit{ii}}{(t) = C^{\mathrm{G}}}(t) C_{\mathit{ii}}^{\mathrm{I}}(t)}

    where :math:`C^{\mathrm{G}}(t)` and :math:`C_{\mathit{ii}}^{\mathrm{I}}(t)` denote the
    global and the internal time correlation function,
    respectively. Within the so-called model free approach
    [Ref14]_, [Ref15]_
    the internal correlation function is modelled by an exponential,

    .. math::

       {C_{\mathit{ii}}^{\mathrm{I}}{(t) = {S_{i}^{2} + \left( {1 - S_{i}^{2}} \right)}}\exp\left( \frac{- t}{\tau_{\mathrm{eff},i}} \right)}

    Here the asymptotic value

    .. math::

       {S_{i}^{2} = C_{\mathit{ii}}}\left( {+ \infty} \right)

    \ is the so-called generalized order parameter, which indicates the
    degree of spatial restriction of the internal motions of a bond vector,
    while the characteristic time :math:`\tau_{\mathrm{eff},i}` is an
    effective correlation time, setting the time scale of the
    internal relaxation processes. :math:`S_{i}^{2}` can adopt values
    ranging from :math:`0` (completely disordered) to :math:`1` (fully ordered). So,
    :math:`S_{i}^{2}` is the appropriate indicator of protein backbone motions in
    computationally feasible timescales as it describes the spatial aspects
    of the reorientational motion of N-H peptidic bonds vector.

    When performing order parameter analysis, MDANSE computes for each
    residue :math:`i` both :math:`C_{\mathit{ii}}(t)` and :math:`S_{i}^{2}`.
    It also computes a correlation function averaged over all the selected
    bonds defined as:

    .. math::

       {C^{\mathrm{I}}{(t) = {\sum\limits_{i = 1}^{N_{\mathrm{bonds}}}{C_{\mathit{ii}}^{\mathrm{I}}(t)}}}}

    where :math:`N_{\mathrm{bonds}}` is the number of selected bonds for the analysis.


.. _analysis-pacf:

Position Autocorrelation Function
'''''''''''''''''''''''''''''''''

The position autocorrelation function (PACF) is similar to the
velocity autocorrelation function in :ref:`analysis-vacf`. In MDANSE the PACF
is calculated relative to the atoms average position over the entire
trajectory. The PACF of atom type :math:`\alpha` is

.. math::
   :label: pacf1

   \mathrm{PACF}_{\alpha}(t) = \frac{1}{3}\frac{1}{Nc_{\alpha}} \sum_{j \in \alpha}  \left\langle {\Delta \mathbf{r}_{j}(0)\cdot \Delta  \mathbf{r}_{j}(t)} \right\rangle

where

.. math::
   :label: pacf2

   \Delta \mathbf{r}_{j}\left( t \right) = \mathbf{r}_{j}(t) - \langle \mathbf{r}_{j} \rangle

so that the origin dependence of the PACF function is removed.

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

.. _analysis-vacf:

Velocity Autocorrelation Function
'''''''''''''''''''''''''''''''''

.. _theory-and-implementation-4:

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

Mathematically, the VACF of atom :math:`j` in an atomic or molecular system is
usually defined as

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
