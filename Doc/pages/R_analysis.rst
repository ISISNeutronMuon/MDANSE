Analysis: other options ref
===========================


.. _analysis-infrared:

Infrared
^^^^^^^^

Dipole AutoCorrelation Function
'''''''''''''''''''''''''''''''

-  available for trajectories only


Refolded Membrane Trajectory
''''''''''''''''''''''''''''

+-----------------------------+----------------+---------+------------------------------------------------------------------------------------+
| Parameter                   | Format         | Default | Description                                                                        |
+=============================+================+=========+====================================================================================+
| Axis                        | Drop-down      | c       | Axis along which is used for trajectory manipulation, the normal to the membrane.  |
+-----------------------------+----------------+---------+------------------------------------------------------------------------------------+
| Name of the lipid of the    | str            | DMPC    | The name of the lipid positioned in the upper leaflet of the membrane.             |
| upper leaflet               |                |         |                                                                                    |
+-----------------------------+----------------+---------+------------------------------------------------------------------------------------+
| Name of the lipid of the    | str            | DMPC    | The name of the lipid positioned in the lower leaflet of the membrane.             |
| lower leaflet               |                |         |                                                                                    |
+-----------------------------+----------------+---------+------------------------------------------------------------------------------------+


-  :ref:`param-output-files`

Thermodynamics
^^^^^^^^^^^^^^
This section contains the following Plugins:

Density
'''''''

Temperature
'''''''''''

-  available for trajectories only

Trajectory
^^^^^^^^^^


Box Translated Trajectory
'''''''''''''''''''''''''

-  available for trajectories only


Center Of Masses Trajectory
'''''''''''''''''''''''''''

Cropped Trajectory
''''''''''''''''''

-  available for trajectories only



Global Motion Filtered Trajectory
'''''''''''''''''''''''''''''''''

+-----------------------------------+----------------------+----------+
|         Configuration             |        Format        | Default  |
+===================================+======================+==========+
| Make the chemical object          |      drop-down       |   None   |
+-----------------------------------+----------------------+----------+
| Make the configuration contiguous.|         bool         |   False  |
| This is done via MMTK universe's  |                      |          |
| contiguousObjectConfiguration()   |                      |          |
| method.                           |                      |          |
+-----------------------------------+----------------------+----------+


