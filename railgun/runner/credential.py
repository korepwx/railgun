#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/runner/credential.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

"""Railgun can be configured to run multiple submission simultaneously
with different system accounts.

This module acquires the accounts from a credential server (if provided),
or just uses the ``config.OFFLINE_USER_ID`` and ``config.ONLINE_USER_ID``.

.. note::

    Offline users will not be able to access the internet.  You must
    use the correct type of users for different submission types.
"""

from railgun.userhost.client import UserHostClient
from . import runconfig


def _acquire(userhost, expires):
    """Acquire a free account from user credential server.

    :param userhost: (`server`, `port`) of the user credential server.
    :type userhost: :class:`tuple`
    :param expires: Seconds for this user to expire.
    :type expires: :class:`int`

    :return: The acquired user account name.
    :raises: Various :class:`Exception` if the user cannot be acquired.
    """
    client = UserHostClient(userhost[0], userhost[1])
    ret = client.acquire(expires)
    if ret is None:
        raise RuntimeError('System account exhausted.')
    return ret


def _put(userhost, user):
    """Release a system account to user credential server.

    :param userhost: (`server`, `port`) of the user credential server.
    :type userhost: :class:`tuple`
    :param user: The name of acquired user.
    :type user: :class:`str`

    :raises: Various :class:`Exception` if the user cannot be released.
    """
    client = UserHostClient(userhost[0], userhost[1])
    if not client.release(user):
        raise RuntimeError('Could not release system account.')


def acquire_offline_user(expires=10):
    """Get a free offline system account.

    :param expires: Seconds for this user to expire.
    :type expires: :class:`int`
    :return: The acquired user account name.
    :raises: Various :class:`Exception` if the user cannot be acquired.
    """
    if runconfig.OFFLINE_USER_HOST:
        return _acquire(runconfig.OFFLINE_USER_HOST, expires)
    return runconfig.OFFLINE_USER_ID


def release_offline_user(user):
    """Release an offline system account.
    Will do nothing if on credential server is configured.

    :param user: The name of acquired user.
    :type user: :class:`str`
    :raises: Various :class:`Exception` if the user cannot be released.
    """
    if runconfig.OFFLINE_USER_HOST:
        _put(runconfig.OFFLINE_USER_HOST, user)


def acquire_online_user(expires=10):
    """Get a free online system account.

    :param expires: Seconds for this user to expire.
    :type expires: :class:`int`
    :return: The acquired user account name.
    :raises: Various :class:`Exception` if the user cannot be acquired."""
    if runconfig.ONLINE_USER_HOST:
        return _acquire(runconfig.ONLINE_USER_HOST, expires)
    return runconfig.ONLINE_USER_ID


def release_online_user(user):
    """Release an online system account.
    Will do nothing if on credential server is configured.

    :param user: The name of acquired user.
    :type user: :class:`str`
    :raises: Various :class:`Exception` if the user cannot be released.
    """
    if runconfig.ONLINE_USER_HOST:
        _put(runconfig.ONLINE_USER_HOST, user)
