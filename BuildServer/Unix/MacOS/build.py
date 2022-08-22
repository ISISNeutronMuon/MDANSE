# coding=utf-8

import os
import sys

if sys.platform.startswith('darwin'):
    from setuptools import setup

    try:
        project_dir = os.environ['GITHUB_WORKSPACE']
    except KeyError:
        project_dir = sys.argv[3]
    try:
        version = os.environ['VERSION_NAME']
    except KeyError:
        version = sys.argv[5]

    APP = [os.path.join(project_dir,'Scripts','mdanse_gui')]

    PLIST = {
        u'CFBundleName': u'MDANSE',
        u'CFBundleShortVersionString': version,
        u'CFBundleVersion': version,
        u'CFBundleIdentifier': u'eu.ill.MDANSE-'+version,
        u'LSApplicationCategoryType': u'public.app-category.science',
        u'LSEnvironment': {u'PYTHONHOME': u'/Applications/MDANSE.app/Contents:'
                                          u'/Applications/MDANSE.app/Contents/Resources',
                           u'PYTHONPATH': u'/Applications/MDANSE.app/Contents/Resources/lib/python2.7:'
                                          u'/Applications/MDANSE.app/Contents/Resources/lib/python2.7/site-packages'}
    }

    try:
        temp_build = os.environ['CI_TEMP_BUILD_DIR']
    except KeyError:
        temp_build = sys.argv[7]
    try:
        temp_dir = os.path.join(os.environ['CI_TEMP_DIR'], 'dist')
    except KeyError:
        temp_dir = os.path.join(sys.argv[9], 'dist')

    OPTIONS = {
        'argv_emulation': False,# has to be False otherwise triggers problems with wxPython which lose some events that are captured by OS
        'iconfile': os.path.join(project_dir, 'Src', 'GUI', 'Icons', 'mdanse.icns'),
        'excludes': 'PyQt4',
		'matplotlib_backends': '-',
        'optimize': '1',
        'plist': PLIST,
        'bdist_base': temp_build,
        'dist_dir': temp_dir,
        'graph': False,
        'xref': False,
        'packages' : ["MDANSE","MMTK","Scientific","matplotlib", "netCDF4"]
    }

    setup(
        name='MDANSE',
        app=APP,
        options={'py2app': OPTIONS},
        setup_requires=['py2app']
    )
else:
    print 'No build_app implementation for your system.'