Rigid Body Trajectory
'''''''''''''''''''''
-  available for trajectories only

+--------------------------+-------+---------+
|      Configuration       | Format| Default |
+==========================+=======+=========+
| Number of Reference Frame| int   |   0     |
| used as reference.       |       |         |
+--------------------------+-------+---------+
| Remove Translation       | bool  |  False  |
+--------------------------+-------+---------+


Unfolded Trajectory
'''''''''''''''''''

-  available for trajectories only


Virtual Instruments
^^^^^^^^^^^^^^^^^^^

McStas Virtual Instrument
'''''''''''''''''''''''''

-  available for trajectories only

+----------------------------------------+--------------------------------------------+-------------------------------+
|            Configuration               |                 Format                     |           Default             |
+========================================+============================================+===============================+
| MDANSE Coherent Structure Factor       | str                                        | ..\\Data\\HDF\\dcsf_prot.nc   |
|                                        |                                            |                               |
+----------------------------------------+--------------------------------------------+-------------------------------+
| MDANSE Incoherent Structure Factor     | str                                        | ..\\Data\\HDF\\disf_prot.nc   |
|                                        |                                            |                               |
+----------------------------------------+--------------------------------------------+-------------------------------+
| Temperature                            | strictly positive float                    | 298.0                         |
|                                        |                                            |                               |
+----------------------------------------+--------------------------------------------+-------------------------------+
| Trace the 3D view of the simulation    | bool                                       | False                         |
|                                        |                                            |                               |
+----------------------------------------+--------------------------------------------+-------------------------------+
| McStas Instrument                      | drop-down                                  | None                          |
|                                        |                                            |                               |
+----------------------------------------+--------------------------------------------+-------------------------------+
| McStas Options                         |                                            |                               |
|   - Ncount                             | int                                        | 10000                         |
|                                        |                                            |                               |
|   - Dir                                | str                                        | None                          |
|                                        |                                            |                               |
+----------------------------------------+--------------------------------------------+-------------------------------+
| McStas Parameters                      | These options become visible once a McStas |                               |
|                                        | instrument has been chosen.                |                               |
+----------------------------------------+--------------------------------------------+-------------------------------+
-  mcstas parameters - these options become visible once a McStas
   instrument has been chosen.


Animation
^^^^^^^^^

Once double-clicked, it creates a new bar below Molecular Viewer that
allows you to watch the whole MD simulation.

+------------------------+-------------+-----------------------------------------------+
|   Control              |    Format   | Description                                   |
+========================+=============+===============================================+
|  Skip to the beginning |  button     | Sets frame number to 0.                       |
|                        |             |                                               |
+------------------------+-------------+-----------------------------------------------+
|   Play                 |  button     | Starts simulation at specified speed.         |
|                        |             |                                               |
+------------------------+-------------+-----------------------------------------------+
|   Skip to the end      |  button     | Sets frame number to the last frame.          |
|                        |             |                                               |
+------------------------+-------------+-----------------------------------------------+
|   Frame Selection      |  sliding bar| Allows selecting frames and displays frame    |
|   (Left)               |             | number.                                       |
|                        |             |                                               |
+------------------------+-------------+-----------------------------------------------+
|   Frame number (Box)   |  input box  | Allows viewing a frame by typing its index.   |
|                        |             | Press Enter to view the frame.                |
+------------------------+-------------+-----------------------------------------------+
|   Speed (Right)        |  sliding bar| Alters simulation speed and displays speed.   |
|                        |             |                                               |
+------------------------+-------------+-----------------------------------------------+
|   Speed (Box)          |   input box | Determines playback speed. Higher values for  |
|                        |             | faster playback.                              |
+------------------------+-------------+-----------------------------------------------+


.. _analysis-den-sup:

Density Superposition
^^^^^^^^^^^^^^^^^^^^^

-  available for trajectories only
-  appears only when :ref:`molecular-viewer` is active
   and you have left-clicked anywhere inside it

Double-clicking this opens the following window:

+------------------------+--------------+---------------------------------------------+
|    Configuration       |    Format    |                  Default                    |
+========================+==============+=============================================+
|     Select file        |   drop-down  |                 None                        |
|                        |              |                                             |
+------------------------+--------------+---------------------------------------------+
|         Shape          |     str      |           loaded from file                  |
|                        |              |                                             |
+------------------------+--------------+---------------------------------------------+
|    Rendering mode      |   drop-down  |                surface                      |
|                        |              |                                             |
+------------------------+--------------+---------------------------------------------+
|    Opacity level       |   float      |                 0.5                         |
|                        |   (0-1)      |                                             |
+------------------------+--------------+---------------------------------------------+
|    Contour Level       |  sliding bar |                 0                           |
|                        |              |                                             |
+------------------------+--------------+---------------------------------------------+
|       Clear button     |    button    | Removes the Density Superposition           |
|                        |              | from :ref:`molecular-viewer`.               |
|                        |              |                                             |
+------------------------+--------------+---------------------------------------------+
|        Draw button     |    button    | Adds Density Superposition on top of        |
|                        |              | :ref:`molecular-viewer`.                    |
|                        |              |                                             |
+------------------------+--------------+---------------------------------------------+


Trajectory Viewer
^^^^^^^^^^^^^^^^^

-  Available for trajectories only
-  appears only when :ref:`molecular-viewer` is active

+------------------------+-------------+-----------------------------------------------+
|     Configuration      |   Format    |              Description                      |
+========================+=============+===============================================+
|      Trajectory        |  drop-down  | Select the variable for plotting. Available   |
|                        |             | options include 3D variables from the         |
|                        |             | trajectory data, such as positions,           |
|                        |             | velocities, and gradients if present.         |
|                        |             |                                               |
+------------------------+-------------+-----------------------------------------------+
|         Atom           | positive int| Choose the atom index for variable plotting.  |
|                        |             | Utilize the arrows to navigate between atoms. |
|                        | Default: 0  | Input a number exceeding atom count selects   |
|                        |             | the last atom for plotting.                   |
|                        |             |                                               |
+------------------------+-------------+-----------------------------------------------+
|      Dimension         |  drop-down  | Specify the spatial component of the          |
|                        |             | selected variable to plot. For instance,      |
|                        |             | you can track the change in position of a     |
|                        |             | specific atom along the x, y, or z-axis       |
|                        |             | over time.                                    |
|                        |             |                                               |
+------------------------+-------------+-----------------------------------------------+
|     Clear button       |    button   | Click to remove all plotted lines from the    |
|                        |             | plot, providing a clean canvas for new data.  |
|                        |             |                                               |
+------------------------+-------------+-----------------------------------------------+
| Plot on same figure    |     Bool    | Control the number of lines that can be       |
|                        |             | simultaneously plotted. When checked (True),  |
|                        |             | multiple lines can be overlaid on the plot.   |
|                        | Def: False  | When unchecked (False), only one line can     |
|                        |             | be plotted at a time, replacing the current   |
|                        |             | line with each selection.                     |
|                        |             |                                               |
+------------------------+-------------+-----------------------------------------------+
|     Show legend        |     Bool    | Toggle the visibility of the legend. When     |
|                        |             | enabled (True), the legend appears in the     |
|                        |             | best-determined location by matplotlib.       |
|                        | Def: False  | When disabled (False), the legend is hidden.  |
|                        |             |                                               |
+------------------------+-------------+-----------------------------------------------+


My jobs
^^^^^^^

Plotter
^^^^^^^

.. _d3d-plotter-1:

2D/3D Plotter
'''''''''''''

-  available for analysis results only

Launches the 2D/3D Plotter inside the current tab of the working panel,
like below. For more information, please see :ref:`2d3dplotter`.

User definition
^^^^^^^^^^^^^^^

This section contains all the
definitions/`selections <#_Creating_selections>`__ that have been made
for the selected NetCDF file, serving similar purpose to `User
definition editor <#user_definitions_editor>`__.

Viewer
^^^^^^

.. _molecular-viewer:

Molecular Viewer
''''''''''''''''

