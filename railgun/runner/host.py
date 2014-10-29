#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/runner/host.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

"""This module provides :class:`BaseHost` as the basic interface of
a submission handler, as well as derived classes targeted to different
programming languages.

Submissions may be various in programming languages, while different
languages may have different context to run.  So a runner host prepares
the environment, compiles and launches the submission according to its
programming language.
"""

import os
import re
import pwd
import grp
import socket
import urllib

from railgun.common.hw import FileRules
from railgun.common.lazy_i18n import lazy_gettext
from railgun.common.fileutil import dirtree, remove_firstdir
from railgun.common.osutil import ProcessTimeout, execute
from railgun.common.tempdir import TempDir
from . import runconfig
from .context import logger
from .credential import (acquire_offline_user, release_offline_user,
                         acquire_online_user, release_online_user)
from .errors import (RunnerError, FileDenyError, RunnerTimeout,
                     NetApiAddressRejected, ExtractFileFailure,
                     RuntimeFileCopyFailure, SpawnProcessFailure,
                     ArchiveContainTooManyFileError)


class HostConfig(dict):
    """Config values passed to hosts by environmental variables."""

    UPPER_KEY_RE = re.compile(r'^[A-Z][A-Z0-9_]*$')

    def make_environ(self):
        """Prepare the environmental variables for the host process.

        Values of :data:`None` will be ignored, and other values will be
        converted into string type before being added to environ dictionary.

        All the keys matching ``[A-Z][A-Z0-9_]*`` will be used directly in the
        new environ dictionary.
        All the keys in other formats will be translated into uppercase,
        and a prefix of "RAILGUN_" will be add to the key.

        For example::

            >>> config = HostConfig(user_id=1, group_id=2, ignored=None,
                                    PYTHONPATH='/usr/local/lib/python2.7')
            >>> config.make_environ()
            {'RAILGUN_USER_ID': '1', 'RAILGUN_GROUP_ID': '2',
             'PYTHONPATH': '/usr/local/lib/python2.7'}

        :return: The environmental variable dictionary.
        :rtype: :class:`dict`
        """
        ret = os.environ.copy()
        # setup default values
        ret['RAILGUN_API_BASEURL'] = runconfig.WEBSITE_API_BASEURL
        ret['RAILGUN_ROOT'] = runconfig.RAILGUN_ROOT
        # setup explicit values
        for k, v in self.iteritems():
            if v is not None:
                k = str(k)
                if HostConfig.UPPER_KEY_RE.match(k):
                    ret[k] = str(v)
                else:
                    ret['RAILGUN_%s' % k.upper()] = str(v)
        return ret


