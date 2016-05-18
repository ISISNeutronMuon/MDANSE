# coding=utf-8
import sys
import os

if sys.platform.startswith('darwin'):
    from setuptools import setup

    version = os.environ['VERSION_NAME']

    APP = ['../../../Scripts/mdanse_gui']

    PLIST = {
        u'CFBundleName': u'MDANSE',
        u'CFBundleShortVersionString': version,
        u'CFBundleVersion': version,
        u'CFBundleIdentifier': u'eu.ill.MDANSE-'+version,
        u'LSApplicationCategoryType': u'public.app-category.science'
    }
    OPTIONS = {
        'argv_emulation': True,
        'iconfile': u'../../../MDANSE/GUI/Icons/mdanse.icns',
        'excludes': 'PyQt4',
		'matplotlib_backends': '-',
        'optimize': '1',
        'plist': PLIST,
        'bdist_base': '../Build/build',
        'dist_dir': '../Build/dist',
        'graph': False,
        'xref': False
    }

    setup(
        name="MDANSE",
        app=APP,
        options={'py2app': OPTIONS},
        setup_requires=['py2app']
    )
else:
   print 'No build_app implementation for your system.'
