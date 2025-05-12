
This section is dealing with specific types of analysis performed by
MDANSE. If you are not sure where these fit into the general workflow
of data analysis, please read :ref:`workflow-of-analysis`.

Analysis: Other
===============

This section contains background theory for following plugins:

-  :ref:`infrared`
-  :ref:`dipole-autocorrelation-function`
-  :ref:`density`
-  :ref:`temperature`
-  :ref:`box-translated-trajectory`
-  :ref:`center-of-masses-trajectory`
-  :ref:`cropped-trajectory`
-  :ref:`global-motion-filtered-trajectory`
-  :ref:`rigid-body-trajectory`
-  :ref:`unfolded-trajectory`
-  :ref:`mcstas-virtual-instrument`


Infrared
^^^^^^^^

^^^^^^^^

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


Thermodynamics
^^^^^^^^^^^^^^

^^^^^^^^^^^^^^

.. _density:

Density
'''''''
Density is used in molecular dynamics simulations to calculate and
analyze the density of particles within a simulated system. Density
refers to the concentration of particles (atoms, molecules, or ions)
in a given volume of space. This helps researchers understand how
particles are distributed within the simulation box and how their
density changes over time. By calculating density profiles or histograms,
scientists can gain insights into phase transitions, the formation of
clusters, or the behavior of molecules in various regions of the system.
Understanding density is crucial for studying phase changes, solvation,
and other thermodynamic processes in molecular systems.

.. _temperature:

Temperature
'''''''''''
The temperature is another essential tool in molecular dynamics
simulations that allows researchers to monitor and control the
temperature of the simulated system. Temperature is a fundamental
thermodynamic variable that influences molecular motion and interactions.
This plugin provides the means to calculate and adjust the temperature
throughout a simulation, ensuring that the system remains at the desired
temperature or follows a specific temperature profile. Monitoring
temperature fluctuations and deviations from the desired values is
crucial for accurately simulating and understanding the thermodynamic
behavior of molecules. Controlling temperature is particularly
important when studying phase transitions, chemical reactions, and
equilibrium properties of molecular systems.

Trajectory
^^^^^^^^^^

^^^^^^^^^^

.. _box-translated-trajectory:

Box Translated Trajectory
'''''''''''''''''''''''''
.. note::

    **This job is currently not available.
    The documentation here is out-dated and only left here for referencing
    purposes.**

    A box translated trajectory in molecular dynamics simulations refers to a
    technique where the entire simulation box, representing the space in which
    molecules interact, is shifted or translated during the simulation. This
    approach can be useful for correcting periodic boundary condition artifacts,
    studying different regions of a system, applying unique boundary conditions,
    or mitigating surface effects. The translation of the simulation box allows
    researchers to explore specific aspects of molecular behavior and system
    properties within the computational environment.

.. _center-of-masses-trajectory:

Center Of Masses Trajectory
'''''''''''''''''''''''''''
The center of mass trajectory (COMT) analysis consists in deriving the
trajectory of the respective centres of mass of a set of groups of
atoms. In order to produce a visualizable trajectory, MDANSE assigns
the centres of mass to pseudo-hydrogen atoms whose mass is equal to the
mass of their associated group. Thus, the produced trajectory can be
reused for other analysis. In that sense, COMT analysis is a practical
way to reduce noticeably the dimensionality of a system.

.. _cropped-trajectory:

Cropped Trajectory
''''''''''''''''''
.. note::

    **This job is currently not available.
    The documentation here is out-dated and only left here for referencing
    purposes.**

    A cropped trajectory in molecular dynamics simulations refers to a
    shortened version of the trajectory data file, focusing on a specific time
    segment of a simulation. This cropping process is useful for reducing data
    size, isolating relevant events, improving computational efficiency, and
    enhancing visualization. It allows researchers to concentrate on the critical
    dynamics or interactions within a molecular system while excluding
    unnecessary or transient data.

.. _global-motion-filtered-trajectory:

