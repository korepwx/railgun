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
from .handin import PythonHandin, NetApiHandin
from .errors import RunnerError, InternalServerError, NonUTF8OutputError
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


def run_handin(handler, handid, hwid):
    """Run given handin with `handler_class`."""
    # Create the api client, we may use it once or twice
    api = ApiClient(runconfig.WEBSITE_API_BASEURL)
    try:
        report_start(handid)
        # create and launch this handler
        if (callable(handler)):
            handler = handler()
        exitcode, stdout, stderr = handler.execute()
        # try to convert stdout & stderr to unicode in UTF-8 encoding
        # if not success, report the client has produced non UTF-8 output
        try:
            stdout = unicode(stdout, 'utf-8')
            stderr = unicode(stderr, 'utf-8')
        except UnicodeError:
            # This routine will terminate the try-catch structure so that
            # we must report the exitcode earlier as well.
            api.proclog(handid, exitcode, None, None)
            raise NonUTF8OutputError()
        # log the handin execution
        if (exitcode != 0):
            logger.warning(
                'Handin[%(handid)s] of hw[%(hwid)s]: Error.\n'
                '  stdout: %(stdout)s\n'
                '  stderr: %(stderr)s' %
                {'handid': handid, 'hwid': hwid, 'stdout': repr(stdout),
                 'stderr': repr(stderr)}
            )
        # Report failure if exitcode != 0. In this case the host itself may
        # not have the chance to report handin scores
        if (exitcode != 0):
            # We do not raise RunnerError here, because under this situation,
            # we must have logged such exception, and do not want to log
            # again.
            score = HwScore(
                False,
                gettext_lazy('Exitcode %(exitcode)s != 0.',
                             exitcode=exitcode)
            )
            api.report(handid, score)
        # Update exitcode, stdout and stderr here, which cannot be set in
        # the host itself.
        #
        # This process may also change Handin.state, if previous process
        # exit with code 0 before it reported the score. See website/api.py
        # for more details.
        api.proclog(handid, exitcode, stdout, stderr)
        # Log that we've succesfully done this job.
        logger.info(
            'Handin[%(handid)s] of hw[%(hwid)s]: OK.' %
            {'handid': handid, 'hwid': hwid}
        )

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
def run_python(handid, hwid, upload, options):
    """Run a given handin as Python."""
    # The actual creation of `PythonHandin` is delayed until `run_handin` is
    # started, so that exceptions raised in the constructor can be reported.
    return run_handin(
        (lambda: PythonHandin(handid, hwid, upload, options)),
        handid,
        hwid
    )


@app.task
def run_netapi(handid, hwid, remote_addr, options):
    """Check the given `remote_addr` as NetAPI handin."""
    return run_handin(
        (lambda: NetApiHandin(handid, hwid, remote_addr, options)),
        handid,
        hwid
    )
