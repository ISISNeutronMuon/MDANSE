
Plotting Options
================

Plots
-----

In this section, we'll explore various plotting options tailored to MDANSE
(Molecular Dynamics Analysis for Neutron Scattering Experiments) data, helping
you effectively analyze and visualize your scientific findings.

Understanding Plotting Options
-------------------------------

**Line Plotter:**
    Visualize dynamic trends in MDANSE data, e.g., temperature fluctuations,
    energy profiles, or scattering intensities over time. Customize line styles,
    colors, and axes settings.

**Image Plotter:**
    Display MDANSE data as heatmaps or spatial distributions. Adjust aspect
    ratios, colormaps, and settings for neutron scattering patterns, electron
    density maps, or spatial correlations.

**Elevation Plotter:**
    Explore 3D MDANSE structures and landscapes. Zoom in on molecular
    structures and adjust contrast for detailed examination of complex systems,
    like biomolecules or nanomaterials.

**2D Slice Plotter:**
    Visualize specific 3D MDANSE data slices, focusing on dimensions and regions
    of interest. Simplify density profiles, radial distribution functions, or
    cross-sectional views of molecular assemblies.

**Iso Surface Plotter:**
    Create 3D surface visualizations with various rendering modes. Adjust opacity,
    contours, and slice orientations to highlight features in volumetric data,
    such as solvent density distributions or macromolecular structures.

Choosing the Right Plotting Option
----------------------------------

Selecting the appropriate plotting option is crucial for meaningful insights:

**Line Plotter:**
    For tracking temporal changes like temperature and energy during simulations.

**Image Plotter:**
    To display spatial information, such as scattering patterns, electron
    densities, or diffusion maps.

**Elevation Plotter:**
    Useful for gaining a 3D perspective on complex molecular structures,
    nanomaterials, or biomolecules.

**2D Slice Plotter:**
    When focusing on specific 3D data sections, aiding local property analysis.

**Iso Surface Plotter:**
    Great for rendering 3D volumetric data, highlighting complex structures like
    solvent-solute interfaces or protein conformations.


Line Plotter
~~~~~~~~~~~~

Toolbar
^^^^^^^

Data plotted with the Line Plotter will have the following menu beneath
the graph:

The top-row buttons, going from left to right, have the following
functions:


+--------------+------------------------------------------------------------+
| Button       | Function                                                   |
+==============+============================================================+
| Home         | Restores the plot to the default position.                 |
+--------------+------------------------------------------------------------+
| Back         | Undoes the latest action.                                  |
+--------------+------------------------------------------------------------+
| Forward      | Redoes the latest undone action.                           |
+--------------+------------------------------------------------------------+
| Pan          | Allows using the mouse to move the graph.                  |
+--------------+------------------------------------------------------------+
| Zoom         | Enables zooming in on a selected area.                     |
+--------------+------------------------------------------------------------+
| Subplots     | Opens the Configure subplots window for adjustments.       |
+--------------+------------------------------------------------------------+
| left         | Moves the left vertical axis to change the size.           |
+--------------+------------------------------------------------------------+
| bottom       | Moves the bottom horizontal axis to change the size.       |
+--------------+------------------------------------------------------------+
| right        | Moves the right vertical axis to change the size.          |
+--------------+------------------------------------------------------------+
| top          | Moves the top horizontal axis to change the size.          |
+--------------+------------------------------------------------------------+
| wspace       | Changes the vertical spacing between multiple graphs.      |
+--------------+------------------------------------------------------------+
| hspace       | Changes the horizontal spacing between multiple graphs.    |
+--------------+------------------------------------------------------------+
| Save         | Opens a file browser to save the graph in various formats. |
+--------------+------------------------------------------------------------+
| Offset value | Allows changing the y-axis offset.                         |
+--------------+------------------------------------------------------------+



-  **Subplots** opens the Configure subplots window, like the one below.
   It can be used to adjust various parameters of the whole graph. The
   red lines signify the original positions, while the blue bars show
   the current value. The values can be adjusted by clicking inside the
   relevant bar, and the blue bar will move to the clicked position.
   PLEASE NOTE that whatever changes you make are automatically applied
   and saved. There is no confirmation prompt when closing this window,
   and when it is reopened, the red bars will move to the new positions.
   The changes can only be reverted by using the **Back** or **Home**
   buttons.


Right-click menu
^^^^^^^^^^^^^^^^

Another way to adjust the plot is through a menu accessible through
right-clicking anywhere inside the tab:

+-------------+------------------------------------------------------------+
| Option      | Function                                                   |
+=============+============================================================+
| Clear       | Removes all the lines from the current graph.              |
+-------------+------------------------------------------------------------+
| Export data | Opens a file browser to save the data making up the graph. |
+-------------+------------------------------------------------------------+

