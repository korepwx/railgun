#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/runner/host.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import os
import copy

from . import runconfig
from railgun.common.osutil import ProcessTimeout, execute
from railgun.common.tempdir import TempDir


class BaseHost(object):
    """Basic handin running host, manage a working directory."""

    def __init__(self, uuid, hw, lang):
        """Create a host to store testing module."""
        self.tempdir = TempDir(uuid)

        # store hw & code instance
        self.hw = hw
        self.hwcode = hw.get_code(lang)

        # store compiler & runner settings
        self.compiler_params = self.hwcode.compiler_params
        self.runner_params = self.hwcode.runner_params

    def __enter__(self):
        """Initialize the host directory"""
        self.tempdir.open()
        return self

    def __exit__(self, ignore1, ignore2, ignore3):
        self.tempdir.close()

    def compile(self):
        """Compile this testing module."""
        pass

    def run(self):
        """Run this testing module."""


class PythonHost(BaseHost):
    """Python handin running host"""

    def __init__(self, uuid, hw):
        super(PythonHost, self).__init__(uuid, hw, 'python')

        # PYTHONPATH of this running environment
        self.python_path = [
            runconfig.RAILGUN_ROOT,
            os.path.join(runconfig.RUNLIB_DIR, 'python')
        ]

        # get interested config values of this task
        self.entry = self.runner_param.get('entry')
        self.entry_path = os.path.join(self.tempdir.path, self.entry)

    def compile(self):
        pass

    def run(self):
        """Run this Python testing module."""
        try:
            # setup new PYTHONPATH environment
            python_path = os.environ.get('PYTHONPATH', None)
            if (not python_path):
                python_path = []
            python_path = os.pathsep.join(self.python_path + python_path)
            env = copy.copy(os.environ)
            env['PYTHONPATH'] = python_path
            # execute the testing module
            execute(
                ['python', self.entry_path],
                runconfig.RUNNER_DEFAULT_TIMEOUT,
                cwd=self.tempdir.path,
                env=env,
                close_fds=True
            )
        except ProcessTimeout:
            raise