class BaseHost(object):
    """The base interface for a runner host.

    A runner host will hold a working directory under ``config.TEMPORARY_DIR``,
    whose name is ``uuid``.  This directory will be automatically removed
    if :class:`BaseHost` is managed by ``with`` statement, for example::

        with BaseHost(uuid, hw, 'python') as host:
            pass

    :param uuid: The uuid of the submission.
    :type uuid: :class:`str`
    :param hw: The corresponding homework object.
    :type hw: :class:`~railgun.common.hw.Homework`
    :param lang: The programming language of this host.
    :type lang: :class:`str`
    """

    def __init__(self, uuid, hw, lang):
        #: A :class:`~railgun.common.tempdir.TempDir`, whose directory name
        #: is `uuid`.
        self.tempdir = TempDir(uuid)

        #: The uuid of the submission.
        self.uuid = uuid

        #: The :class:`~railgun.common.hw.Homework`.
        self.hw = hw

        #: The :class:`~railgun.common.hw.HwCode` of corresponding language.
        self.hwcode = hw.get_code(lang)

        #: The xml node of compiler parameters.
        #: You may refer to :attr:`HwCode.compiler_params` for more details.
        self.compiler_params = self.hwcode.compiler_params

        #: The xml node of runner parameters.
        #: You may refer to :attr:`HwCode.runner_params` for more details.
        self.runner_params = self.hwcode.runner_params

        #: The :class:`HostConfig` for the process.
        self.config = HostConfig(handid=uuid, hwid=self.hw.uuid)

        #: The acquired system account (name or uid).
        #:
        #: Railgun can be configured to run multiple submissions in
        #: different system accounts simultaneously.  This attribute
        #: stores the acquired system account, so that we can release
        #: it later.
        #:
        #: If you intend to get the `uid` and `gid` of this user,
        #: access ``config['user_id']`` and ``config['group_id']``
        #: instead.
        self.runner_user = None

    def __enter__(self):
        #: We create the directory with mode 0777, while the owner is the owner
        #: of runner queue process.
        #: The permissions and the owner will be set to `config['user_id']`
        #: until :meth:`spawn`.
        self.tempdir.open(mode=0777)
        return self

    def __exit__(self, ignore1, ignore2, ignore3):
        #: The temporary directory will be removed here.
        self.tempdir.close()

    def spawn(self, cmdline, timeout=None):
        """Spawn an external process to execute the given commands.

        If the owner user of current process (runner queue) is `root`,
        and ``config['user_id']`` != 0, the owner of :attr:`tempdir`
        will be changed to that user, and the file system mode will
        be changed to 0700.

        :param cmdline: The command line to be executed.
        :type cmdline: :class:`str`
        :param timeout: Wait for `timeout` seconds before we kill the
            external process and claim a rejected submission.

            If this argument is not given, ``config.RUNNER_DEFAULT_TIMEOUT``
            will be chosen as the timeout limit.
        :type timeout: :class:`float`
        """

        try:
            # Before spawn the process, we've already known the process
            # user.  And we'll try to chown & chmod if our runner queue
            # runs at root privilege (otherwise we cannot change the
            # owner user).
            if os.getuid() == 0:
                # If config['user_id'] is 0, runner_user must be None,
                # where we shouldn't go any more.
                if self.config['user_id'] != 0:
                    self.tempdir.chown(
                        self.config['user_id'],
                        self.config['group_id'],
                        True
                    )
                    self.tempdir.chmod(0700, True)
            # Now we can execute the host process safely!
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
            raise SpawnProcessFailure()

    def set_user(self, uid, gid=None):
        """Set the user and the group in host config.

        The `uid` will be stored in ``config['user_id']`` while the `gid`
        will be stored in ``config['group_id']``.  However, if `uid` is
        given :data:`None`, all the defence based on user privileges will
        not take place.

        :param uid: The uid or name of system account.
        :type uid: :class:`int` or :class:`str`
        :param gid: The gid or group name in the system.
            If set to :data:`None`, the group of given user will be
            selected.
        :type gid: :class:`int` or :class:`str`

        :raises: :class:`KeyError` if `uid` or `gid` is a :class:`str`,
            but does not exist in the system database.
        """

        # If uid is None, set config['user_id'] and config['group_id'] to 0
        if not uid:
            self.config['user_id'] = 0
            self.config['group_id'] = 0
            return

        # Store user name for later release
        self.runner_user = uid

        # NOTE: pwd.getpwnam and grp.getgrname does throw KeyError
        #       if given name not exist.
        if not isinstance(uid, int):
            uid = pwd.getpwnam(uid).pw_uid
        if gid is None:
            gid = pwd.getpwuid(uid).pw_gid
        elif not isinstance(gid, int):
            gid = grp.getgrnam(gid).gr_gid

        self.config['user_id'] = uid
        self.config['group_id'] = gid

    def compile(self):
        """Call to compile the submission.  Some programming language may
        skip this process.
        """
        pass

    def run(self):
        """Run this submission.  All derived classes must implement this.

        :return: A :class:`tuple` of (exitcode, stdout, stderr).
        """
        raise NotImplementedError()

    def prepare_hwcode(self):
        """Prepare the runner context by copying files from `hw/code` into
        :attr:`tempdir`.  This method should be called before
        :meth:`extract_handin`.
        """
        try:
            self.tempdir.copyfiles(
                self.hwcode.path,
                dirtree(self.hwcode.path),
                mode=0777
            )
        except Exception:
            logger.exception(
                'Cannot copy code files into tempdir for homework %(hwid)s '
                'when executing submission %(handid)s.' %
                {'hwid': self.hw.uuid, 'handid': self.uuid}
            )
            raise RuntimeFileCopyFailure()

    def extract_handin(self, archive):
        """Extract the given archive file into :attr:`tempdir`.

        The :class:`~railgun.common.hw.FileRules` defined in :attr:`hw` and
        :attr:`hwcode` will be validated on each file, so this method is
        safe.

        :param archive: An extractor of the submission archive file.
        :type archive: :class:`~railgun.common.fileutil.Extractor`
        """

        try:
            # We limit the count of files in an archive file, since too many
            # files may slow down the runner queue.
            maxCount = runconfig.MAX_SUBMISSION_FILE_COUNT
            if archive.countfiles(maxCount) > maxCount:
                raise ArchiveContainTooManyFileError()

            # If the archive file contains only one top-level directory,
            # it is likely that all the code files are placed under it.
            #
            # So we remove the top-level directory and extract the files
            # in it directly to :attr:`tempdir`.
            onedir = archive.onedir()
            canonical_path = remove_firstdir if onedir else (lambda s: s)

            # Use the :class:`FileRules` to filter out unwanted files.
            def should_skip(path):
                path = canonical_path(path)
                # First, check the rules in HwCode
                action = self.hwcode.file_rules.get_action(
                    path, default_action=-1
                )
                if action == FileRules.DENY:
                    raise FileDenyError(path)
                if action == FileRules.ACCEPT:
                    return False
                if action != -1:
                    # action is not None, and action != ACCEPT, this means
                    # that rules in `hwcode` rejects this file.
                    return True
                # Next, check the rules in Homework
                action = self.hw.file_rules.get_action(
                    path, default_action=FileRules.LOCK
                )
                if action == FileRules.DENY:
                    raise FileDenyError(path)
                return (action != FileRules.ACCEPT)

            # Call utility to do the extraction.  Initial file mode is 0777,
            # and we'll correct this problem in :meth:`spawn`
            self.tempdir.extract(archive, should_skip, mode=0777)
        except RunnerError:
            raise
        except Exception:
            logger.exception(
                'Cannot extract archive into tempdir for homework %(hwid)s '
                'when executing submission %(handid)s.' %
                {'hwid': self.hw.uuid, 'handid': self.uuid}
            )
            raise ExtractFileFailure()


