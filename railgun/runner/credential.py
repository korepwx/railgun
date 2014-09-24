#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/runner/credential.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

"""
This module provides to utility to acquire and release system account for
the runner.
"""

from railgun.userhost.client import UserHostClient
from . import runconfig


def _acquire(userhost, expires):
    """Acquire a free account from user credential host.

    Args:
        userhost: (server, port) of the user credential host.
        expires: seconds for this user to expire.

    Returns:
        The user account name.

    Raises:
        Exception: if user cannot be acquired.
    """
    client = UserHostClient(userhost[0], userhost[1])
    ret = client.acquire(expires)
    if ret is None:
        raise RuntimeError('System account exhausted.')
    return ret


def _put(userhost, user):
    """Release a system account on user credential host.

    Args:
        userhost: (server, port) of the user credential host.
        user: name of this user.

    Raises:
        Exception: if user cannot be acquired.
    """
    client = UserHostClient(userhost[0], userhost[1])
    if not client.release(user):
        raise RuntimeError('Could not release system account.')


def acquire_offline_user(expires=10):
    """Get a free account for the offline runner."""
    if runconfig.OFFLINE_USER_HOST:
        return _acquire(runconfig.OFFLINE_USER_HOST, expires)
    return runconfig.OFFLINE_USER_ID


def release_offline_user(user):
    """Release the system account for offline runner."""
    if runconfig.OFFLINE_USER_HOST:
        _put(runconfig.OFFLINE_USER_HOST, user)


def acquire_online_user(expires=10):
    """Get a free account for the online runner."""
    if runconfig.ONLINE_USER_HOST:
        return _acquire(runconfig.ONLINE_USER_HOST, expires)
    return runconfig.ONLINE_USER_ID


def release_online_user(user):
    """Release the system account for online runner."""
    if runconfig.ONLINE_USER_HOST:
        _put(runconfig.ONLINE_USER_HOST, user)
