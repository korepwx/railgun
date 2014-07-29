#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: config.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

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
