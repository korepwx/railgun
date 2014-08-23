#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: hw/arith_api/code/netapi/run.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import os
import json
import requests
import unittest

from pyhost.scorer import UnitTestScorer
import SafeRunner


class ArithApiUnitTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(ArithApiUnitTest, self).__init__(*args, **kwargs)
        self.base_url = os.environ['RAILGUN_REMOTE_ADDR'].rstrip('/')

    def _post(self, action, payload):
        """Do post and get remote api result."""

        payload = json.dumps(payload)
        # Get remote response
        try:
            ret = requests.post(self.base_url + action, data=payload,
                                headers={'Content-Type': 'application/json'})
        except Exception:
            raise RuntimeError("Cannot get response from remote API.")

        # Check response status
        if (ret.status_code != 200):
            raise RuntimeError("HTTP status %d != 200." % ret.status_code)
        ret = ret.text

        # Convert response to object
        try:
            return json.loads(ret)
        except Exception:
            raise ValueError(
                "Response '%(msg)s' is not json." % {'msg': ret})

    def _get_result(self, action, payload):
        """Ensure the remote api does not return error, and get 'value' from
        remote api result."""

        ret = self._post(action, payload)
        if (ret['error'] != 0):
            raise RuntimeError("Remote API error: %s." % ret['message'])
        return ret['result']

    def test_add(self):
        self.assertEqual(self._get_result('/add/', {'a': 1, 'b': 2}), 3)

    def test_pow(self):
        self.assertEqual(self._get_result('/pow/', {'a': 2, 'b': 100}), 2**100)

    def test_gcd(self):
        self.assertEqual(self._get_result('/gcd/', {'a': 2, 'b': 4}), 2)

if (__name__ == '__main__'):
    scorers = [
        (UnitTestScorer.FromTestCase(ArithApiUnitTest), 1.0),
    ]
    SafeRunner.run(scorers)
