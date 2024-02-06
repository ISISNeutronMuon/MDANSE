Plotting Information
=====================

Line Plotter
~~~~~~~~~~~~

Toolbar
^^^^^^^

Data plotted with the Line Plotter will have the following menu beneath
the graph:

Settings in table below:
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
Settings in table below:
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

Settings in table below:
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

Axis setting in table below:
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


Lines settings
^^^^^^^^^^^^^^
The Lines settings button in the right-click menu opens the following window:
The Lines box is a list of all lines in the figure. Delete removes line from graph.

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
At the bottom of an Image Plotter is the menu below. 
See table below:

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

By selecting a point, a cross appears on the plot, and a window with
value plots is displayed.

-  **Subplots**: Opens the "Configure subplots" window. It allows you
   to adjust various graph parameters. The red lines indicate original
   positions, and blue bars show current values, which you can modify
   by clicking on them. Changes are automatically applied and saved
   without confirmation prompts. Reverting changes is possible using
   the **Back** or **Home** buttons.

The buttons in the bottom bar work similarly to those in the Image Plot.

-  **Auto Scale**: Adjusts the y-axis to include 0.
-  **Single target plot** checkbox: Determines whether additional
   slices should be added to the same 'Cross slicing' window. Changes
   take effect when the window is closed, opening a new window if the
   box is checked.

For illustration, if the box is unchecked or the window is not closed
after checking, only one 'Cross slicing' window will be open and will
change as further slices are performed.


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


See table below for additional settings and options:
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
~~~~~~~~~~~~~~~~~~~
The data panel looks as follows:

+-------------+----------------+---------+------------------------------------------------------+
| Setting     | Format         | Default | Description                                          |
+=============+================+=========+======================================================+
| Dim         | Positive Int   | 0       | Dimension for color gradient in the plot. Values: 0, |
|             |                |         | 1, 2. Assigned based on order (e.g.,                 |
|             |                |         | 'time,atom,dim' → time=0, atom=1, dim=2).            |
+-------------+----------------+---------+------------------------------------------------------+
| Slice       | Positive Int   | 0       | Part of the dimension plotted. Values: 0 to          |
|             |                |         | dimension size. For example, if Dim is a             |
|             |                |         | configuration variable (x, y, or z), Slice           |
|             |                |         | determines which component to plot.                  |
+-------------+----------------+---------+------------------------------------------------------+

**Dim**
The dimension that determines the color gradient in the plot. It accepts
values of 0, 1, and 2. You can discern which dimension corresponds to each
number from the 'Axis' column in the Data panel, if available, or from the
'Size' column if 'Axis' is not populated. Dimensions are assigned numbers
based on their order of appearance. For example, if 'Axis' lists 'time,
atom, dim,' then time is 0, atom is 1, and dim is 2.

**Slice**
Slice selects a portion of the dimension to be plotted, with accepted values
ranging from 0 to the size of the dimension. When Dim corresponds to a
configuration variable like the x, y, or z component, the Slice field
corresponds to these components. For instance, selecting Slice 1
(representing the y component) results in a 2D plot with time and the number
of atoms on the x and y axes. In this case, the color gradient corresponds
to the y-component of the position vectors.

once above options configured, plot similar to below will show:



Iso Surface Plotter
~~~~~~~~~~~~~~~~~~~
When opened, this plotter might look like this:

You can use the mouse to drag the plot around to move the 3D picture. The plot can be zoomed in or out using the scrolling wheel or touchpad.

Settings
--------
See table below for additional settings and options:
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
