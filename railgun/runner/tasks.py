#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/runner/tasks.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

from . import runconfig
from .apiclient import ApiClient
from .context import app, logger
from .handin import PythonHandin
from .errors import RunnerError, InternalServerError
from railgun.common.hw import HwScore
from railgun.common.lazy_i18n import gettext_lazy


def report_error(handid, err):
    """Report a `RunnerError` to remote api."""

    api = ApiClient(runconfig.WEBSITE_API_BASEURL)
    score = HwScore(False, result=err.message)
    api.report(handid, score)


def report_start(handid):
    """Report a handin is running."""

    api = ApiClient(runconfig.WEBSITE_API_BASEURL)
    api.start(handid)


def run_handin(handler, handid, hwid, filename):
    """Run given handin with `handler`."""
    try:
        report_start(handid)
        exitcode, stdout, stderr = handler.execute()
        # log the handin execution
        if (exitcode != 0):
            logger.warning(
                'Handin[%(handid)s] of hw[%(hwid)s]: Error.\n%(stdout)s\n'
                '%(stderr)s' %
                {'handid': handid, 'hwid': hwid, 'stdout': stdout,
                 'stderr': stderr}
            )
        else:
            logger.info(
                'Handin[%(handid)s] of hw[%(hwid)s]: OK.' %
                {'handid': handid, 'hwid': hwid}
            )
        # Create the api client, we may use it once or twice
        api = ApiClient(runconfig.WEBSITE_API_BASEURL)
        # Report failure if exitcode != 0. In this case the host itself may
        # not have the chance to report handin scores
        if (exitcode != 0):
            score = HwScore(
                False,
                gettext_lazy('Exitcode of your handin is %(exitcode)s != 0.',
                             exitcode=exitcode)
            )
            api.report(handid, score)
        # Update exitcode, stdout and stderr here, which cannot be set in
        # the host itself.
        api.proclog(handid, exitcode, stdout, stderr)

    except RunnerError, ex:
        # RunnerError is logically OK and sent to client only.
        # So we just log the message of this exception, not exception detail.
        logger.warning(
            'Handin[%(handid)s] of hw[%(hwid)s]: %(message)s.' %
            {'handid': handid, 'hwid': hwid, 'message': ex.message}
        )
        report_error(handid, ex)
    except Exception:
        logger.exception(
            'Error executing handin "%(handid)s" for homework "%(hwid)s".' %
            {'handid': handid, 'hwid': hwid}
        )
        report_error(handid, InternalServerError())


@app.task
def run_python(handid, hwid, filename):
    """Run a given handin as Python."""
    return run_handin(
        PythonHandin(handid, hwid, filename), handid, hwid, filename
    )
