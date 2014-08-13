#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: hw/arith_api/code/netapi/run.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import os
import json
import requests
import unittest

from pyhost.scorer import UnitTestScorer
from pyhost import SafeRunner


class ArithApiUnitTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(ArithApiUnitTest, self).__init__(*args, **kwargs)
        self.base_url = os.environ['RAILGUN_API_URL'].rstrip('/')

    def _post(self, action, payload):
        payload = json.dumps(payload)
        try:
            ret = requests.post(self.base_url + action, data=payload,
                                headers={'Content-Type': 'application/json'})
            ret = ret.text
        except Exception:
            raise Exception("Cannot get response from remote API.")
        try:
            return json.loads(ret)
        except Exception:
            raise ValueError("%(msg)s not json." % {'msg': ret})

    def test_add(self):
        self.assertTrue(self._post('/add/', {'a': 1, 'b': 2}), 3)

    def test_pow(self):
        self.assertTrue(self._post('/pow/', {'a': 2, 'b': 100}), 2**100)

    def test_gcd(self):
        self.assertTrue(self._post('/gcd/', {'a': 2, 'b': 4}), 2)

if (__name__ == '__main__'):
    scorers = [
        (UnitTestScorer.FromTestCase(ArithApiUnitTest), 1.0),
    ]
    SafeRunner.run(scorers)