class PythonHost(BaseHost):
    """The Python runner host, derived from :class:`BaseHost`.

    This class is special, in that it does not only acts as a derived
    class to serve Python submission, but also acts as a base class for
    all Python based hosts.

    For example, the :class:`InputClassHost`, taking a Python script
    to evaluate the submitted csv data, is merely the same as a
    :class:`PythonHost`.  So it just inherits this class to implement
    the common functions.

    :param uuid: The uuid of this submission.
    :type uuid: :class:`str`
    :param hw: The corresponding homework.
    :type hw: :class:`~railgun.common.hw.Homework`
    :param lang: The programming language of this host.  Can be set
        by derived classes.
    :type lang: :class:`str`
    :param offline: Whether this host uses offline system accounts?
        Offline system accounts will not be able to access the internet.
    :type offline: :class:`bool`
    """

    def __init__(self, uuid, hw, lang="python", offline=True):
        super(PythonHost, self).__init__(uuid, hw, lang)

        #: Store the path of Python safe runner (``RAILGUN_ROOT/SafeRunner``).
        self.safe_runner = os.path.join(
            runconfig.RAILGUN_ROOT,
            'SafeRunner'
        )

        # Add additional Python library search path.
        python_path = os.environ.get('PYTHONPATH', None)
        python_path = [python_path] if python_path else []
        self.config['PYTHONPATH'] = os.path.pathsep.join(
            [runconfig.RAILGUN_ROOT,
             os.path.join(runconfig.RUNLIB_DIR, 'python')] +
            python_path
        )

        #: Whether this host uses offline system accounts?
        self.offline = offline

        #: The main Python script file (from :attr:`BaseHost.runner_params`).
        self.entry = self.runner_params.get('entry')

        #: The timeout limit of this submission
        #: (from :attr:`BaseHost.runner_params`).
        self.timeout = int(self.runner_params.get('timeout') or
                           runconfig.RUNNER_DEFAULT_TIMEOUT)

        #: The parent directory of :attr:`entry` file.
        self.entry_path = os.path.join(self.tempdir.path, self.entry)

    def run(self):
        """Run this Python submission."""
        try:
            # Get a free system account.
            #
            # Note that we'll keep the process running for at most `timeout`
            # seconds (with a 1~2 second error), so we hold the system
            # account for at most such a long time.
            expires = self.timeout + 2
            if self.offline:
                user_login = acquire_offline_user(expires)
            else:
                user_login = acquire_online_user(expires)
            self.set_user(user_login)

            return self.spawn(
                '"%s" "%s"' % (self.safe_runner, self.entry_path),
                self.timeout
            )
        finally:
            # Whether succeeded or not, we must release the system account.
            if self.runner_user:
                if self.offline:
                    release_offline_user(self.runner_user)
                else:
                    release_online_user(self.runner_user)


