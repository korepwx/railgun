#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/runner/runconfig.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

from config import *

# The base url of API for the runner to interact with
WEBSITE_API_BASEURL = WEBSITE_BASEURL + '/api'

# The user id and group id for submissions on offline run queue
# If group id is not defined, the group id of the user will be selected.
OFFLINE_USER_ID = None
OFFLINE_GROUP_ID = None

# The offline user host, or None if host server is not used.
# OFFLINE_USER_HOST = ('127.0.0.1', 9777)
OFFLINE_USER_HOST = None

# The user id and group id for submissions on online run queue
# If group id is not defined, the group id of the user will be selected.
ONLINE_USER_ID = None
ONLINE_GROUP_ID = None

# The online user host, or None if host server is not used.
# OFFLINE_USER_HOST = ('127.0.0.1', 9778)
ONLINE_USER_HOST = None

# ---- specify the broker of Celery ----
# NOTE: format of Redis server is redis://:password@hostname:port/db_number
BROKER_URL = 'redis://localhost:6379/0'

# ---- celery run queues ----
CELERY_DEFAULT_QUEUE = 'default'
CELERY_CREATE_MISSING_QUEUES = True

CELERY_ROUTES = {
    # 'railgun.runner.tasks.helloWorld': {'queue': 'example'}
}

# ---- List of modules to import when celery starts ----
CELERY_IMPORTS = ()

# ---- Date and time settings ----
CELERY_TIMEZONE = DEFAULT_TIMEZONE
CELERY_ENABLE_UTC = True

# ---- serialization settings ----
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']

# Load un-versioned general config values from config/general.py
LoadConfig(
    sys.modules[__name__],
    os.path.join(RAILGUN_ROOT, 'config/runner.py')
)
