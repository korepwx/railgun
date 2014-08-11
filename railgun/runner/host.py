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
from .context import logger
from .errors import RunnerError, InternalServerError, FileDenyError, \
    RunnerTimeout
from railgun.common.hw import FileRules
from railgun.common.fileutil import dirtree, remove_firstdir
from railgun.common.osutil import ProcessTimeout, execute
from railgun.common.tempdir import TempDir


class BaseHost(object):
    """Basic handin running host, manage a working directory."""

    def __init__(self, uuid, hw, lang):
        """Create a host to store testing module."""
        self.tempdir = TempDir(uuid)
        self.uuid = uuid

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
        #self.tempdir.close()
        pass

    def compile(self):
        """Compile this testing module."""
        pass

    def run(self):
        """Run this testing module. Should return (exitcode, stdout, stderr)"""

    def prepare_hwcode(self):
        """Copy files from hw.code directory into tempdir."""

        try:
            self.tempdir.copyfiles(self.hwcode.path, dirtree(self.hwcode.path))
        except Exception:
            logger.exception(
                'Cannot copy code files into tempdir for homework %(hwid)s '
                'when executing handin %(handid)s.' %
                {'hwid': self.hw.uuid, 'handid': self.uuid}
            )
            raise InternalServerError()

    def extract_handin(self, archive):
        """Extract handin archive files into tempdir."""

        try:
            # if the archive contains only one dir, remove first dir from path
            onedir = archive.onedir()
            canonical_path = remove_firstdir if onedir else (lambda s: s)

            # use hwcode.file_rules to filter archive files
            def should_skip(path):
                path = canonical_path(path)
                # First, check the rules in HwCode
                action = self.hwcode.file_rules.get_action(
                    path, default_action=-1
                )
                if (action == FileRules.DENY):
                    raise FileDenyError(path)
                if (action == FileRules.ACCEPT):
                    return False
                if (action != -1):
                    # action is not None, and action != ACCEPT, this means
                    # that rules in `hwcode` rejects this file.
                    return True
                # Next, check the rules in Homework
                action = self.hw.file_rules.get_action(
                    path, default_action=FileRules.LOCK
                )
                if (action == FileRules.DENY):
                    raise FileDenyError(path)
                return (action != FileRules.ACCEPT)

            # now extract the archive files
            self.tempdir.extract(archive, should_skip)
        except RunnerError:
            raise
        except Exception:
            logger.exception(
                'Cannot extract archive into tempdir for homework %(hwid)s '
                'when executing handin %(handid)s.' %
                {'hwid': self.hw.uuid, 'handid': self.uuid}
            )
            raise InternalServerError()


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
        self.entry = self.runner_params.get('entry')
        self.entry_path = os.path.join(self.tempdir.path, self.entry)

    def compile(self):
        pass

    def run(self):
        """Run this Python testing module."""
        try:
            # setup new PYTHONPATH environment
            python_path = os.environ.get('PYTHONPATH', None)
            if (not python_path):
                python_path = self.python_path
            else:
                python_path = self.python_path + [python_path]
            python_path = os.pathsep.join(python_path)
            env = copy.copy(os.environ)
            env['PYTHONPATH'] = python_path
            # Setup other environment variables
            env['RAILGUN_API_BASEURL'] = runconfig.WEBSITE_API_BASEURL
            env['RAILGUN_ROOT'] = runconfig.RAILGUN_ROOT
            env['RAILGUN_HANDID'] = self.uuid
            env['RAILGUN_HWID'] = self.hw.uuid
            # execute the testing module
            return execute(
                'python "%s"' % self.entry_path,
                runconfig.RUNNER_DEFAULT_TIMEOUT,
                cwd=self.tempdir.path,
                env=env,
                close_fds=True
            )
        except ProcessTimeout:
            raise RunnerTimeout()
        except Exception:
            logger.exception(
                'Error when executing handin %(handid)s of homework %(hwid)s.' %
                {'hwid': self.hw.uuid, 'handid': self.uuid}
            )
            raise InternalServerError()
