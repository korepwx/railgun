#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/runner/host.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import os
import re
import socket
import urllib

from . import runconfig
from .context import logger
from .errors import RunnerError, InternalServerError, FileDenyError, \
    RunnerTimeout, NetApiAddressRejected
from railgun.common.hw import FileRules
from railgun.common.lazy_i18n import lazy_gettext
from railgun.common.fileutil import dirtree, remove_firstdir
from railgun.common.osutil import ProcessTimeout, execute
from railgun.common.tempdir import TempDir


class HostConfig(object):
    """Configuration values to be passed to host process by environmental
    variables.

    Any non-callable object attribute will be uppercased and put into the
    new envinronment.
    """

    def __init__(self, **kwargs):
        # Read implicit values from kwargs
        for k, v in kwargs.iteritems():
            setattr(self, k, v)
        # Dictionary for explicit values.
        self._values = {}

    def putenv(self, key, value):
        """Put explicit value into config."""
        self._values[key] = value

    def getenv(self, key):
        """Get explicit value from config."""
        return self._values[key]

    def make_environ(self):
        """Make the new environ from current process and config values."""
        ret = os.environ.copy()
        # setup default values
        ret['RAILGUN_API_BASEURL'] = runconfig.WEBSITE_API_BASEURL
        ret['RAILGUN_ROOT'] = runconfig.RAILGUN_ROOT
        # setup implicit values
        for k, v in self.__dict__.iteritems():
            if (v is not None and not k.startswith('_') and not callable(v)):
                ret['RAILGUN_%s' % str(k).upper()] = str(v)
        # setup explicit values
        for k, v in self._values.iteritems():
            ret[k] = v
        return ret


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

        # the host config object
        self.config = HostConfig(handid=uuid, hwid=self.hw.uuid)

    def __enter__(self):
        """Initialize the host directory"""
        self.tempdir.open()
        return self

    def __exit__(self, ignore1, ignore2, ignore3):
        self.tempdir.close()

    def _spawn(self, cmdline, timeout=None):
        """Spawn external process."""

        try:
            # execute the testing module
            return execute(
                cmdline,
                timeout or runconfig.RUNNER_DEFAULT_TIMEOUT,
                cwd=self.tempdir.path,
                env=self.config.make_environ(),
                close_fds=True
            )
        except ProcessTimeout:
            raise RunnerTimeout()
        except Exception:
            logger.exception(
                'Error when executing submission %(handid)s of homework '
                '%(hwid)s.' %
                {'hwid': self.hw.uuid, 'handid': self.uuid}
            )
            raise InternalServerError()

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
                'when executing submission %(handid)s.' %
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
                'when executing submission %(handid)s.' %
                {'hwid': self.hw.uuid, 'handid': self.uuid}
            )
            raise InternalServerError()


class PythonHost(BaseHost):
    """Python handin running host"""

    def __init__(self, uuid, hw, lang="python"):
        super(PythonHost, self).__init__(uuid, hw, lang)

        # Update process running environment
        python_path = os.environ.get('PYTHONPATH', None)
        python_path = [python_path] if python_path else []
        self.config.putenv(
            'PYTHONPATH',
            os.path.pathsep.join([
                runconfig.RAILGUN_ROOT,
                os.path.join(runconfig.RUNLIB_DIR, 'python')
            ] + python_path)
        )

        # get interested parameters of this task
        self.entry = self.runner_params.get('entry')
        self.timeout = int(self.runner_params.get('timeout') or
                           runconfig.RUNNER_DEFAULT_TIMEOUT)
        self.entry_path = os.path.join(self.tempdir.path, self.entry)

    def compile(self):
        pass

    def run(self):
        """Run this Python testing module."""
        return self._spawn('python "%s"' % self.entry_path, self.timeout)


class NetApiHost(PythonHost):
    """NetAPI handin running host"""

    def __init__(self, remote_addr, uuid, hw):
        super(NetApiHost, self).__init__(uuid, hw, 'netapi')
        self.config.remote_addr = remote_addr
        # Rule of url and ip in regex expression
        self.config.urlrule = self.compiler_params.get('url') or None
        self.config.iprule = self.compiler_params.get('ip') or None

    def compile(self):
        """Validate the provided address by urlrule and iprule."""
        if (self.config.urlrule):
            p = re.compile(self.config.urlrule)
            if (not p.match(self.config.remote_addr)):
                raise NetApiAddressRejected(compile_error=lazy_gettext(
                    'Address "%(url)s" does not match pattern "%(rule)s"',
                    url=self.config.remote_addr, rule=self.config.urlrule
                ))
        if (self.config.iprule):
            domain = urllib.splitport(
                urllib.splithost(
                    urllib.splittype(self.config.remote_addr)[1]
                )[0]
            )[0]
            # get ip from domain
            try:
                ipaddr = socket.gethostbyname(domain)
            except Exception:
                logger.exception(
                    'Could not get ip address for domain "%s".' % domain)
                ipaddr = '<invalid>'
            # ip not match, skip
            p = re.compile(self.config.iprule)
            if (not p.match(ipaddr)):
                raise NetApiAddressRejected(compile_error=lazy_gettext(
                    'IP address "%(ip)s" does not match pattern "%(rule)s"',
                    ip=ipaddr, rule=self.config.iprule
                ))


class InputClassHost(PythonHost):
    """NetAPI handin running host"""

    def __init__(self, uuid, hw):
        super(InputClassHost, self).__init__(uuid, hw, 'input')