Global Motion Filtered Trajectory
'''''''''''''''''''''''''''''''''
.. note::

    **This job is currently not available.
    The documentation here is out-dated and only left here for referencing
    purposes.**

    It is often of interest to separate global motion from internal motion,
    both for quantitative analysis and for visualization by animated
    display. Obviously, this can be done under the hypothesis that global
    and internal motions are decoupled within the length and timescales of
    the analysis. MDANSE can create global motion filtered trajectory
    (GMFT) by filtering out global motions (made of the three
    translational and rotational degrees of freedom), either on the whole
    system or on a user-defined subset, by fitting it to a reference
    structure (usually the first frame of the MD). Global motion filtering
    uses a straightforward algorithm:

    -  for the first frame, find the linear transformation such that the
       coordinate origin becomes the centre of mass of the system and its
       principal axes of inertia are parallel to the three coordinates axes
       (also called principal axes transformation),
    -  this provides a reference configuration :math:`C_{\mathrm{ref}}`,
    -  for any other frames :math:`f`, finds and applies the linear transformation
       that minimizes the RMS distance between frame :math:`f` and :math:`C_{\mathrm{ref}}`.

    The result is stored in a new trajectory file that contains only
    internal motions. This analysis can be useful in case where diffusive
    motions are not of interest or simply not accessible to the experiment
    (time resolution, powder analysis . . . ).

.. _rigid-body-trajectory:

Rigid Body Trajectory
'''''''''''''''''''''
.. note::

    **This job is currently not available.
    The documentation here is out-dated and only left here for referencing
    purposes.**

    To analyse the dynamics of complex molecular systems it is often
    desirable to consider the overall motion of molecules or molecular
    subunits. We will call this motion rigid-body motion in the following.
    Rigid-body motions are fully determined by the dynamics of the centroid,
    which may be the centre-of-mass, and the dynamics of the angular
    coordinates describing the orientation of the rigid body. The angular
    coordinates are the appropriate variables to compute angular correlation
    functions of molecular systems in space and time. In most cases,
    however, these variables are not directly available from MD
    simulations since MD algorithms typically work in cartesian
    coordinates. Molecules are either treated as flexible, or, if they are
    treated as rigid, constraints are taken into account in the framework of
    cartesian coordinates [Ref23]_. In MDANSE,
    rigid-body trajectory (RBT) can be defined from a MD trajectory by
    fitting rigid reference structures, defining a (sub)molecule, to the
    corresponding structure in each time frame of the trajectory. Here 'fit'
    means the optimal superposition of the structures in a least-squares
    sense. We will describe now how rigid body motions, i.e. global
    translations and rotations of molecules or subunits of complex
    molecules, can be extracted from a MD trajectory. A more detailed
    presentation is given in [Ref24]_. We define
    an optimal rigid-body trajectory in the following way: for each time
    frame of the trajectory the atomic positions of a rigid reference
    structure, defined by the three cartesian components of its centroid
    (e.g. the centre of mass) and three angles, are as close as possible to
    the atomic positions of the corresponding structure in the MD
    configuration. Here "as close as possible" means as close as possible in
    a least-squares sense.

    **Optimal superposition**: We consider a given time frame in which the
    atomic positions of a (sub)molecule are given by :math:`x_{\alpha}` where :math:`{\alpha = 1}, \ldots, N`.
    The corresponding positions in the reference structure are denoted as
    :math:`x_{\alpha}^{(0)}` where :math:`{\alpha = 1}, \ldots, N`.
    For both the given structure and the reference structure we introduce
    the yet undetermined centroids :math:`X` and :math:`X^{(0)}`, respectively, and
    define the deviation

    .. math::

       {\Delta_{\alpha}\doteq D(q){\left\lbrack {x_{\alpha}^{(0)} - X^{(0)}} \right\rbrack - \left\lbrack {x_{\alpha} - X} \right\rbrack}.}

    Here :math:`D(q)` is a rotation matrix which depends on also yet
    undetermined angular coordinates which we chose to be quaternion
    parameters, abbreviated as vector :math:`q = (q_0, q_1, q_2, q_3)`.
    The quaternion parameters fulfil the normalization condition :math:`q \cdot {q = 1}` [Ref25]_.
    The target function to be minimized is now defined as

    .. math::

       {m{\left( {q;X,X^{(0)}} \right) = {\sum\limits_{\alpha}{\omega_{\alpha}|\Delta|_{\alpha}^{2}}}}.}

    where :math:`\omega_{\alpha}` are atomic weights. The minimization
    with respect to the centroids is decoupled from the minimization with
    respect to the quaternion parameters and yields

    .. math::

       {{X = {\sum\limits_{\alpha}\omega_{\alpha}}}x_{\alpha} \qquad\qquad  {X^{(0)} = {\sum\limits_{\alpha}\omega_{\alpha}}}x_{\alpha}^{(0)}}

    We are now left with a minimization problem for the rotational part
    which can be written as

    .. math::

       m{(q) = {\sum\limits_{\alpha}{\omega_{\alpha}\left\lbrack {{D(q)r}_{\alpha}^{(0)} - r_{\alpha}} \right\rbrack^{2}}}\overset{!}{=}\mathrm{Min}}.

    The relative position vectors

    .. math::

       {{r_{\alpha} = {x_{\alpha} - X}} \qquad\qquad r_{\alpha}^{(0)} = {x_{\alpha}^{(0)} - X^{(0)}}}

    are fixed and the rotation matrix reads
    [Ref25]_

    .. math::

       D(q) = \begin{pmatrix}
       {q_{0}^{2} + q_{1}^{2} - q_{2}^{2} - q_{3}^{2}} & {2\left( {{- q_{0}}{q_{3} + q_{1}}q_{2}} \right)} & {2\left( {q_{0}{q_{2} + q_{1}}q_{3}} \right)} \\
       {2\left( {q_{0}{q_{3} + q_{1}}q_{2}} \right)} & {q_{0}^{2} + q_{2}^{2} - q_{1}^{2} - q_{3}^{2}} & {2\left( {{- q_{0}}{q_{1} + q_{2}}q_{3}} \right)} \\
       {2\left( {{- q_{0}}{q_{2} + q_{1}}q_{3}} \right)} & {2\left( {q_{0}{q_{1} + q_{2}}q_{3}} \right)} & {q_{0}^{2} + q_{3}^{2} - q_{1}^{2} - q_{2}^{2}} \\
       \end{pmatrix}


    **Quaternions and rotations**: The rotational minimization problem can
    be elegantly solved by using quaternion algebra. Quaternions are
    so-called hypercomplex numbers, having a real unit, 1, and three
    imaginary units, :math:`I`, :math:`J`, and :math:`K`. Since :math:`IJ = K` (cyclic),
    quaternion multiplication is not commutative. A possible matrix
    representation of an arbitrary quaternion,

    .. math::

       {{A = a_{0}}{1 + a_{1}}{I + a_{2}}{J + a_{3}} K,}

    reads

    .. math::

       A = \begin{pmatrix}
       a_{0} & {- a_{1}} & {- a_{2}} & {- a_{3}} \\
       a_{1} & a_{0} & {- a_{3}} & a_{2} \\
       a_{2} & a_{3} & a_{0} & {- a_{1}} \\
       a_{3} & {- a_{2}} & a_{1} & a_{0} \\
       \end{pmatrix}

    The components :math:`a_{\upsilon}`
    are real numbers. Similarly, as normal complex numbers allow one to
    represent rotations in a plane, quaternions allow one to represent
    rotations in space. Consider the quaternion representation of a vector
    :math:`R`, which is given by

    .. math::

       {{R = x}{I + y}{J + z} K,}

    and perform the operation

    .. math::

       {{R^{'} = \mathit{QRQ}^{T}},}

    where :math:`Q` is a normalised quaternion

    .. math::

       {\text{|}Q\text{|}^{2}\doteq{{q_{0}^{2} + q_{1}^{2} + q_{2}^{2} + q_{3}^{2}} = \frac{1}{4}\mathrm{Tr}\, Q^{T}Q = 1}}.

    We note that a normalized quaternion is represented by an orthogonal 4 x 4 matrix. :math:`R'` may then be
    written as

    .. math::

       {{R^{'} = x^{'}}{I + y^{'}}{J + z^{'}} K,}

    where the components :math:`x'`, :math:`y'`, :math:`z'`, abbreviated as :math:`r'`, are given by :math:`r^{'} = D(q)r`.

    **Solution of the minimization problem**: In quaternion algebra, the
    rotational minimization problem may now be phrased as follows:

    .. math::

       {m{(q) = {{\sum\limits_{\alpha}{{\omega_{\alpha}\text{|}\mathit{QR}}_{\alpha}^{(0)}Q}^{T}} - R_{\alpha}}}{\text{|}^{2}\overset{!}{=}\mathrm{Min}}.}

    Since the matrix :math:`Q` representing a normalized quaternion is orthogonal
    this may also be written as

    .. math::

       {{{m{(q) = {\sum\limits_{\alpha}\omega_{\alpha}}}\text{|}\mathit{QR}_{\alpha}^{(0)}} - R_{\alpha}}Q\text{|}^{2}{\overset{!}{=}\mathrm{Min}}.}

    This follows from the simple fact that :math:`\text{|}A{\text{|} = \text{|}}\mathit{AQ}\text{|}`
    if :math:`Q` is normalized. Eq. `104` shows that the
    target function to be minimized can be written as a simple quadratic
    form in the quaternion parameters [Ref24]_,

    .. math::

       {m{(q) = q}\cdot\mathit{Mq} \qquad\qquad {M = {\sum\limits_{\alpha}{\omega_{\alpha}M_{\alpha}}}}}

    The matrices :math:`M` are positive semi-definite matrices depending on the
    positions :math:`r_{\alpha}` and :math:`r_{\alpha}^{(0)}`.

    The rotational fit is now reduced to the problem of finding the minimum
    of a quadratic form with the constraint that the quaternion to be
    determined must be normalized. Using the method of Lagrange multipliers
    to account for the normalization constraint we have

    .. math::

       {m^{'}{\left( {q,\lambda} \right) = q}\cdot{\mathit{Mq} - \lambda}{\left( {q\cdot{q - 1}} \right)\overset{!}{=}\mathrm{Min}}.}

    This leads immediately to the eigenvalue problem

    .. math::

       {{\mathit{Mq} = \lambda}q \qquad\qquad q\cdot{q = 1.}}

    Now any normalized eigenvector :math:`q` fulfils the relation

    .. math::

       {{\lambda = q}\cdot\mathit{Mq}\equiv m(q)}

    Therefore, the eigenvector belonging to the smallest eigenvalue,
    :math:`\lambda_{\mathrm{min}}`, is the desired solution. At the same time :math:`\lambda_{\mathrm{min}}`
    gives the average error per atom. The result of RBT analysis is stored
    in a new trajectory file that contains only RBT motions.

.. _unfolded-trajectory:

Unfolded Trajectory
'''''''''''''''''''
.. note::

    **This job is currently not available.
    The documentation here is out-dated and only left here for referencing
    purposes.**

    An unfolded trajectory in the context of molecular dynamics
    simulations refers to a trajectory data file that has been processed or
    analyzed to reveal the unfolding or expansion of molecular structures over
    time. This term is particularly relevant in the study of biomolecules or
    polymers, where understanding the dynamic evolution and changes in these
    structures holds significant importance for scientific applications,
    including drug design, materials science, and biomolecular research.
    Unfolding trajectories provide valuable insights into molecular behavior
    and interactions, contributing to the development of new materials and the
    design of therapeutic compounds.


Virtual Instruments
^^^^^^^^^^^^^^^^^^^

^^^^^^^^^^^^^^^^^^^

.. _mcstas-virtual-instrument:

McStas Virtual Instrument
'''''''''''''''''''''''''
.. note::

    **This job is currently not available.
    The documentation here is out-dated and only left here for referencing
    purposes.**

    McStas enables researchers to create virtual instruments that replicate the
    behavior of real neutron or X-ray instruments. This capability streamlines
    the design, optimization, and testing of experiments within a virtual
    environment before conducting physical experiments. Such simulations help
    researchers conserve valuable time and resources while simultaneously
    enhancing the precision and reliability of their experiments. McStas finds
    widespread application in fields like materials science and condensed
    matter physics.