-  available for trajectories only

Double-clicking on this option opens the Molecular Viewer plugin inside
the current tab of the `Working panel <#_Working_panel>`__. This shows a
simulated 3D view of the first frame of the trajectory. The Viewer can
be interacted with by dragging the simulation and zooming in/out. It can
be closed using the x button in the top right corner:

Clicking on an atom highlights it and prints out some basic information
about it in the Logger<link>. More options are available by
right-clicking anywhere inside the Molecular Viewer, which brings up the
following menu:

+------------------------+-------------+------------------------------------------------+
| Configuration          |    Format   | Description                                    |
+========================+=============+================================================+
| Rendering              | hover/click | Display options for system visualization.      |
+------------------------+-------------+------------------------------------------------+
| Show/hide selection box| button      | Create a selection box around the system.      |
|                        |             | Allows moving faces of the box for selection.  |
+------------------------+-------------+------------------------------------------------+
| Save selection         | button      | Save the selected atoms as a trajectory        |
|                        |             | selection using either click or selection box. |
+------------------------+-------------+------------------------------------------------+
| Clear selection        | button      | Deselect all atoms. Does not hide the box.     |
+------------------------+-------------+------------------------------------------------+
| Parallel projection    | toggle      | Toggle trimetric parallel projection of        |
|                        |             | the camera for unequally foreshortened view.   |
+------------------------+-------------+------------------------------------------------+
| Show/hide bounding box | toggle      | Toggle display of the simulation bounding box. |
+------------------------+-------------+------------------------------------------------+

Jobs
^^^^

When an analysis is started by clicking on the Run button, it appears as
a job in this panel, like so:

+------------------------+-------------+------------------------------------------------+
|   Field                |    Format   | Description                                    |
+========================+=============+================================================+
|   NAME                 |  unique ID  | Unique name assigned to the job. Also, a       |
|                        |  (button)   | button displaying selected analysis options.   |
+------------------------+-------------+------------------------------------------------+
|   PID                  |   number    | Process ID assigned by the operating system    |
|                        |             | to the job process.                            |
+------------------------+-------------+------------------------------------------------+
|   START                | date & time | Date and time when the job was started.        |
+------------------------+-------------+------------------------------------------------+
|   ELAPSED              |   time      | Time elapsed since the start of the job.       |
+------------------------+-------------+------------------------------------------------+
|   STATE                |  job state  | Job state: 'running', 'finished', or 'aborted'.|
|                        |  (button)   | Button shows traceback to error if 'aborted'.  |
+------------------------+-------------+------------------------------------------------+
|   PROGRESS             |   progress  | Approximate progress of the job.               |
+------------------------+-------------+------------------------------------------------+
|   ETA                  |   time      | Estimated time until job completion.           |
+------------------------+-------------+------------------------------------------------+
|   KILL                 |  (button)   | Button to cancel the job with confirmation.    |
+------------------------+-------------+------------------------------------------------+



