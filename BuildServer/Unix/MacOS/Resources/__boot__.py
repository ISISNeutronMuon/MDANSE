def _reset_sys_path():
    # Clear generic sys.path[0]
    import sys
    import os

    resources = os.environ['RESOURCEPATH']
    while sys.path[0] == resources:
        del sys.path[0]


_reset_sys_path()


def _update_path():
    import os
    import sys

    resources = os.environ['RESOURCEPATH']
    sys.path.append(os.path.join(
        resources, 'lib', 'python%d.%d' % (
            sys.version_info[:2]), 'lib-dynload'))
    sys.path.append(os.path.join(
        resources, 'lib', 'python%d.%d' % (
            sys.version_info[:2])))
    sys.path.append(os.path.join(
        resources, 'lib', 'python%d.%d' % (
            sys.version_info[:2]), 'site-packages.zip'))


_update_path()


""" Add Apple's additional packages to sys.path """


def add_system_python_extras():
    import site
    import sys

    ver = '%s.%s' % (sys.version_info[:2])

    site.addsitedir(
        '/System/Library/Frameworks/Python.framework/Versions/'
        '%s/Extras/lib/python' % (ver,))


add_system_python_extras()


def _chdir_resource():
    import os
    os.chdir(os.environ['RESOURCEPATH'])


_chdir_resource()


def _disable_linecache():
    import linecache

    def fake_getline(*args, **kwargs):
        return ''

    linecache.orig_getline = linecache.getline
    linecache.getline = fake_getline


_disable_linecache()


import re
import sys

cookie_re = re.compile(b"coding[:=]\s*([-\w.]+)")
if sys.version_info[0] == 2:
    default_encoding = 'ascii'
else:
    default_encoding = 'utf-8'


def guess_encoding(fp):
    for i in range(2):
        ln = fp.readline()

        m = cookie_re.search(ln)
        if m is not None:
            return m.group(1).decode('ascii')

    return default_encoding


def _run():
    global __file__
    import os
    import site  # noqa: F401
    sys.frozen = 'macosx_app'
    base = os.environ['RESOURCEPATH']

    argv0 = os.path.basename(os.environ['ARGVZERO'])
    script = SCRIPT_MAP.get(argv0, DEFAULT_SCRIPT)  # noqa: F821

    path = os.path.join(base, script)
    sys.argv[0] = __file__ = path
    if sys.version_info[0] == 2:
        with open(path, 'rU') as fp:
            source = fp.read() + "\n"
    else:
        with open(path, 'rb') as fp:
            encoding = guess_encoding(fp)

        with open(path, 'r', encoding=encoding) as fp:
            source = fp.read() + '\n'

        BOM = b'\xef\xbb\xbf'.decode('utf-8')
        if source.startswith(BOM):
            source = source[1:]

    exec(compile(source, path, 'exec'), globals(), globals())


import os
os.environ['MATPLOTLIBDATA'] = os.path.join(
    os.environ['RESOURCEPATH'], 'mpl-data')


def _setup_ctypes():
    from ctypes.macholib import dyld
    import os
    frameworks = os.path.join(os.environ['RESOURCEPATH'], '..', 'Frameworks')
    dyld.DEFAULT_FRAMEWORK_FALLBACK.insert(0, frameworks)
    dyld.DEFAULT_LIBRARY_FALLBACK.insert(0, frameworks)


_setup_ctypes()


DEFAULT_SCRIPT='mdanse_gui'
SCRIPT_MAP={}
_run()
