Tutorial: Get started (Installation)
====================================

.. _installation_tutorial:

MDANSE Installation Steps
--------------------------

MDANSE can be easily installed by following these steps:

Create Virtual Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~
To create your Python virtual environment for MDANSE use `venv` or `virtualenv`.

Open a Terminal or Command Prompt.

Navigate to Your Project Directory (Optional): If you have a specific
project directory where you want to work with MDANSE, navigate to that
directory using the ``cd`` command. For example:

.. code-block:: bash

   cd path/to/your/project/directory

Create a Virtual Environment: To create a virtual environment named
``mdanse``, use the following command:

.. code-block:: bash

   python3 -m venv mdanse


Activate Virtual Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After creating the virtual environment, you need to activate it to use MDANSE within this isolated environment. The
activation command varies by operating system:

- On macOS and Linux:

  .. code-block:: bash

     source mdanse/bin/activate

- On Windows:

  .. code-block:: console

     mdanse\Scripts\activate

Install MDANSE Package
~~~~~~~~~~~~~~~~~~~~~~

Use `pip` to install the MDANSE package from the specified GitHub repository:

.. code-block:: bash

   pip install MDANSE

Install MDANSE_GUI Package
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Similarly, install the MDANSE_GUI package using `pip`:

.. code-block:: bash

   pip install MDANSE_GUI

Run MDANSE
~~~~~~~~~~

You can now start using MDANSE by running the following command:

.. code-block:: bash

   mdanse_gui

Run MDANSE
~~~~~~~~~~

You can now start using MDANSE by running the following command:

.. code-block:: bash

   mdanse_gui

This will launch the MDANSE Graphical User Interface (GUI), and you can start using MDANSE for your
analysis.

Note for Windows Users: On Windows, the command to run MDANSE may need to be:

.. code-block:: bash

   python3 mdanse_gui

That's it! You have successfully installed MDANSE and are ready to use it for your data analysis needs.
