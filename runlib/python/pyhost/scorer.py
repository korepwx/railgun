#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: runlib/python/pyhost/scorer.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import unittest
from time import time

from railgun.common.lazy_i18n import gettext_lazy
from .utility import UnitTestScorerDetailResult


class Scorer(object):
    """Base class for all scorers. All scorers should give a score between
    0 and 100."""

    def __init__(self, name):
        # name of the score
        self.name = name
        # time used by this module
        self.time = None
        # final score of the testing module
        self.score = None
        # brief explanation of the score
        self.brief = None
        # detail explanation of the score
        self.detail = None

    def run(self):
        """run the testing module and generate the score"""


class UnitTestScorer(Scorer):
    """scorer according to the result of unit test"""

    def __init__(self, suite):
        super(UnitTestScorer, self).__init__(gettext_lazy('UnitTest Scorer'))
        self.suite = suite

    def run(self):
        # get the result of unittest
        result = UnitTestScorerDetailResult()
        startTime = time()
        self.suite.run(result)
        self.time = time() - startTime
        # format score and reports according to unittest result
        total = self.suite.countTestCases()
        errors, failures = map(len, (result.errors, result.failures))
        # give out a score according to the above statistics
        success = total - (errors + failures)
        self.score = 100.0 * success / total
        # format the brief report
        self.brief = gettext_lazy(
            'Ran %(total)d tests in %(time).3f seconds, among which '
            '%(success)d tests passed.',
            total=total, time=self.time, success=success
        )
        # format the detailed report
        self.detail = result.details

    @staticmethod
    def fromTestCase(testcase):
        """Make a `UnitTestScorer` instance from `testcase`"""
        return UnitTestScorer(
            unittest.TestLoader().loadTestsFromTestCase(testcase)
        )
