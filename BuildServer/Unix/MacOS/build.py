# coding=utf-8

import argparse
import os
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--project_dir')
parser.add_argument('--version')
parser.add_argument('--temp_build_dir')
parser.add_argument('--temp_dir')
args, pyapp = parser.parse_known_args()

if sys.platform.startswith('darwin'):
    from setuptools import setup

    try:
        project_dir = os.environ['GITHUB_WORKSPACE']
    except KeyError as e:
        project_dir = args.project_dir.replace("'", '').replace('"', '')
        print e
    try:
        version = os.environ['VERSION_NAME']
    except KeyError:
        version = args.version.replace("'", '').replace('"', '')

    APP = [os.path.join(project_dir, 'Scripts', 'mdanse_gui')]

    PLIST = {
        u'CFBundleName': u'MDANSE',
        u'CFBundleShortVersionString': version,
        u'CFBundleVersion': version,
        u'CFBundleIdentifier': u'eu.ill.MDANSE-'+version,
        u'LSApplicationCategoryType': u'public.app-category.science'
    }

    try:
        temp_build_dir = os.environ['CI_TEMP_BUILD_DIR']
    except KeyError:
        temp_build_dir = args.temp_build_dir.replace("'", '').replace('"', '')
    try:
        temp_dir = os.path.join(os.environ['CI_TEMP_DIR'],'dist')
    except KeyError:
        temp_dir = args.temp_dir.replace("'", '').replace('"', '')

    OPTIONS = {
        'argv_emulation': False,# has to be False otherwise triggers problems with wxPython which lose some events that are captured by OS
        'iconfile': os.path.join(project_dir,'MDANSE','GUI','Icons','mdanse.icns'),
        'excludes': 'PyQt4',
		'matplotlib_backends': '-',
        'optimize': '1',
        'plist': PLIST,
        'bdist_base': temp_build_dir,
        'dist_dir': temp_dir,
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