class NetApiHost(PythonHost):
    """The NetAPI runner host, derived from :class:`PythonHost`.

    :param remote_addr: The user submitted url address.
    :type remote_addr: :class:`str`
    :param uuid: The uuid of this submission.
    :type uuid: :class:`str`
    :param hw: The corresponding homework.
    :type hw: :class:`~railgun.common.hw.Homework`
    """

    def __init__(self, remote_addr, uuid, hw):
        super(NetApiHost, self).__init__(uuid, hw, 'netapi', offline=False)
        self.config['remote_addr'] = remote_addr
        # Rule of url and ip in regex expression
        self.config['urlrule'] = self.compiler_params.get('url') or None
        self.config['iprule'] = self.compiler_params.get('ip') or None

    def compile(self):
        """Validate the user submitted url address at compile stage.

        The url address will be tested with the configured regex patterns
        loaded from :attr:`BaseHost.compiler_params`.
        Refer to :ref:`hwnetapi` for more details about the rules.
        """
        if self.config['urlrule']:
            p = re.compile(self.config['urlrule'])
            if not p.match(self.config['remote_addr']):
                raise NetApiAddressRejected(compile_error=lazy_gettext(
                    'Address "%(url)s" does not match pattern "%(rule)s"',
                    url=self.config['remote_addr'], rule=self.config['urlrule']
                ))
        if self.config['iprule']:
            domain = urllib.splitport(
                urllib.splithost(
                    urllib.splittype(self.config['remote_addr'])[1]
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
            p = re.compile(self.config['iprule'])
            if not p.match(ipaddr):
                raise NetApiAddressRejected(compile_error=lazy_gettext(
                    'IP address "%(ip)s" does not match pattern "%(rule)s"',
                    ip=ipaddr, rule=self.config['iprule']
                ))


class InputClassHost(PythonHost):
    """The CSV data runner host, derived from :class:`PythonHost`.

    :param uuid: The uuid of this submission.
    :type uuid: :class:`str`
    :param hw: The corresponding homework.
    :type hw: :class:`~railgun.common.hw.Homework`
    """

    def __init__(self, uuid, hw):
        super(InputClassHost, self).__init__(uuid, hw, 'input')
