#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: manage.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is distributed under 2-clause BSD license which can be found in
# LICENSE.txt

import sys
from cStringIO import StringIO


class App(object):

    def __init__(self):
        pass

    def _usage(self):
        # Gather all actions
        options = []
        for k in dir(self):
            v = getattr(self, k)
            if (callable(v) and not k.startswith('_') and v.__doc__):
                options.append((k.replace('_', '-'), v.__doc__))
        options = sorted(options)
        options = '\n'.join(['  %-16s%s' % (k, m) for k, m in options])
        # Print the help message
        print(
            'manage.py action [options ...]\n'
            '\n'
            'Options:\n' + options
        )
        sys.exit(0)

    def _call(self, argv):
        """Call with command line `argv`."""
        if (len(argv) < 1):
            self._usage()
        # Get the method
        method = argv[0]
        m = getattr(self, method.replace('-', '_'), None)
        if (not m):
            self._usage()
        else:
            m(argv[1:])

    def build_cache(self, argv):
        """Build all cache of Railgun system."""
        from railgun.maintain.hwcache import HwCacheTask
        from railgun.maintain.tzcache import TzCacheTask

        io = StringIO()
        # HwCache
        task = HwCacheTask(logstream=io)
        task.execute()
        task.logflush()
        # TzCache
        io.write('-' * 70)
        io.write('\n')
        task = TzCacheTask(logstream=io)
        task.execute()
        task.logflush()
        sys.stdout.write(io.getvalue())

    def runner_perm(self, argv):
        """Check the permissions of runner host."""
        from railgun.maintain.permissions import RunnerPermissionCheckTask

        io = StringIO()
        task = RunnerPermissionCheckTask(logstream=io)
        task.execute()
        task.logflush()
        sys.stdout.write(io.getvalue())


# search the index
app = App()
app._call(sys.argv[1:])
