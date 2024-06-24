
.. _appendix-fca:

Correlation Functions
=====================

Most of the quantities which can be extracted from MD
simulations are time correlation functions. In MDANSE we use a correlation
window method to ensure that the time averaging for each time step
is done in a consistent way. Consider two time series

.. math::
   :label: eqn-fca1

   a(k\cdot\Delta t)
   \qquad b(k\cdot\Delta t)
   \qquad k = 0, \ldots, N_t-1,

of length :math:`T = (N_{\mathrm{t}} -1)\cdot\Delta t` which are
to be correlated. The following the shorthands
:math:`a(k)` and :math:`b(k)` will be used. Now we choose a specific
number of correlation frames :math:`N_{\mathrm{c}}` to use which will define
the length of our correlation function. The correlation function of
:math:`a(k)` and :math:`b(k)` will be

.. math::
   :label: eqn-fca2

   c_{ab}(m) \doteq \frac{1}{N_{\mathrm{t}} - N_{\mathrm{c}} + 1} \sum\limits_{} a^{*}(k)b(k + m) \qquad m = 0, \ldots, N_{\mathrm{c}} - 1.

and :math:`c_{ab}(m) = c^{*}_{ab}(-m)`. In case that :math:`a(k)` and
:math:`b(k)` are identical, the corresponding correlation function
:math:`c_{aa}(m)` is called an *autocorrelation* function. Notice that
the prefactor is the same for all time steps :math:`m`, in previous
versions of MDANSE this was not the case. This meant that for different
time steps a different number of configurations were used to obtain the
average correlation; leading to spuriously large correlations for some
time intervals.

In many cases not only is the computation of a correlation function
required, but also the computation of its Fourier spectrum. In
MDANSE the spectra can be smoothed by applying a window in the time
domain [Ref45]_ 

.. math::
   :label: eqn-fca11

   P_{ab}\left(\frac{n}{2N_{\mathrm{c}}}\right) =
   \Delta t\cdot \sum_{m=-(N_{\mathrm{c}}-1)}^{N_{\mathrm{c}}-1}
   \exp\left[-2\pi i\left(\frac{n m}{2N_{\mathrm{c}}}\right)\right]
   \,W(m)\,\frac{1}{N_{\mathrm{c}}-|m|}c_{ab}(m).

The time step :math:`\Delta t` in front of the sum yields the proper
normalization of the spectrum. For example, a Gaussian window
[Ref46]_ can be used where:

.. math::
   :label: eqn-fca12

   W(m) = \exp\left[
   -\frac{1}{2}\left(\alpha\frac{|m|}{N_{\mathrm{c}}-1}\right)^2
   \right]
   \qquad m = -(N_{\mathrm{c}}-1), \ldots, N_{\mathrm{c}}-1.

Its widths in the time and frequency domain are :math:`\sigma_t = \alpha/T`
and :math:`\sigma_\nu = 1/(2\pi\sigma_t)`, respectively.
:math:`\sigma_\nu` corresponds to the width of the resolution
function of the Fourier spectrum and
:math:`T_{\mathrm{c}} =(N_{\mathrm{c}}-1)\cdot\Delta t` is the length of the correlation
function.
