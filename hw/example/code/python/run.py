#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: hw/test/code/python/run.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import unittest
from pyhost.scorer import ScorerSet, UnitTestScorer


class AdderTestCase(unittest.TestCase):

    def test_add(self):
        # NOTE: any modules handed by student should only be loaded until the
        #       test is actually called. This is because the test runner will
        #       guarded by C module instead of Python, so that the result
        #       reporter will be prevent from injection.
        from arith import add
        self.assertEqual(add(1, 2), 3)

    def test_subtract(self):
        from arith import subtract
        self.assertEqual(subtract(1, 2), -1)


if (__name__ == '__main__'):
    scorers = ScorerSet()
    scorers.add(UnitTestScorer.fromTestCase(AdderTestCase), 1.0)
    # safeRunner.run(scorers)
