# coding=utf-8

import os
import sys
import subprocess

if sys.platform.startswith('darwin'):
    from setuptools import setup

    try:
        project_dir = os.environ.get('GITHUB_WORKSPACE',
                                     os.environ['RUNNER_WORKSPACE'])
        version = os.environ['VERSION_NAME']
    except KeyError:
        project_dir = sys.argv[2]
        version = sys.argv[3]

    APP = [os.path.join(project_dir,'Scripts','mdanse_gui')]

    PLIST = {
        u'CFBundleName': u'MDANSE',
        u'CFBundleShortVersionString': version,
        u'CFBundleVersion': version,
        u'CFBundleIdentifier': u'eu.ill.MDANSE-'+version,
        u'LSApplicationCategoryType': u'public.app-category.science'
    }
    OPTIONS = {
        'argv_emulation': False,# has to be False otherwise triggers problems with wxPython which lose some events that are captured by OS
        'iconfile': os.path.join(project_dir,'MDANSE','GUI','Icons','mdanse.icns'),
        'excludes': 'PyQt4',
		'matplotlib_backends': '-',
        'optimize': '1',
        'plist': PLIST,
        'bdist_base': os.environ['CI_TEMP_BUILD_DIR'] or sys.argv[4],
        'dist_dir': os.path.join(os.environ['CI_TEMP_DIR'] or sys.argv[5],'dist'),
        'graph': False,
        'xref': False,
        'packages' : ["MDANSE","MMTK","Scientific","matplotlib"]
    }

    setup(
        name='MDANSE',
        app=APP,
        options={'py2app': OPTIONS},
        setup_requires=['py2app']
    )
else:
    print 'No build_app implementation for your system.'
