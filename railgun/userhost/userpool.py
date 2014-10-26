#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/userhost/userpool.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import time


class UserPool(object):
    """Manages the available account."""

    def __init__(self, users):
        self.users = users
        self._expires = {u: 0 for u in users}

    def current_time(self):
        """Get the current timestamp."""
        return int(time.time())

    def acquire(self, expires=10):
        """Get a free user, which will expire in `expires` seconds.
        Returns the user name if available, None otherwise.
        """
        now_time = self.current_time()
        for u in self.users:
            user_expire = self._expires[u]
            if user_expire < now_time:
                self._expires[u] = now_time + expires
                return u

    def release(self, user):
        """Release the required user immediately."""
        self._expires[user] = 0
