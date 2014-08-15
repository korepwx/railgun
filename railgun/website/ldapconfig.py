#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: entry/website/webconfig.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   Dawei Yang           <davy.pristina@gmail.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import os
import ldap
from config import *

LDAP_ADMIN_KEY = (
    open(os.path.join(ENTRY_ROOT, 'keys/ldapKey.txt'), 'rb').read().strip()
)

BASE_DN = 'ou=People,dc=secoder,dc=net'
ADMIN_DN = 'cn=admin,dc=secoder,dc=net'

CONN = ldap.initialize('ldap://ldap.secoder.net')
CONN.simple_bind_s(ADMIN_DN, LDAP_ADMIN_KEY)
