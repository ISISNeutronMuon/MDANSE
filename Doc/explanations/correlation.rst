
.. _correlation-frames:

Time Series
===========

Correlation Functions
~~~~~~~~~~~~~~~~~~~~~

Most of the quantities which can be extracted from MD
simulations are time correlation functions. In MDANSE we use a correlation
window to ensure that the time averaging for each time step
is done in a consistent way. Consider two time series

.. math::
   :label: correlation1

   A(n \Delta t) \quad \text{and} \quad B(n \Delta t)

of length :math:`t_{\mathrm{tot}} = (n_{\mathrm{t}} -1) \Delta t` (:math:`n = 0, \ldots, n_{\mathrm{t}}-1`)
which are to be correlated. In MDANSE,
correlation function are calculated by first choosing a specific
number of correlation time steps :math:`n_{\mathrm{c}}` which will define
the length of our correlation function :math:`t_{\mathrm{cor}} = (n_{\mathrm{c}} -1) \Delta t`. The correlation function of
:math:`A(n \Delta t)` and :math:`B(n \Delta t)` will be

.. math::
   :label: correlation2

   C_{AB}(n' \Delta t) = \frac{1}{n_{\mathrm{t}} - n_{\mathrm{c}} + 1} \sum\limits_{n=0}^{n_{\mathrm{t}} - n_{\mathrm{c}} + 1} A^{*}(n\Delta t)B([n + n']\Delta t)

where :math:`n' = 0, \ldots, n_{c} - 1`. In case that :math:`A(n \Delta t)` and
:math:`B(n \Delta t)` are identical, the corresponding correlation function
:math:`C_{AA}(n' \Delta t)` is called an *autocorrelation* function. Notice that
the prefactor is the same for all :math:`n' \Delta t` time steps, this was
not the case in previous versions of MDANSE. This meant that for different
time steps a different number of configurations were used to obtain the
average correlation; leading to spuriously large correlations for some
time intervals. However in MDANSE 2 your correlation functions will be
truncated since :math:`t_{\mathrm{tot}} \geq t_{\mathrm{cor}}`.

.. _correlation-fourier-spectrum :

Fourier Spectrum
~~~~~~~~~~~~~~~~

In many cases not only is the computation of a correlation function
required, but also the computation of its Fourier spectrum. In
MDANSE the spectra can be smoothed by applying an instrument resolution
function

.. math::
   :label: fourier1

   P_{AB}\left(m \Delta \omega \right) = \frac{\Delta t}{2 \pi}\sum_{n=-(n_{\mathrm{c}}-1)}^{n_{\mathrm{c}}-1}
   \exp\left[- 2 \pi i \frac{n \Delta t }{2n_{\mathrm{c}} - 1} m \Delta \omega \right] \frac{W(n \Delta t)}{W(0)} C_{AB}( \vert n \Delta t \vert )

here :math:`m = -(n_{\mathrm{c}}-1), \ldots, n_{\mathrm{c}}-1` and :math:`\Delta \omega` is the
frequency step. Notice that the we assume that the correlation is symmetric so
that :math:`C_{AB}(n \Delta t) = C_{AB}( |n \Delta t| )` which should
approximately be the case for all the correlation functions calculated
in MDANSE assuming good (equilibrated, of a sufficient length/size and
etc) MD trajectories are used. In MDANSE, the resolution function are
specified in the frequency domain and are related to the resolution
function in the time domain via a Fourier transform

.. math::
   :label: fourier2

   W(n \Delta t) = \frac{1}{2n_{\mathrm{c}} - 1} \frac{1}{ \Delta t} \sum_{m=-(n_{\mathrm{c}}-1)}^{n_{\mathrm{c}}-1} \exp\left[ 2 \pi i \frac{m \Delta \omega}{2n_{\mathrm{c}} - 1} n \Delta t \right] W(m \Delta \omega)

where :math:`n = -(n_{\mathrm{c}}-1), \ldots, n_{\mathrm{c}}-1`.

Resolution Functions
~~~~~~~~~~~~~~~~~~~~

**Ideal**: The Ideal window is the default resolution function and is simply
:math:`W(m \Delta \omega) = \delta(m \Delta \omega)`. This means that the spectra will not be smoothed,
it is important to use this window first to check the raw results from
your MD calculations so that you can determine how noisy your raw results
are and whether longer MD trajectories where required.

**Gaussian**: A Gaussian window instrument resolution function is

.. math::
   :label: resolution1

   W(m \Delta \omega) = \frac{\sqrt{2 \pi}}{ \sigma} \exp\left[-\frac{1}{2}\left(\frac{ m \Delta \omega  - \mu }{\sigma}\right)^2\right]

where :math:`\sigma` is related to the width of the resolution function
and :math:`\mu` is a parameter which shifts the resolution function.

**Lorentzian**: A Lorentzian window instrument resolution function is

.. math::
   :label: resolution2

   W(m \Delta \omega) = \frac{2 \sigma}{(m\Delta \omega - \mu)^2 + \sigma^2}

where :math:`\sigma` is related to the width of the resolution function
and :math:`\mu` is a parameter which shifts the resolution function..

**Triangular**: A triangular window instrument resolution function is

.. math::
   :label: resolution3

    W(m \Delta \omega) = \begin{cases}
        2 \pi (1 - \vert m \Delta \omega - \mu \vert / \sigma), & \vert m \Delta \omega - \mu \vert \leq \sigma;\\
        0,                    & \text{otherwise}.
    \end{cases}

where :math:`\sigma` is related to width of the resolution function
and :math:`\mu` is a parameter which shifts the resolution function.

**Square**: A square window instrument resolution function is

.. math::
   :label: resolution4

    W(m \Delta \omega) = \begin{cases}
        \pi / \sigma, & \vert m \Delta \omega - \mu \vert \leq \sigma;\\
        0,                    & \text{otherwise}.
    \end{cases}

where :math:`\sigma` is related to width of the resolution function
and :math:`\mu` is a parameter which shifts the resolution function.

**PseudoVoigt**: A Pseudo-Voigt window instrument resolution function is a
linear combination of the Gaussian and Lorentzian window functions


.. math::
   :label: resolution5

    W(m \Delta \omega) = \eta \frac{2 \sigma_{\text{L}}}{(m\Delta \omega - \mu_{\text{L}})^2 + \sigma_{\text{L}}^2} + (1 - \eta) \frac{\sqrt{2 \pi}}{ \sigma_{\text{G}}} \exp\left[-\frac{1}{2}\left(\frac{ m \Delta \omega  - \mu_{\text{G}} }{\sigma_{\text{G}}}\right)^2\right]

where :math:`\eta` is a parameter which changes the fractions of the
Gaussian and Lorentzian window functions, :math:`\sigma_{\text{L}}`
and :math:`\sigma_{\text{G}}` related to width of the resolution
functions of the Lorentzian and Gaussian windows and :math:`\mu_{\text{L}}`
and :math:`\mu_{\text{G}}` are is a parameter which shifts the
Lorentzian and Gaussian windows.
