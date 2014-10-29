#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/runner/context.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

from celery import Celery
from celery.utils.log import get_task_logger

from . import runconfig, permcheck


#: The :class:`celery.Celery` context object.
#:
#: Celery is a robust and scalable job queue.  You may shift a running
#: instance from one machine to paralleled computing platform simply by
#: changing the backend of Celery.
#: To learn more about this framework, you may refer to
#: `Celery Project <http://www.celeryproject.org>`_.
app = Celery('railgun.runner')
app.config_from_object(runconfig)

#: The default logger for this Celery application.  It is used everywhere
#: in this package.  The interface is the same as :class:`logging.Logger`,
#: so you may refer to :mod:`logging` for more details.
logger = get_task_logger(__name__)

# If runconfig.RUNNER_CHECK_PERM is :data:`True`, we will perform the file
# system permissions here.
#
# As is mentioned in :ref:`away_from_exploit`, Railgun relies heavily on
# the system account and file system permissions to protect itself from
# exploits.
#
# The following code will check the permissions as if it is running in a
# installation pattern of two hosts (website and the runner),
# and will reject all the submissions if the permissions are not configured
# as expectation.
if runconfig.RUNNER_CHECK_PERM:
    permcheck.checker.execute(logger)
