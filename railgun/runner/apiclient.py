#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/runner/apiclient.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import json
import requests

from railgun.common.hw import get_comm_key
from railgun.common.crypto import EncryptMessage
from . import runconfig


class ApiClient(object):
    """API client for runner to interact with website."""

    def __init__(self, baseurl):
        self.baseurl = baseurl
        self.key = get_comm_key()

    def _get_url(self, action):
        """Get the url for `action`."""

        return '%s%s' % (self.baseurl, action)

    def _cert_kwargs(self):
        """Construct the `certs` kwargs for web requests."""
        if (runconfig.WEBSITE_API_SSL_CERT):
            return {'certs': (runconfig.WEBSITE_API_SSL_CERT, )}
        return {}

    def post(self, action, payload):
        """Post `payload` to `action` at remote api."""

        payload = EncryptMessage(json.dumps(payload), self.key)
        return requests.post(
            self._get_url(action),
            data=payload,
            headers={'Content-Type': 'application/octet-stream'},
            **self._cert_kwargs()
        )

    def report(self, handid, hwscore):
        """Report `hwscore` to remote api."""

        obj = hwscore.to_plain()
        obj['uuid'] = handid
        return self.post('/handin/report/%s/' % handid, payload=obj)

    def start(self, handid):
        """Update state of `handid` to running."""

        obj = {'uuid': handid}
        return self.post('/handin/start/%s/' % handid, payload=obj)

    def proclog(self, handid, exitcode, stdout, stderr):
        """Log process (exitcode, stdout, stderr) of `handid`."""

        obj = {'uuid': handid, 'exitcode': exitcode, 'stdout': stdout,
               'stderr': stderr}
        return self.post('/handin/proclog/%s/' % handid, payload=obj)