-  **Export data** opens a file browser that can be used to save the
   data making up the graph. The exported data is in columns separated
   by spaces. The adjustments made that affect the data itself, such as
   changes in `units <#_Units>`__, are applied. This option is useful if
   you would like to plot the data using a software of your choice
   rather than the MDANSE plotter.

General settings
^^^^^^^^^^^^^^^^

Clicking on General settings in the above menu opens this window:

+---------+----------+-----------+---------------------------------------------------------+
| Setting | Format   | Default   | Description                                             |
+=========+==========+===========+=========================================================+
| Label   | Title    | str       | Sets a title for the graph, appearing above the figure. |
+---------+----------+-----------+---------------------------------------------------------+
| X Axis  | Format   | str       | Sets the x-axis label, appearing below the bottom axis. |
+---------+----------+-----------+---------------------------------------------------------+
| Y Axis  | Format   | str       | Sets the y-axis label, appearing below the bottom axis. |
+---------+----------+-----------+---------------------------------------------------------+
| Legend  | Show     | bool      | Toggles the legend's visibility.                        |
+---------+----------+-----------+---------------------------------------------------------+
|         | Location | drop-down | Sets the location of the legend on the graph.           |
+---------+----------+-----------+---------------------------------------------------------+
|         | Style    | Frame on  | Adds a frame around the legend.                         |
+---------+----------+-----------+---------------------------------------------------------+
|         |          | Fancy box | Slightly changes the legend frame/shadow.               |
+---------+----------+-----------+---------------------------------------------------------+
|         |          | Shadow    | Adds a shadow beneath the legend.                       |
+---------+----------+-----------+---------------------------------------------------------+
| Grid    | Style    | drop-down | Determines how the grid should look.                    |
+---------+----------+-----------+---------------------------------------------------------+
|         | Width    | int       | Sets the thickness of the grid lines.                   |
+---------+----------+-----------+---------------------------------------------------------+
|         | Color    | window    | Opens a window for advanced color selection.            |
+---------+----------+-----------+---------------------------------------------------------+


Axes settings
^^^^^^^^^^^^^

The Axes settings button in the right-click menu opens the following
window:


+----------------+----------+----------------+-------------------------------------------------+
| Setting        | Format   | Default        | Description                                     |
+================+==========+================+=================================================+
| Bounds         | X Min    | float          | Sets the x-axis minimum value.                  |
+----------------+----------+----------------+-------------------------------------------------+
|                | Y Min    | float          | Sets the y-axis minimum value.                  |
+----------------+----------+----------------+-------------------------------------------------+
|                | X Max    | float          | Sets the x-axis maximum value.                  |
+----------------+----------+----------------+-------------------------------------------------+
|                | Y Max    | float          | Sets the y-axis maximum value.                  |
+----------------+----------+----------------+-------------------------------------------------+
|                | Auto fit | button         | Restores values to their defaults for best fit. |
+----------------+----------+----------------+-------------------------------------------------+
| Unit and Scale | X        | str; drop-down | Sets the units for the x-axis.                  |
+----------------+----------+----------------+-------------------------------------------------+
|                | Y        | str; drop-down | Sets the units for the y-axis.                  |
+----------------+----------+----------------+-------------------------------------------------+



   -  **Auto fit** button restores all the above values to their
      defaults, ie. it adjusts the graph to the best fit, where all data
      is visible and least white space is left. It automatically applies
      the changes.
.

Lines settings
^^^^^^^^^^^^^^

The Lines settings button in the right-click menu opens the following
window:


+---------+--------+-----------+----------------------------------------------+
| Setting | Format | Default   | Description                                  |
+=========+========+===========+==============================================+
| Legend  | Format | str       | Sets the legend label for the selected line. |
+---------+--------+-----------+----------------------------------------------+
|         | Style  | drop-down | Determines how the line should look.         |
+---------+--------+-----------+----------------------------------------------+
|         | Width  | int       | Sets the width of the line.                  |
+---------+--------+-----------+----------------------------------------------+
|         | Color  | window    | Opens a window for advanced color selection. |
+---------+--------+-----------+----------------------------------------------+


Image Plotter
~~~~~~~~~~~~~

At the bottom of an Image Plotter is the menu below. The functions of
the buttons, from left to right, is below that.

The functions of the buttons, from left to right, are as follows:

