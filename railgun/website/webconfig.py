#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/webconfig.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import os
from config import *

# When DEBUG is set to True, Flask debugging console will be enabled.
DEBUG = False

# SECRET_KEY is the private key for session encryption.
SECRET_KEY = (
    open(os.path.join(RAILGUN_ROOT, 'keys/webKey.txt'), 'rb').read().strip()
)

# COMM_KEY is the secret key to encrypt /api/handin/update/<uuid>/
# payloads.
COMM_KEY = (
    open(os.path.join(RAILGUN_ROOT, 'keys/commKey.txt'), 'rb').read().strip()
)

# SQLDB_KEY is the secret key to interact with external database server.
# Maybe it can used by config/website.py, so load it here.
#
# You may add following config into config/website.py to use MYSQL server
# SQLALCHEMY_DATABASE_URI = (
#     'mysql+mysqldb://railgun:%s@localhost/railgun??charset=utf8&use_unicode=0'
#     % SQLDB_KEY
# )
SQLDB_KEY = (
    open(os.path.join(RAILGUN_ROOT, 'keys/sqlKey.txt'), 'rb').read().strip()
)

# BABEL_DEFAULT_LOCALE language is provided to the client when prefered
# locale is not available.
BABEL_DEFAULT_LOCALE = DEFAULT_LOCALE

# BABEL_DEFAULT_TIMEZONE is used to represent the date and times when
# user configuration is not available.
BABEL_DEFAULT_TIMEZONE = DEFAULT_TIMEZONE

# SQLALCHEMY_DATABASE_URI configures the database of Railgun system
SQLALCHEMY_DATABASE_URI = (
    'sqlite:///%s' % os.path.join(RAILGUN_ROOT, 'db/main.db')
)

# LDAP Authentication related
LDAP_AUTH_ENABLED = True
LDAP_ADMIN_KEY = (
    open(os.path.join(RAILGUN_ROOT, 'keys/ldapKey.txt'), 'rb').read().strip()
)

LDAP_BASE_DN = 'ou=People,dc=secoder,dc=net'
LDAP_ADMIN_DN = 'cn=admin,dc=secoder,dc=net'
LDAP_RAILGUN_ADMIN_GROUP_DN = 'cn=railgun_admin,ou=group,dc=secoder,dc=net'
LDAP_URL = 'ldap://localhost'

# Load un-versioned general config values from config/general.py
LoadConfig(
    sys.modules[__name__],
    os.path.join(RAILGUN_ROOT, 'config/website.py')
)
