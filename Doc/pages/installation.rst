Section 4: Installation
=======================

MDANSE can be installed through the Python package manager, pip, in
the new version. This streamlined installation process eliminates
the need for platform-specific installers or manual compilation from
source code.

Below are the steps for installing MDANSE using pip:

.. code-block:: bash

pip install mdanse

This command will automatically download and install MDANSE along
with all the necessary libraries and files it requires to operate.
When that is done, you will see a welcome screen, followed by a
license agreement. The default installation location is in
C:\\Program Files\\MDANSE, but it can be changed to any location.

Once you select next, the installation will start, which may take
a while. Finally, you will see a screen where you can select some
extra options. If you want to have a desktop shortcut, don’t forget
to check the box. The ‘View CHANGELOG’ link at the bottom will open
CHANGELOG.txt file where you can see what has changed.

.. note:: ADD SETUP IMAGE HERE

4.1. Windows
-------------

Installing MDANSE on Windows has become even more straightforward
with the new pip-based installation method. You can follow these steps:

1. Open a Command Prompt with administrator privileges.

2. Run the following command to install MDANSE:

.. code-block:: bash

pip install mdanse

3. The installation will begin and may take a few moments to complete.

4.2. MacOS
----------

On MacOS, you can also utilize the pip-based installation method:

1. Open a terminal window.

2. Run the following command to install MDANSE:

.. code-block:: bash

pip install mdanse

3. The installation will be performed, and you can use MDANSE like
any other application once it's complete.

.. note:: Please note that since MDANSE is not registered with Apple,
you might need to take some additional steps to run it. You can refer
to guides in Ref [Ref3] and Ref [Ref4] for assistance if necessary.

4.3. Linux
----------

MDANSE offers a DEB package for Debian-based Linux systems, but
the pip-based installation is also available:

1. Open a terminal.

2. Run the following command to install MDANSE from the DEB package
(replace [MDANSE.deb] with the correct path and full name of the DEB file):

.. code-block:: bash

sudo apt install ./MDANSE.deb

Apt will automatically handle any missing dependencies during installation.

3. After the installation is complete, you can start MDANSE either from
the terminal or the applications list.

.. note:: For systems that do not natively support DEB packages, building
MDANSE from source code may be necessary. You can find instructions for
this in the "Building MDANSE from Source Code" section and issue #8 on
our GitHub [Ref5]. If you encounter difficulties, please don't hesitate
to contact us for assistance.