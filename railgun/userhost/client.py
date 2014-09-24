#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/userhost/client.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import socket


class UserHostClient(object):
    """Client to communicate with user host server."""

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def _communicate(self, payload):
        sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sck.settimeout(10)
        sck.connect((self.host, self.port))
        f = sck.makefile('rw')
        f.write('%s\n' % payload)
        f.flush()
        ret = f.readline().strip()
        sck.close()
        return ret

    def acquire(self, expires=10):
        """Get a free user, which will expire in `expires` seconds.
        Returns the user name if available, None otherwise.
        """
        ret = self._communicate('get %d' % expires).split(' ')
        if ret[0] == 'okay':
            return ret[1]

    def release(self, user):
        """Release the required user immediately.
        Returns True if success, False otherwise.
        """
        ret = self._communicate('put %s' % user)
        return ret == 'okay'
