# coding=utf-8
import sys
import os

if sys.platform.startswith('darwin'):
    from setuptools import setup

    build_name = os.environ['BUILD_NAME']
    rev_number = os.environ['REV_NUMBER']
    version = build_name + " v" + rev_number

    APP = ['../../../Scripts/mdanse_gui']

    PLIST = {
        u'CFBundleName': u'MDANSE',
        u'CFBundleShortVersionString': build_name,
        u'CFBundleVersion': version,
        u'CFBundleIdentifier': u'eu.ill.MDANSE-'+build_name,
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
