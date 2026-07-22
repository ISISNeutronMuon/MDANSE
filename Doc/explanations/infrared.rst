
This section is dealing with specific types of analysis performed by
MDANSE. If you are not sure where these fit into the general workflow
of data analysis, please read :ref:`workflow-of-analysis`.

Infrared
========

This section contains background theory for following plugins:

-  :ref:`infrared`
-  :ref:`dipole-autocorrelation-function`

.. _infrared:

Infrared
''''''''
Calculates the molecular infrared spectrum averaged over all molecules
in the trajectory. The infrared spectrum is calculated from the Fourier
transform of the autocorrelation of the time-derivative of the
molecular dipole:

.. math::
   :label: ir1

   I(\omega) \propto  \frac{1}{N_{m}}\sum_{m} \frac{1}{6\pi} \int \mathrm{d}t \,  \left\langle \dot{\vec{\mu}}_{m}(0) \cdot \dot{\vec{\mu}}_{m}(t) \right\rangle e^{-i\omega t}

where :math:`N_{m}` is the number of molecules and :math:`\dot{\vec{\mu}}_{m}(t)` is
the time-derivative of the molecular dipole moment of molecule :math:`m`.

.. _dipole-autocorrelation-function:

Dipole Autocorrelation Function
'''''''''''''''''''''''''''''''

Calculates the molecular dipole autocorrelation function which is closely
related to the molecular infrared spectrum

.. math::
   :label: ir2

   \mathrm{DACF}(t) = \frac{1}{3 N_{m}}\sum_{m} \left\langle \vec{\mu}_{m}(0) \cdot \vec{\mu}_{m}(t) \right\rangle

where :math:`N_{m}` is the number of molecules :math:`m` and :math:`\vec{\mu}(t)` is
the molecular dipole moment of molecule :math:`m`.
