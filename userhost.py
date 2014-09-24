#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: userhost.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import sys
from getopt import getopt

from railgun.userhost.userpool import UserPool
from railgun.userhost.server import UserHostServer


def usage():
    """Show usage of this script."""
    print(
        'userhost.py [options] account-file(s) ...\n'
        'Options:\n'
        '\n'
        '  -a address       Address of this server to listen to '
        '[default 127.0.0.1].\n'
        '  -p port          Port of this server to listen to [default 9777].\n'
    )
    sys.exit(0)

interface = '127.0.0.1'
port = 9777
users = []

# parse the arguments
opts, args = getopt(sys.argv[1:], 'a:p:')
for o, v in opts:
    if o == '-a':
        interface = v
    elif o == '-p':
        try:
            port = int(v)
        except Exception:
            usage()
    else:
        usage()

if not args:
    usage()

# Load the accounts from external files
for fname in args:
    users.extend([v.strip() for v in open(fname, 'rb')])
users = [v for v in set(users) if v]

# run the server
userpool = UserPool(users=users)
server = UserHostServer(userpool=userpool)
server.run(interface=interface, port=port)