+--------------+-------------------------------------------------------------------------------+
| Button       | Function                                                                      |
+==============+===============================================================================+
| Home         | Restores the plot to the default position.                                    |
+--------------+-------------------------------------------------------------------------------+
| Back         | Undoes the latest action.                                                     |
+--------------+-------------------------------------------------------------------------------+
| Forward      | Redoes the latest undone action.                                              |
+--------------+-------------------------------------------------------------------------------+
| Pan          | Allows using the mouse to move the graph.                                     |
+--------------+-------------------------------------------------------------------------------+
| Zoom         | Enables zooming in on a selected area.                                        |
+--------------+-------------------------------------------------------------------------------+
| Subplots     | Opens the Configure subplots window for adjustments.                          |
+--------------+-------------------------------------------------------------------------------+
| left         | Moves the left vertical axis to change the size of the plot.                  |
+--------------+-------------------------------------------------------------------------------+
| bottom       | Moves the bottom horizontal axis to change the size of the plot.              |
+--------------+-------------------------------------------------------------------------------+
| right        | Moves the right vertical axis to change the size of the plot.                 |
+--------------+-------------------------------------------------------------------------------+
| top          | Moves the top horizontal axis to change the size of the plot.                 |
+--------------+-------------------------------------------------------------------------------+
| wspace       | Changes the vertical spacing between multiple graphs (matplotlib subplots).   |
+--------------+-------------------------------------------------------------------------------+
| hspace       | Changes the horizontal spacing between multiple graphs (matplotlib subplots). |
+--------------+-------------------------------------------------------------------------------+
| Save         | Opens a file browser to save the graph in various formats.                    |
+--------------+-------------------------------------------------------------------------------+
| Slicing mode | When ticked, allows you to select any point in the plot.                      |
+--------------+-------------------------------------------------------------------------------+

By selecting a point, a cross appears on the plot, and a window with value plots is displayed.


-  **Subplots** opens the Configure subplots window, like the one below.
   It can be used to adjust various parameters of the whole graph. The
   red lines signify the original positions, while the blue bars show
   the current value. The values can be adjusted by clicking inside the
   relevant bar, and the blue bar will move to the clicked position.
   PLEASE NOTE that whatever changes you make are automatically applied
   and saved. There is no confirmation prompt when closing this window,
   and when it is reopened, the red bars will move to the new positions.
   The changes can only be reverted by using the **Back** or **Home**
   buttons. (The illustrations are of a line plot, but exactly the same
   happens to an Image Plot)

The buttons in the bottom bar work the same as the corresponding buttons
in the Image Plot. The other buttons work thusly:

-  **Auto Scale** adjusts the y-axis so that it contains 0.
-  **Single target plot** checkbox determines whether additional slices
   should be added to the same ‘Cross slicing’ window. It does not take
   effect immediately; if it is checked but the window is not closed,
   additional cross slices will be added to the plots in the opened
   window. However, if the box is checked then the window is closed, any
   cross slices made will open a new window where all the previously
   made slices are present plus the new one. In this case, the windows
   corresponding to older slices are not altered.

For illustration, if the box is unchecked or the window is not closed
after checking the box, only one ‘Cross slicing’ window will be open and
will change thusly (left to right) as further slices are performed:

|image39|\ |image40|\ |image41|

If the first window is closed after checking the box, new windows will
continue being created like so:



Right-click menu
^^^^^^^^^^^^^^^^

By right-clicking anywhere inside the axes, the following menu will
appear:


-  **Export data** opens a file browser that can be used to save the
   data making up the graph. The exported data is in columns separated
   by spaces. The adjustments made that affect the data itself, such as
   changes in `units <#_Units>`__, are applied. This option is useful if
   you would like to plot the data using a software of your choice
   rather than the MDANSE plotter.

Settings
^^^^^^^^

By clicking on Setting, the following window will open:

+----------------------+-----------+--------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Setting              | Format    | Default                                    | Description                                                                                                                                                               |
+======================+===========+============================================+===========================================================================================================================================================================+
| Label - Title        | str       | None                                       | Sets a title for the graph. This will appear above the figure.                                                                                                            |
+----------------------+-----------+--------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| X Axis               | str       | Name of the variable plotted on the x-axis | Sets the x-axis label. This will appear below the bottom ax, to the left of the x-axis units.                                                                             |
+----------------------+-----------+--------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Y Axis               | str       | Name of the first plotted variable         | Sets the y-axis label. This will appear below the bottom ax, to the left of the y-axis units.                                                                             |
+----------------------+-----------+--------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Aspect - Proportions | drop-down | auto                                       | Changes how the scale of the x-axis and y-axis is related. 'auto' automatically decides how to fit the plot, while 'equal' makes both axes range between the same values. |
+----------------------+-----------+--------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Interpolation Order  | drop-down | Nearest                                    | The algorithm to use for image scaling. For more information, see matplotlib documentation.                                                                               |
+----------------------+-----------+--------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Scale                | drop-down | none                                       | Changes the scale of the axes.                                                                                                                                            |
+----------------------+-----------+--------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Units - X            | str       | Depends on physical quantity               | The units that the data making up the graph is in. Both the plot and the axis label are adjusted once Apply is pressed.                                                   |
+----------------------+-----------+--------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Units - Y            | str       | Depends on physical quantity               | The units that the data making up the graph is in. Both the plot and the axis label are adjusted once Apply is pressed.                                                   |
+----------------------+-----------+--------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Apply Button         | -         | -                                          | Applies the changes without closing the window.                                                                                                                           |
+----------------------+-----------+--------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------+


