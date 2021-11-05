if __name__ == "__main__":
    import sys
    import os

    script_dir = sys.argv[1]
    try:
        arg1 = str(sys.argv[2]).strip()
    except IndexError:
        os.system(str(os.path.join(script_dir, 'python')))

    if arg1 == '-c':
        exec(' '.join(sys.argv[3:]))

    elif arg1[:3] == '-m':
        if len(arg1) > 2:
            module = arg1[3:]
            args = list(sys.argv[3:])
        else:
            module = str(sys.argv[3])
            args = list(sys.argv[4:])

        for path in sys.path:
            if os.path.exists(os.path.join(path, module)) or os.path.exists(os.path.join(path, module + '.py')):
                command = [os.path.join(script_dir, 'python'), '-m', module]
                if args:
                    command.extend(args)
                os.system(' '.join(command))
                break
        else:
            raise OSError('No module named ' + module)

    else:
        execfile(arg1)
