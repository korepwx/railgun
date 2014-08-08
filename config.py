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
this file contains common configurations shared by website and runner
Flask and Celery specified configurations can be found in each directory.
"""

import os

# RAILGUN_ROOT stores the path of railgun project
RAILGUN_ROOT = os.path.realpath(os.path.dirname(__file__))

# DEFAULT_LOCALE is selected to serve the client when prefered locale
# is not available.
DEFAULT_LOCALE = 'en'

# DEFAULT_TIMEZONE is used to represent the date and times when user
# configuration is not available.
DEFAULT_TIMEZONE = 'Asia/Shanghai'

# DEFAULT_HIDE_RULES hides particular files from all homework packs
DEFAULT_HIDE_RULES = (
    'Thumbs\\.db$',         # windows picture preview database
    '\\.DS_Store$',         # OS X directory meta
    '\\.directory$',        # dolphin directory meta
    '\\.py[cdo]$',          # hide all python binary files
    '^(py|java)host.*',     # prevent runlib from overwritten
)

# HOMEWORK_DIR stores the definitions of homeworks
HOMEWORK_DIR = os.path.join(RAILGUN_ROOT, 'hw')

# HOMEWORK_PACK_DIR stores the packed archives of all homeworks
HOMEWORK_PACK_DIR = os.path.join(HOMEWORK_DIR, '.pack')

# TEMPORARY_DIR stores the temporary directory for runner
TEMPORARY_DIR = os.path.join(RAILGUN_ROOT, 'tmp')

# UPLOAD_DIR stores all uploaded handins
UPLOAD_DIR = os.path.join(RAILGUN_ROOT, 'upload')

# RUNLIB_DIR is the root directory of all host libraries
RUNLIB_DIR = os.path.join(RAILGUN_ROOT, 'runlib')

# RUNNER_DEFAULT_TIMEOUT controls the default timeout config for testing
# module to run
RUNNER_DEFAULT_TIMEOUT = 10
