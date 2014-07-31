#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: config.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import os

# When DEBUG is set to True, Flask debugging console will be enabled.
DEBUG = True

# SECRET_KEY is the private key for session encryption.
SECRET_KEY = 'This is not the final secret key'

# BABEL_DEFAULT_LOCALE language is provided to the client when prefered
# locale is not available.
BABEL_DEFAULT_LOCALE = 'en'

# BABEL_DEFAULT_TIMEZONE is used to represent the date and times when
# user configuration is not available.
BABEL_DEFAULT_TIMEZONE = 'Asia/Shanghai'

# SQLALCHEMY_DATABASE_URI configures the database of Railgun system
SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/railgun.db'

# RAILGUN_ROOT stores the path of railgun project
RAILGUN_ROOT = os.path.realpath(os.path.dirname(__file__))

# HOMEWORK_DIR stores the definitions of homeworks
HOMEWORK_DIR = os.path.join(RAILGUN_ROOT, 'hw')

# TEMPORARY_DIR stores the temporary directory for all system components
TEMPORARY_DIR = os.path.join(HOMEWORK_DIR, 'tmp')
