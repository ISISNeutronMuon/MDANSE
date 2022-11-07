
Building MDANSE from source code
================================

.. note::
   The MDANSE branch 1.5.x is still based on Python 2.
   At the time this manual has been written, in 2022,
   this makes it extremally difficult to find all the
   necessary software dependencies.
   It is strongly recommended to install a pre-built
   package for your operating system instead of
   building MDANSE from source yourself.
   A new version of MDANSE, based on Python 3,
   is currently under development.

MDANSE is an open-source software, and so the source code is widely
available. Currently, it is hosted by ISIS at GitHub
[`38 <#SignetBibliographie_038>`__]. The code can be freely altered and
distributed as per the GPL-3.0 license that it is licensed under. All
the necessary information is present in the repository. In any case
though, to access the very latest features that have not been released
via an executable, or to make custom alterations to the code, it is
necessary to build MDANSE from source code. Below are instructions on
how to do that on major platforms using Python 2. Please note that as of
writing this guide, MDANSE is compatible only with Python 2, but works
are under way to transfer MDANSE to Python 3, so in the future the code
in the repository may require different compilation instructions.

.. _windows-2:

Windows
~~~~~~~

To build MDANSE on Windows, the following software will have to be
downloaded and installed. All three programs have executables which can
be used in the typical windows fashion.

-  Miniconda [`39 <#SignetBibliographie_039>`__] (or any other conda
   installation)

-  Microsoft Visual Studio 2008 [`40 <#SignetBibliographie_040>`__]

   -  If MDANSE is to be built on an x64 system, during this
      installation, the ‘x64 Compilers and Tools’ option has to be
      selected. Alternatively, the complete installation can be
      selected, which will install all parts including this one.

Then, download the following wheels from Ref
[`41 <#SignetBibliographie_041>`__], selecting the appropriate version
based on your architecture. The asterisks in the names stand for
architecture.

-  wxPython_common‑3.0.2.0‑py2‑none‑any.whl
-  wxPython‑3.0.2.0‑cp27‑none‑win*.whl
-  PyQt4-4.11.4-cp27-cp27m-win*.whl
-  VTK-6.3.0-cp27-cp27m-win*.whl

Afterwards, a virtual environment can be created and the wheels as well
as other dependencies can be installed into it.

.. code-block:: console

    conda create --name envname python=2.7
    conda activate envname
    conda install h5py netCDF4
    pip install numpy==1.16.6 matplotlib==2.2.5 Cython==0.29.24 Pyro
    wxPython_common‑3.0.2.0‑py2‑none‑any.whl
    wxPython‑3.0.2.0‑cp27‑none‑win_amd64.whl
    VTK‑6.3.0‑cp27‑cp27m‑win_amd64.whl PyQt4‑4.11.4‑cp27‑cp27m‑win_amd64.whl

Then, ScientificPython can be installed into the virtual environment.
This has to be done from source, using an ILL version of
ScientificPython.

.. code-block:: console

    git clone https://code.ill.fr/scientific-software/scientific-python.git
    cd scientific-python
    python setup.py --netcdf_prefix=dir_h --netcdf_dll=dir_dll build install

In the second line, dir_h stands for the directory where the netcdf.h
file exists, and dir_dll for the location of netcdf.dll. The location of
both these files is inside the environment. If Miniconda was installed
into the default location, the .h file should be located in
C:\\Users\\username\\Miniconda\\envs\\envname\\Library\\include\\ and
.dll in C:\\Users\\username\\Miniconda\\envs\\envname\\Library\\bin\\
where username and envname are variable.

If an error is encountered pointing out that the location of netcdf.lib
file cannot be found, then the setup.py file has to be edited. Changing
the line 86, which should read netcdf_lib = netcdf_dll, to netcdf_lib =
r'path', where path is the path to said file should fix the issue.
Alternatively, the line can be replaced with the following code:

.. code-block:: python

    if os.path.exists(os.path.join(netcdf_dll, 'netcdf.lib')):
        netcdf_lib = netcdf_dll
    elif os.path.exists(os.path.join(os.path.dirname(netcdf_dll), 'lib',
    'netcdf.lib')):
        netcdf_lib = os.path.join(os.path.dirname(netcdf_dll), 'lib')
    else:
        print "netcdf.lib could not be found"
        raise SystemExit

