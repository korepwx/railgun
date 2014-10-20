#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/webconfig.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import os
from config import *

# When DEBUG is set to True, Flask debugging console will be enabled.
DEBUG = False

# MAX_CONTENT_LENGTH controls the maximum request size for flask to handle
# NOTE: we want to display a message instead of HTTP error when the user
#       uploads a large (but not too large) archive file, so we limit
#       flask MAX_CONTENT_LENGTH to 10 * MAX_SUBMISSION_SIZE
MAX_CONTENT_LENGTH = MAX_SUBMISSION_SIZE * 10

# SECRET_KEY is the private key for session encryption.
SECRET_KEY = (
    ReadKeyFile(os.path.join(RAILGUN_ROOT, 'keys/webKey.txt'))
)

# COMM_KEY is the secret key to encrypt /api/handin/update/<uuid>/
# payloads.
COMM_KEY = (
    ReadKeyFile(os.path.join(RAILGUN_ROOT, 'keys/commKey.txt'))
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
    ReadKeyFile(os.path.join(RAILGUN_ROOT, 'keys/sqlKey.txt'))
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

# AUTH_PROVIDERS define all the external authenticate providers this
# website should use
AUTH_PROVIDERS = [
    ('railgun.website.userauth.CsvFileAuthProvider', {
        'name': 'csvfile',
        'path': os.path.join(RAILGUN_ROOT, 'config/users.csv'),
    }),
]

# LOG_FILE defines the main log file for the website
LOG_FILE = os.path.join(RAILGUN_ROOT, 'logs/website.log')

# WEBSITE_LOGGING configures the logging facility of Python for the website.
WEBSITE_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'filename': LOG_FILE,
            'maxBytes': 204800,
            'backupCount': 3,
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'WARNING',
        },
        'railgun.website.context': {
            'handlers': ['default'],
            'level': 'WARNING',
        },
        'sqlalchemy': {
            'handlers': ['default'],
            'level': 'WARNING',
        },
    }
}

# Load un-versioned general config values from config/general.py
LoadConfig(
    sys.modules[__name__],
    os.path.join(RAILGUN_ROOT, 'config/website.py')
)
