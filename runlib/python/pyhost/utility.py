#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: runlib/python/pyhost/utility.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import unittest

from railgun.common.lazy_i18n import gettext_lazy


class UnitTestScorerDetailResult(unittest.TestResult):
    """A test result class that gather detailed unittest report.
    Used by UnitTestScorer."""

    def __init__(self):
        super(UnitTestScorerDetailResult, self).__init__()
        self.details = []

    def getDescription(self, test):
        """Get description string of given `test`."""
        return str(test)

    def startTest(self, test):
        super(UnitTestScorerDetailResult, self).startTest(test)

    def addSuccess(self, test):
        super(UnitTestScorerDetailResult, self).addSuccess(test)
        self.details.append(gettext_lazy(
            'PASSED: %(test)s.',
            test=self.getDescription(test)
        ))

    def addError(self, test, err):
        super(UnitTestScorerDetailResult, self).addError(test, err)
        self.details.append(gettext_lazy(
            'ERROR: %(test)s.\n%(error)s',
            test=self.getDescription(test),
            error=self._exc_info_to_string(err, test)
        ))

    def addFailure(self, test, err):
        super(UnitTestScorerDetailResult, self).addFailure(test, err)
        self.details.append(gettext_lazy(
            'FAIL: %(test)s.\n%(error)s',
            test=self.getDescription(test),
            error=self._exc_info_to_string(err, test)
        ))

    def addSkip(self, test, reason):
        super(UnitTestScorerDetailResult, self).addSkip(test, reason)
        self.details.append(gettext_lazy(
            'SKIP: %(test)s: %(reason)s.',
            test=self.getDescription(test),
            reason=reason
        ))

    def addExpectedFailure(self, test, err):
        super(UnitTestScorerDetailResult, self).addExpectedFailure(test, err)
        self.details.append(gettext_lazy(
            'EXPECTED FAIL: %(test)s.\n%(error)s',
            test=self.getDescription(test),
            error=self._exc_info_to_string(err, test)
        ))

    def addUnexpectedSuccess(self, test):
        super(UnitTestScorerDetailResult, self).addUnexpectedSuccess(test)
        self.details.append(gettext_lazy(
            'UNEXPECTED SUCCESS: %(test)s.',
            test=self.getDescription(test)
        ))

    def printErrors(self):
        pass