Any other errors can be attempted to be solved by running "C:\\Program
Files (x86)\\Microsoft Visual Studio 9.0\\VC\\bin\\vcvars32.bat" on x32
systems and "C:\\Program Files (x86)\\Microsoft Visual Studio
9.0\\VC\\bin\\amd64\\vcvarsamd64.bat" on x64 systems. If a missing
vcvarsall.bat error is encountered after that, Visual Studio 2008 might
have to be reinstalled (not to forget to install the x64 Tools).

Once ScientificPython is installed successfully, MMTK and MDANSE can be
built and installed from source.

.. code-block:: console
    
    git clone https://code.ill.fr/scientific-software/mmtk.git
    cd mmtk
    python setup.py install
    git clone https://github.com/ISISNeutronMuon/MDANSE.git
    cd MDANSE
    python setup.py build install

After that, MDANSE can be used from command line as per usual, and the
GUI can be started by running

.. code-block:: console

    python path\\envname\\Scripts\\mdanse_gui

.. _macos-2:

MacOS
~~~~~

Like on Windows, on MacOS the easiest way to build MDANSE is to use
conda all the way, which can be downloaded from Ref
[`42 <#SignetBibliographie_042>`__]. A virtualenv/venv environment can
be used but conda still has to be used to download multiple packages
unless they are built from source. This guide uses conda fully.

First, create a conda virtual environment and install dependencies
(envname can be whatever name desirable for the environment).

.. code-block:: console

    conda create --name envname python=2.7
    conda activate envname
    conda install h5py netCDF4
    pip install numpy==1.16.6 matplotlib==2.2.5 Cython==0.29.24 Pyro pyyaml
    sudo conda install -y -c daf wxpython
    sudo conda install -y -c ccordoba12 vtk

Afterwards, ScientificPython, MMTK, and MDANSE can be built and
installed from source code. Please note that the NETCDF_HEADER_FILE_PATH
below has to be set to the location of the directory of netcdf.h.

.. code-block:: console

    export NETCDF_HEADER_FILE_PATH=/Users/username/Miniconda/envs/envname/include
    git clone https://code.ill.fr/scientific-software/scientific-python.git
    cd scientific-python/
    python setup.py install
    git clone https://code.ill.fr/scientific-software/mmtk.git
    cd mmtk
    spython setup.py install
    git clone https://github.com/ISISNeutronMuon/MDANSE.git
    cd MDANSE
    python setup.py install

If there are any permission issues, the installation will have to be
performed with elevated privileges and full path to python, ie.
path/envname/bin/python. Afterwards, MDANSE can be used from command
line like normal, and the GUI can be started by running:

.. code-block:: console

    path/envname/bin/mdanse_gui

.. _linux-2:

Linux
~~~~~

The installation on various linux platforms is similar to that on MacOS,
with the main difference being what the required libraries are called.
This also differs a lot between various linux distributions, and many
may already be installed. Further, which libraries have to be installed
depends if you plan to build Python, wxpython, and VTK from source. In
any case, what is always required is a C compiler, preferably GTK2, and
netcdf. A development version of netcdf, something like netcdf-devel,
may also be necessary. An exact guide for when everything is built from
source on CentOS 7 is on MDANSE GitHub issue #8
[`5 <#SignetBibliographie_005>`__]. Other than that, we do not keep
instructions specific to any other distributions, though inspiration can
be taken from our continuous integration pipeline at
.github/workflows/CI.yml.

Given this complexity and other reasons, it is advisable that conda is
used for building MDANSE, which makes installing packages much simpler
and should reduce the dependence on distribution somewhat. The steps to
follow are such:

.. code-block:: console

    conda create --name envname python=2.7
    conda activate envname
    conda install h5py netCDF4
    pip install numpy==1.16.6 matplotlib==2.2.5 Cython==0.29.24 Pyro pyyaml
    sudo conda install -y -c daf wxpython
    sudo conda install -y -c ccordoba12 vtk
    export NETCDF_HEADER_FILE_PATH=/usr/include/
    git clone https://code.ill.fr/scientific-software/scientific-python.git
    cd scientific-python/
    python setup.py install
    git clone https://code.ill.fr/scientific-software/mmtk.git
    cd mmtk
    spython setup.py install
    git clone https://github.com/ISISNeutronMuon/MDANSE.git
    cd MDANSE
    python setup.py install

