#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/runner/tasks.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

from celery.utils.log import get_task_logger

from .context import app
from .handin import PythonHandin
from .errors import RunnerError


logger = get_task_logger(__name__)


@app.task
def run_python(handid, hwid, filename):
    """Run a given handin as Python."""
    try:
        handin = PythonHandin(handid, hwid, filename)
        handin.execute()
        logger.info(
            'Executed handin "%(handid)s" for homework "%(hwid)s".' %
            {'handid': handid, 'hwid': hwid}
        )
    except RunnerError:
        logger.exception(
            'Error executing handin "%(handid)s" for homework "%(hwid)s".' %
            {'handid': handid, 'hwid': hwid}
        )