Elevation Plotter
~~~~~~~~~~~~~~~~~

An elevation plot should look like this when opened:


You can use the mouse to drag the plot around to change the perspective,
a bit similar to how Pan would behave in Image Plotter when activated.
The plot can be zoomed in or out using the scrolling wheel or touchpad.

The **Scaling Panel** in the toolbar can be used to change the size of
the plot, either along x-axis or y-axis, depending on which part is
used. Please note, however, that it is possible that only a part of the
plot is initially visible, meaning the changes on screen are only a
side-effect of actual changes. Both the input field and the sliding bar
achieve the same purpose.

The **Elevation Panel** changes the contrast of the colours in the plot.
Both the input field and the sliding bar achieve the same purpose.

The **Save current view** button opens a file browse, allowing the
current contents of the screen (inside the plot, ie. not toolbar) to be
saved as a PNG file.

2D Slice Plotter
~~~~~~~~~~~~~~~~

This plotter was created to help visualising the 3D trajectory
variables, configuration, velocities, and gradients. It creates a 2D
plot of a 3D variable. Therefore, extra setup is required before it can
be used, and so it looks as follows in the Data panel:

-  **Dim**

*Format:* positive int

*Default:* 0

*Description:* the dimension that will appear as the colour gradient in
the plot. The other two dimensions will be plotted on the x and y axes
of the plot. Only values 0, 1, and 2 are accepted. Which dimension is
which number can be determined from the ‘Axis’ column in the Data panel
if it is populated, or the ‘Size’ column if the former is not. The
dimensions are assigned number in the order in which they appear, so,
e.g., if ‘Axis’ column shows ‘time,atom,dim’, then time is 0, atom is 1,
and dim is 3.

-  **Slice**

*Format:* positive int

*Default:* 0

*Description:* the part of the dimension that is plotted. Only values
from 0 to the size of the dimension are accepted. For example, if Dim
corresponding to the dimension of the configuration variable (i.e., the
x, y, or z component) is selected, then the Slice field corresponds to
those x/y/z components. Thus, if in this example, we select Slice of 1
(i.e., the y component), then we get a 2D plot with time and the number
of atoms on the x and y axes, and the colour gradient corresponds to the
y-component of the position vectors (picture below).

When this plotter is configured with the above options and plotted, a
plot similar to below will be obtained.

For the description of the various manipulations of this plot, please
see `Image Plotter <#_Image_Plotter>`__. 2D Slice Plotter uses Image
Plotter under the hood, meaning that the various options are identical.

Iso Surface Plotter
~~~~~~~~~~~~~~~~~~~

You can use the mouse to drag the plot around to move the 3D picture. The plot can be zoomed in or out using the scrolling wheel or touchpad.

Settings
--------

+-------------------+-----------------+---------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Setting           | Format          | Default | Description                                                                                                                                                                                                         |
+===================+=================+=========+=====================================================================================================================================================================================================================+
| Rendering Mode    | Drop-down       | Line    | Changes which geometric shapes (points, lines, surface) are used to display the surface.                                                                                                                            |
+-------------------+-----------------+---------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Opacity Level     | Float (0-1)     | 1.0     | Changes the opacity/transparency of the objects used to display the surface.                                                                                                                                        |
+-------------------+-----------------+---------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Contour Level     | Sliding Bar     | Middle  | Changes how much space the shapes making the surface take.                                                                                                                                                          |
+-------------------+-----------------+---------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Slice Orientation | Multiple Choice | None    | Adds a colored plane described by the shown axes that slices through the surface. After clicking on the plot, the plane can be moved along the axis not mentioned in the chosen plane’s name by using + and – keys. |
+-------------------+-----------------+---------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Save Current View | Button          |  -      | Opens a file browser that allows the current view to be saved as a PNG file.                                                                                                                                        |
+-------------------+-----------------+---------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
