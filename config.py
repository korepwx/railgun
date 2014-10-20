#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: config.py
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
    # The regex to match a config value
    config_value_pattern = re.compile('^[A-Z][A-Z0-9_]*$')

    # extract config values from an object or a dictionary into an object
    # or a dictionary
    def extract_configs(obj, target):
        kv_iter = (obj.iteritems() if isinstance(obj, dict)
                   else obj.__dict__.iteritems())
        if (isinstance(target, dict)):
            setvalue = lambda k, v: target.update({k: v})
        else:
            setvalue = lambda k, v: setattr(target, k, v)
        # enumerate all available values
        for k, v in kv_iter:
            if (config_value_pattern.match(k)):
                setvalue(k, v)
        return target

    if (os.path.isfile(fpath)):
        values = {}
        the_globals = extract_configs(obj, {})
        execfile(fpath, the_globals, values)
        extract_configs(values, obj)


def ReadKeyFile(fpath, keysize=32):
    """Read key from `fpath`, or generate a new key if path not found."""
    if not os.path.exists(fpath):
        import string
        import random

        # generate the new key
        alphabet = string.letters + string.digits
        theKey = ''.join([
            random.choice(alphabet)
            for i in xrange(keysize)
        ])

        # create necessary directories
        dpath = os.path.split(fpath)[0]
        if not os.path.isdir(dpath):
            os.makedirs(dpath, 0700)

        # save the file
        with open(fpath, 'wb') as f:
            f.write('%s\n' % theKey)
        os.chmod(fpath, 0700)
    else:
        theKey = open(fpath, 'rb').read().strip()

    return theKey


# RAILGUN_ROOT stores the path of railgun project
RAILGUN_ROOT = os.path.realpath(os.path.dirname(__file__))

# LOG_ROOT stores the log directory of railgun project
LOG_ROOT = os.path.join(RAILGUN_ROOT, 'logs')

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
    # prevent system libraries from overwritten
    '^(railgun|pyhost|javahost|unittest|coverage|pep8|traceback|SafeRunner)'
    '(\.py$|/.*)',
)

# HOMEWORK_DIR stores the definitions of homeworks
HOMEWORK_DIR = os.path.join(RAILGUN_ROOT, 'hw')

# HOMEWORK_PACK_DIR stores the packed archives of all homeworks
HOMEWORK_PACK_DIR = os.path.join(RAILGUN_ROOT, 'hw/.pack')

# HOMEWORK_STATIC_DIR stores the copied description resources of all homeworks
HOMEWORK_STATIC_DIR = os.path.join(RAILGUN_ROOT, 'hw/.static')

# STORE_UPLOAD controls whether or not to store the student uploaded
# homework content
STORE_UPLOAD = True

# If STORE_HOMEWORK is True, then UPLOAD_STORE_DIR determines the directory
# to store student uploaded files
UPLOAD_STORE_DIR = os.path.join(RAILGUN_ROOT, 'upload')

# LOCKED_HOMEWORKS define the list of homeworks that cannot be submitted
# NOTE: if '*' is in LOCKED_HOMEWORKDS, then all the homeworks will be locked
LOCKED_HOMEWORKS = ()

# HIDDEN_HOMEWORKS define the list of homeworks that cannot be view.
HIDDEN_HOMEWORKS = ()

# IGNORE_HANDINS_OF_REMOVED_HW determines whether to list submissions for
# deleted homeworks
IGNORE_HANDINS_OF_REMOVED_HW = True

# ADMIN_SCORE_IN_REPORT controls whether the scores of admins should appear
# in the score sheet.
ADMIN_SCORE_IN_REPORT = False

# TEMPORARY_DIR stores the temporary directory for runner
TEMPORARY_DIR = os.path.join(RAILGUN_ROOT, 'tmp')

# RUNLIB_DIR is the root directory of all host libraries
RUNLIB_DIR = os.path.join(RAILGUN_ROOT, 'runlib')

# TRANSLATION_DIR is the root directory of all translation resources
TRANSLATION_DIR = os.path.join(RAILGUN_ROOT, 'railgun/website/translations')

# RUNNER_CHECK_PERM determines whether the system will check the file
# permissions of runner host, and show warnings if the permissions not
# match requirements
RUNNER_CHECK_PERM = False

# RUNNER_DEFAULT_TIMEOUT controls the default timeout config for testing
# module to run
RUNNER_DEFAULT_TIMEOUT = 3

# RUNNER_CONCURRENTY controls how many runners will be executed at the
# same time
RUNNER_CONCURRENTY = 1

# MAX_SUBMISSION_SIZE controls the maximum data size allowed for a student
# to submit (in bytes)
MAX_SUBMISSION_SIZE = 256 * 1024

# MAX_SUBMISSION_FILE_COUNT controls the maximum file count allowed for
# a student to submit
MAX_SUBMISSION_FILE_COUNT = 100

# MAX_USER_PENDING controls the maximum submissions of a single user that
# is running or pending for a single homework.
MAX_USER_PENDING_PER_HW = 1

# EXAMPLE_USER_EMAIL_SUFFIX is the email suffix for users came from the
# auth providers which does not provide emails.
EXAMPLE_USER_EMAIL_SUFFIX = '@not-a-email.secoder.net'

# WEBSITE_BASEURL tells runner what is the base url of railgun
WEBSITE_BASEURL = 'http://localhost:5000'

# Load un-versioned general config values from config/general.py
LoadConfig(
    sys.modules[__name__],
    os.path.join(RAILGUN_ROOT, 'config/general.py')
)
