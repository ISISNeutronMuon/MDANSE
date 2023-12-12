Installation
=============

MDANSE Installation Guide
-------------------------

MDANSE can be easily installed by following these steps:

Activate Virtual Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before proceeding, activate your Python virtual environment for MDANSE. If you don't
have a virtual environment set up, you can create one using `venv` or `virtualenv`.

Install MDANSE and MDANSE_GUI Packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use `pip` to install the MDANSE and MDANSE_GUI packages from the specified GitHub
repository:

.. code-block:: bash

   python3 -m pip install "git+https://github.com/ISISNeutronMuon/MDANSE@protos#egg=MDANSE&subdirectory=MDANSE"
   python3 -m pip install "git+https://github.com/ISISNeutronMuon/MDANSE@protos#egg=MDANSE_GUI&subdirectory=MDANSE_GUI"

Install PyQt6
~~~~~~~~~~~~~

Install PyQt6, which is a Python binding for the Qt library:

.. code-block:: bash

   pip install PyQt6

Run MDANSE
~~~~~~~~~~

You can now run MDANSE using the following command:

.. code-block:: bash

   mdanse_gui

This will launch the MDANSE Graphical User Interface (GUI), and you can start using
MDANSE for your analysis.

That's it! You have successfully installed MDANSE and are ready to use it for your
data analysis needs.

Windows
-------

Installing MDANSE on Windows is straightforward with the new pip-based installation
method. Follow these steps:

1. Open a Command Prompt with administrator privileges.

2. Run the following command to install MDANSE:

.. code-block:: bash

   pip install mdanse

3. The installation will begin and may take a few moments to complete.

MacOS
-----

On MacOS, you can also utilize the pip-based installation method:

1. Open a terminal window.

2. Run the following command to install MDANSE:

.. code-block:: bash

   pip install mdanse

3. The installation will be performed, and you can use MDANSE like any other
application once it's complete.

.. note:: Please note that since MDANSE is not registered with Apple, you might need
to take some additional steps to run it. You can refer to guides in Ref [Ref3] and Ref
[Ref4] for assistance if necessary.

Linux
-----

MDANSE offers a DEB package for Debian-based Linux systems, but the pip-based
installation is also available:

1. Open a terminal.

2. Run the following command to install MDANSE from the DEB package (replace
[MDANSE.deb] with the correct path and full name of the DEB file):

.. code-block:: bash

   sudo apt install ./MDANSE.deb

3. Apt will automatically handle any missing dependencies during installation.

4. After the installation is complete, you can start MDANSE either from the terminal
or the applications list.

.. note:: For systems that do not natively support DEB packages, building MDANSE from
source code may be necessary. You can find instructions for this in the "Building MDANSE
from Source Code" section and issue #8 on our GitHub [Ref5]. If you encounter
difficulties, please don't hesitate to contact us for assistance.
