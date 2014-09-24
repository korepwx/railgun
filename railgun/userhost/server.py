#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/userhost/server.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import socket


class UserHostServer(object):
    """User credential server that assigns system accounts for each runner
    task.  This server runs single threaded, and will not block if all users
    are assigned.
    """

    def __init__(self, userpool):
        self.pool = userpool

    def _serve_request(self, conn):
        """Serve a incoming request."""
        f = conn.makefile('rw')
        act, arg = tuple(v for v in f.readline().strip().split(' ') if v)
        if act == 'get':
            user = self.pool.acquire(int(arg))
            if user:
                print('get %s -> okay %s' % (arg, user))
                f.write('okay %s\n' % user)
            else:
                print('get %s -> fail' % arg)
                f.write('error\n')
        elif act == 'put':
            print('put %s -> okay' % arg)
            self.pool.release(arg)
            f.write('okay\n')
        else:
            print('unknown: %s' % act)
            f.write('unknown action\n')
        f.flush()

    def run(self, port, interface='', backlog=100):
        """Run the user credential server.

        Args:
            port: the port of user credential server.
            interface: the interface of server to bind to. [default '']
            backlog: tcp backlog size [default 100]
        """
        sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sck.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sck.bind((interface, port))
        sck.listen(backlog)
        while True:
            conn, addr = sck.accept()
            conn.settimeout(10)
            try:
                self._serve_request(conn)
            except Exception:
                pass
            conn.close()
        sck.close()
