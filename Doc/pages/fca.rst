
.. _appendix-fca:

The FCA algorithm
=================

Most of the quantities which can be extracted from MD
simulations are time correlation functions. 
Correlation functions of discrete time series can be efficiently
calculated by using the FFT [Ref44]_ . The FCA allows
the number of multiplications (complexity) to be reduced
from :math:`\propto N_t^2` to :math:`\propto N_t \log_2(N_t)`. In 
MDANSE all time correlation functions are computed using
the FCA method which will be outlined in the 
following. We will also briefly comment on spectral smoothing
of Fourier transformed correlation functions.

We consider two time series

.. math::
   :label: eqn-fca1

   a(k\cdot\Delta t),
   \qquad b(k\cdot\Delta t),
   \qquad k = 0\ldots N_t-1, 

of length :math:`T = (N_t-1)\cdot\Delta t` which are
to be correlated. In the following the shorthands
:math:`a(k)` and :math:`b(k)` will be used. The discrete
correlation function of :math:`a(k)` and :math:`b(k)` is
defined as

.. math::
   :label: eqn-fca2

   c_{ab}(m) \doteq \left\{
   \begin{array}{ll}
   \frac{1}{N_t - m}\sum_{k=0}^{N_t-m-1}a^*(k)b(k+m),
                 \qquad m= 0\ldots N_t-1,\\
   \frac{1}{N_t - |m|}\sum_{k=|m|}^{N_t-1}a^*(k)b(k-|m|),
                 \qquad m= -(N_t-1)\ldots -1.\\
   \end{array} \right.

The prefactors in front of the sums ensure the proper normalization of
the individual channels, :math:`m = -(N_t-1)\ldots N_t-1`.  The asterisk
denotes a complex conjugate. According to :math:numref:`eqn-fca2`,
:math:`c_{ab}(m)` has :math:`2N_t - 1` data points and obeys
the symmetry relation

.. math::
   :label: eqn-fca3
   
   c_{ab}(m) = c^*_{ba}(-m).
   
In case that :math:`a(k)` and :math:`b(k)` are identical, the corresponding
correlation function :math:`c_{aa}(m)` is called an *autocorrelation*
function. We define now the extended, periodic time series

.. math::
   :label: eqn-fca4
   
   A(k) = \begin{split}
           a(k) k = 0 \ldots N_t-1\\
           0    k = N_t \ldots 2N_t-1\\
                ,\end{split}\\
   B(k) = \begin{split}
           b(k) k = 0 \ldots N_t-1\\
           0    k = N_t \ldots 2N_t-1\\
                ,\end{split}

which have the period :math:`2N_t`,

.. math::
   :label: eqn-fca5

   A(k) = A(k + m\cdot 2N_t),\qquad
   B(k) = B(k + m\cdot 2N_t),\qquad m = 0,\pm 1,\pm 2,\ldots.

The discrete, cyclic correlation of :math:`A(k)` and :math:`B(k)`
is defined as

.. math::
   :label: eqn-fca6

   S_{AB}(m) = \sum_{k=0}^{2N_t-1} A^*(k)B(k+m).

It is easy to see that

.. math::
   :label: eqn-fca7

   c_{ab}(m) = \frac{1}{N_t-|m|}S_{AB}(m),\qquad -(N_t-1) \le m \le N_t-1.

Using the correlation theorem of discrete periodic functions [Ref44]_
, :math:`S_{AB}(m)` can be written as

.. math::
   :label: eqn-fca8

   S_{AB}(m) = \frac{1}{2N_t}\sum_{n=0}^{2N_t-1} 
   \exp\left[2\pi i\left(\frac{mn}{2N_t}\right)\right]\,
   \tilde A^*\left(\frac{n}{2N_t}\right)\tilde B\left(\frac{n}{2N_t}\right)

where :math:`\tilde A\left(\frac{n}{2N_t}\right)` and
:math:`\tilde B\left(\frac{n}{2N_t}\right)` are the
discrete Fourier transforms of
:math:`A(k)` and :math:`B(k)`, respectively:

.. math::
   :label: eqn-fca9

   \tilde A\left(\frac{n}{2N_t}\right) =
   \sum_{k=0}^{2N_t-1} \exp\left[-2\pi i\left(\frac{n k}{2N_t}\right)\right]
   \,A(k),\\
   \tilde B\left(\frac{n}{2N_t}\right) =
   \sum_{k=0}^{2N_t-1} \exp\left[-2\pi i\left(\frac{n k}{2N_t}\right)\right]
   \,B(k).

If the Fourier transforms of the signals :math:`A(k)`
and :math:`B(k)` as well as the inverse transform in
:math:numref:`eqn-fca8` are computed by FFT,
$S_{AB}(m)$ can be computed by $\propto N_t\log_2(N_t)$ instead of
$\propto N_t^2$ multiplications. It is sometimes said that the FFT}
method induces spurious correlations. We emphasize that this is only
the case if the time series $a(k)$ and $b(k)$ are not properly
extended, as indicated in Eqs. :math:numref:`eqn-fca4`. The FFT
method and the direct scheme :math:numref:`eqn-fca2` give, apart from
round-off errors, *identical results*.

In many cases not only the computation of a correlation function is
required, but also the computation of its Fourier spectrum. In
principle one could use the product

.. math::
   :label: eqn-fca10

   \tilde A^*\left(\frac{n}{2N_t}\right) \tilde B\left(\frac{n}{2N_t}\right)

which is already available as an intermediate step in the computation
of :math:`S_{AB}(m)` according to :math:numref:`eqn-fca8`.
This would, however, not be a good estimate for the spectrum
of :math:`c_{ab}(m)` [Ref45]_ . In
MDANSE all spectra are smoothed by applying a window in the time
domain [Ref45]_ 

.. math::
   :label: eqn-fca11

   P_{ab}\left(\frac{n}{2N_t}\right) =
   \Delta t\cdot \sum_{m=-(N_t-1)}^{N_t-1} 
   \exp\left[-2\pi i\left(\frac{n m}{2N_t}\right)\right]
   \,W(m)\,\frac{1}{N-|m|}S_{AB}(m).

The time step :math:`\Delta t` in front of the sum yields the proper
normalization of the spectrum. In MDANSE a Gaussian window
[Ref46]_ is used:

.. math::
   :label: eqn-fca12

   W(m) = \exp\left[
   -\frac{1}{2}\left(\alpha\frac{|m|}{N_t-1}\right)^2
   \right],
   \qquad m = -(N_t-1)\ldots N_t-1.

Its widths in the time and frequency domain are :math:`\sigma_t = \alpha/T`
and :math:`\sigma_\nu = 1/(2\pi\sigma_t)`, respectively. We recall that
:math:`T =(N_t-1)\cdot\Delta t` is the length of the simulation.
:math:`\sigma_\nu` corresponds to the width of the resolution
function of the Fourier spectrum.

