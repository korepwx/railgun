#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/runner/tasks.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

"""This module defines all :class:`celery.Task` objects.

A :class:`~celery.Task` object is a proxy for the foreground process to
queue their jobs into the Celery background runner.  The communications
are managed by the Celery framework, and the client may not care about
these details.

For example, if you want to run a long-time job in the background
runner, you may decorate the job method with :meth:`app.task`::

    @app.task
    def RestartService(name):
        os.system('sudo service %s restart' % name)

Then you can tell Celery to queue and run that method in your foreground
process::

    from tasks import RestartService

    RestartService.delay('dnsmasq')

:class:`~celery.Task` defined in this module are mainly used in
:mod:`railgun.website.codelang`.  You may also refer to
:ref:`celery:guide-tasks` to learn more about how to define a task, and
:ref:`celery:guide-calling` about how to call a task.
"""

from . import runconfig, permcheck
from .apiclient import ApiClient, report_error, report_start
from .context import app, logger
from .handin import PythonHandin, NetApiHandin, InputClassHandin
from .errors import (RunnerError, InternalServerError, NonUTF8OutputError,
                     RunnerPermissionError)
from railgun.common.hw import HwScore
from railgun.common.lazy_i18n import lazy_gettext


def run_handin(handler, handid, hwid):
    """Common pattern to run a submission.  Its main function is to
    glue :class:`~railgun.runner.handin.BaseHandin`,
    :class:`~railgun.runner.host.BaseHost` and
    :class:`~railgun.runner.apiclient.ApiClient` together.

    It is guaranteed that all errors are handled and logged correctly in this
    method.

    :param handler: A factory to create a
        :class:`~railgun.runner.handin.BaseHandin` handler object.
    :param handid: The uuid of this submission.
    :type handid: :class:`str`
    :param hwid: The uuid of the homework.
    :type hwid: :class:`str`
    """
    # Create the api client, we may use it once or twice
    api = ApiClient(runconfig.WEBSITE_API_BASEURL)
    # Immediately report error if permcheck has error
    if permcheck.checker.has_error():
        report_error(handid, RunnerPermissionError())
        return
    try:
        report_start(handid)
        # create and launch this handler
        if callable(handler):
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
        if exitcode != 0:
            logger.warning(
                'Submission[%(handid)s] of hw[%(hwid)s]: Error.\n'
                '  stdout: %(stdout)s\n'
                '  stderr: %(stderr)s' %
                {'handid': handid, 'hwid': hwid, 'stdout': repr(stdout),
                 'stderr': repr(stderr)}
            )
        # Report failure if exitcode != 0. In this case the host itself may
        # not have the chance to report handin scores
        if exitcode != 0:
            # We do not raise RunnerError here, because under this situation,
            # we must have logged such exception, and do not want to log
            # again.
            score = HwScore(
                False,
                lazy_gettext('Exitcode %(exitcode)s != 0.',
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
            'Submission[%(handid)s] of hw[%(hwid)s]: OK.' %
            {'handid': handid, 'hwid': hwid}
        )
    except RunnerError, ex:
        # RunnerError is logically OK and sent to client only.
        # So we just log the message of this exception, not exception detail.
        logger.warning(
            'Submission[%(handid)s] of hw[%(hwid)s]: %(message)s.' %
            {'handid': handid, 'hwid': hwid, 'message': ex.message}
        )
        report_error(handid, ex)
    except Exception:
        logger.exception(
            'Error executing submission "%(handid)s" for homework "%(hwid)s".'
            % {'handid': handid, 'hwid': hwid}
        )
        report_error(handid, InternalServerError())


@app.task
def run_python(handid, hwid, upload, options):
    """Run the given Python submission.

    :handler: :class:`~railgun.common.handin.PythonHandin`
    :param handid: The uuid of this submission.
    :type handid: :class:`str`
    :param hwid: The uuid of the homework.
    :type hwid: :class:`str`
    :param upload: The uploaded archive file content encoded in base64.
    :type upload: :class:`str`
    :param options: {'filename': the uploaded filename}
    :type options: :class:`dict`
    """
    # The actual creation of `PythonHandin` is delayed until `run_handin` is
    # started, so that exceptions raised in the constructor can be reported.
    return run_handin(
        (lambda: PythonHandin(handid, hwid, upload, options)),
        handid,
        hwid
    )


@app.task
def run_netapi(handid, hwid, remote_addr, options):
    """Run the given NetAPI submission.

    :handler: :class:`~railgun.common.handin.NetApiHandin`
    :param handid: The uuid of this submission.
    :type handid: :class:`str`
    :param hwid: The uuid of the homework.
    :type hwid: :class:`str`
    :param remote_addr: The submitted url address.
    :type remote_addr: :class:`str`
    :param options: {}
    :type options: :class:`dict`
    """
    return run_handin(
        (lambda: NetApiHandin(handid, hwid, remote_addr, options)),
        handid,
        hwid
    )


@app.task
def run_input(handid, hwid, csvdata, options):
    """Run the given CSV data submission.

    :handler: :class:`~railgun.common.handin.InputClassHandin`
    :param handid: The uuid of this submission.
    :type handid: :class:`str`
    :param hwid: The uuid of the homework.
    :type hwid: :class:`str`
    :param csvdata: The submitted csv file content.
    :type csvdata: :class:`str`
    :param options: {}
    :type options: :class:`dict`
    """
    return run_handin(
        (lambda: InputClassHandin(handid, hwid, csvdata, options)),
        handid,
        hwid
    )
