#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/runner/apiclient.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import os
import json
import requests

from railgun.common.crypto import EncryptMessage
from railgun.common.hw import HwScore
from . import runconfig


def get_comm_key():
    """Load the secret key from ``keys/commKey.txt``.

    :return: The secret key to encrypt and decrypt API post data.
    """
    path = os.path.join(runconfig.RAILGUN_ROOT, 'keys/commKey.txt')
    with open(path, 'rb') as f:
        return f.read().strip()


class ApiClient(object):
    """The API client for runner to communicate with website.

    The runner queue and the runner host should report the results of
    submissions via website api.
    Refer to :ref:`design_webapi` for more details.

    :param baseurl: The base url of website api.
    :type baseurl: :class:`str`
    """

    def __init__(self, baseurl):
        #: Store the base url of website api.
        self.baseurl = baseurl.rstrip('/')
        #: Store the secret communication key.
        self.key = get_comm_key()

    def _get_url(self, action):
        return '%s%s' % (self.baseurl, action)

    def post(self, action, payload):
        """Send `payload` to remote server and execute given `action`.

        :param action: The url of the performing action.
        :type action: :class:`str`
        :param payload: The plain object to be sent.
        :type payload: :class:`object`

        :return: The :class:`requests.Response` object.
        """

        payload = EncryptMessage(json.dumps(payload), self.key)
        return requests.post(
            self._get_url(action),
            data=payload,
            headers={'Content-Type': 'application/octet-stream'},
            verify=False
        )

    def report(self, handid, hwscore):
        """Send the score of given submission.

        :param handid: The uuid of the submission.
        :type handid: :class:`str`
        :param hwscore: The score object.
        :type hwscore: :class:`~railgun.common.hw.HwScore`
        """
        obj = hwscore.to_plain()
        obj['uuid'] = handid
        self.post('/handin/report/%s/' % handid, payload=obj)

    def start(self, handid):
        """Change the status of submission to `Running`.

        :param handid: The uuid of the submission.
        :type handid: :class:`str`
        """
        obj = {'uuid': handid}
        self.post('/handin/start/%s/' % handid, payload=obj)

    def proclog(self, handid, exitcode, stdout, stderr):
        """Store the process exitcode, standard output and standard error
        output of the submission.

        :param handid: The uuid of the submission.
        :type handid: :class:`str`
        :param exitcode: The exit code of the process.
        :type exitcode: :class:`int`
        :param stdout: The standard output of the process.
        :type stdout: :class:`str`
        :param stderr: The standard error output of the process.
        :type stderr: :class:`str`
        """
        obj = {'uuid': handid, 'exitcode': exitcode, 'stdout': stdout,
               'stderr': stderr}
        self.post('/handin/proclog/%s/' % handid, payload=obj)


def report_error(handid, err):
    """Shortcut to report the error of a submission.

    :param handid: The uuid of the submission.
    :type handid: :class:`str`
    :param err: A runner error object holding the error message.
    :type err: :class:`~railgun.runner.errors.RunnerError`
    """
    api = ApiClient(runconfig.WEBSITE_API_BASEURL)
    score = HwScore(False, result=err.message, compile_error=err.compile_error)
    api.report(handid, score)


def report_start(handid):
    """Shortcut to report that a submission has been launched.

    :param handid: The uuid of the submission.
    :type handid: :class:`str`
    """
    api = ApiClient(runconfig.WEBSITE_API_BASEURL)
    api.start(handid)
