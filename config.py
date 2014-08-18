#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: config.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

"""
This file contains common configurations shared by website and runner
Flask and Celery specified configurations can be found in each directory.

Since this file is version controlled by git, modify this file directly for
production environment is not recommended. Modify config/general.py instead.
"""

import os
import re
import sys


# Utility to load config values from external file
def LoadConfig(obj, fpath):
    """Load config values from `fpath` into `obj`."""
    if (os.path.isfile(fpath)):
        values = {}
        execfile(fpath, {}, values)
        p = re.compile('^[A-Z][A-Z_]*$')
        for k, v in values.iteritems():
            if (p.match(k)):
                setattr(obj, k, v)

# RAILGUN_ROOT stores the path of railgun project
RAILGUN_ROOT = os.path.realpath(os.path.dirname(__file__))

# ALLOW_SIGNUP determines whether the railgun website allows new user
# sign up.
ALLOW_SIGNUP = True

# DEFAULT_LOCALE is selected to serve the client when prefered locale
# is not available.
DEFAULT_LOCALE = 'en'

# DEFAULT_TIMEZONE is used to represent the date and times when user
# configuration is not available.
DEFAULT_TIMEZONE = 'UTC'

# DEFAULT_HIDE_RULES hides particular files from all homework packs
DEFAULT_HIDE_RULES = (
    'Thumbs\\.db$',         # windows picture preview database
    '\\.DS_Store$',         # OS X directory meta
    '__MACOSX',             # OS X archive file meta data
    '^\\._.*$|/\\._.*$',    # OS X special backup files
    '\\.directory$',        # dolphin directory meta
    '\\.py[cdo]$',          # hide all python binary files
    '^(py|java)host.*',     # prevent runlib from overwritten
)

# HOMEWORK_DIR stores the definitions of homeworks
HOMEWORK_DIR = os.path.join(RAILGUN_ROOT, 'hw')

# HOMEWORK_PACK_DIR stores the packed archives of all homeworks
HOMEWORK_PACK_DIR = os.path.join(RAILGUN_ROOT, 'hw/.pack')

# HOMEWORK_STATIC_DIR stores the copied description resources of all homeworks
HOMEWORK_STATIC_DIR = os.path.join(RAILGUN_ROOT, 'hw/.static')

# IGNORE_HANDINS_OF_REMOVED_HW determines whether to list submissions for
# deleted homeworks
IGNORE_HANDINS_OF_REMOVED_HW = True

# TEMPORARY_DIR stores the temporary directory for runner
TEMPORARY_DIR = os.path.join(RAILGUN_ROOT, 'tmp')

# RUNLIB_DIR is the root directory of all host libraries
RUNLIB_DIR = os.path.join(RAILGUN_ROOT, 'runlib')

# TRANSLATION_DIR is the root directory of all translation resources
TRANSLATION_DIR = os.path.join(RAILGUN_ROOT, 'railgun/website/translations')

# RUNNER_DEFAULT_TIMEOUT controls the default timeout config for testing
# module to run
RUNNER_DEFAULT_TIMEOUT = 10

# WEBSITE_BASEURL tells runner what is the base url of railgun
WEBSITE_BASEURL = 'http://localhost:5000'

# Load un-versioned general config values from config/general.py
LoadConfig(
    sys.modules[__name__],
    os.path.join(RAILGUN_ROOT, 'config/general.py')
)
