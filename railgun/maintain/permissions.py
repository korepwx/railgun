#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/maintain/permissions.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import os
import pwd

import config
from .base import Task, tasks


class RunnerPermissionCheckTask(Task):
    """Task to check permissions of the runner host."""

    def __init__(self, logstream=None):
        super(RunnerPermissionCheckTask, self).__init__(logstream)
        self.errcount = 0

    def _get_uid(self, user):
        """Get the system user id of given `user`."""
        if not isinstance(user, int):
            user = pwd.getpwnam(user).pw_uid
        return user

    def _get_uname(self, uid):
        """Get the system user name of given `uid`."""
        try:
            return pwd.getpwuid(uid).pw_name
        except KeyError:
            return uid

    def _require_owner_mod(self, path, owner, mode, must_exist=False):
        """Check whether `path` is owned by `owner`, and it has the `mode`.

        Args:
            path (str): the file entity to check.
            owner (int or str): the required owner.
            mode (int): the required mode.
            must_exist (bool): whether the entity must exist? default False.
        """
        if not os.path.exists(path):
            if must_exist:
                self.logger.warning('"%(path)s" is required but not exist.' %
                                    {'path': path})
            return

        # get uid and file mode
        st = os.stat(path)
        uid = st.st_uid
        md = st.st_mode & 0777

        # log generator
        def make_log(rtype, require, current):
            self.logger.warning(
                '%(rtype)s of "%(path)s" is required to be %(require)s, '
                'not %(current)s.' % {
                    'path': path,
                    'require': require,
                    'current': current,
                    'rtype': rtype
                })
            self.errcount += 1

        if uid != self._get_uid(owner):
            make_log('owner', owner, self._get_uname(uid))
        if md != mode:
            make_log('mode', oct(mode), oct(md))

    def check_perm(self):
        # check configuration files
        for fname in ('runner.py', 'website.py', 'users.csv'):
            fpath = os.path.join(config.RAILGUN_ROOT, fname)
            self._require_owner_mod(fpath, 'root', 0600)

        # check critical directories
        for dname in ('logs', 'keys'):
            dpath = os.path.join(config.RAILGUN_ROOT, dname)
            self._require_owner_mod(dpath, 'root', 0700)

        # the temporary directory as submission working directory
        self._require_owner_mod(config.TEMPORARY_DIR, 'root', 0700)

        # if homework is not public repository, it should be 0700
        public_hw = os.path.join(config.RAILGUN_ROOT, 'hw')
        if public_hw != config.HOMEWORK_DIR:
            self._require_owner_mod(config.HOMEWORK_DIR, 'root', 0700)

    def execute(self):
        try:
            self.check_perm()
        except Exception:
            self.errcount += 1
            self.logger.exception('Could not check permissions of runner.')


tasks.add('runner-perm-check', RunnerPermissionCheckTask)
