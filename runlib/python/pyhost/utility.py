#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: runlib/python/pyhost/utility.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import re
import pep8
import unittest
import traceback

from railgun.common.lazy_i18n import lazy_gettext


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
        self.details.append(lazy_gettext(
            'PASSED: %(test)s.',
            test=self.getDescription(test)
        ))

    def addError(self, test, err):
        super(UnitTestScorerDetailResult, self).addError(test, err)
        self.details.append(lazy_gettext(
            'ERROR: %(test)s.\n%(error)s',
            test=self.getDescription(test),
            error=self._exc_info_to_string(err, test)
        ))

    def addFailure(self, test, err):
        super(UnitTestScorerDetailResult, self).addFailure(test, err)
        self.details.append(lazy_gettext(
            'FAIL: %(test)s.\n%(error)s',
            test=self.getDescription(test),
            error=self._exc_info_to_string(err, test)
        ))

    def addSkip(self, test, reason):
        super(UnitTestScorerDetailResult, self).addSkip(test, reason)
        self.details.append(lazy_gettext(
            'SKIP: %(test)s: %(reason)s.',
            test=self.getDescription(test),
            reason=reason
        ))

    def addExpectedFailure(self, test, err):
        super(UnitTestScorerDetailResult, self).addExpectedFailure(test, err)
        self.details.append(lazy_gettext(
            'EXPECTED FAIL: %(test)s.\n%(error)s',
            test=self.getDescription(test),
            error=self._exc_info_to_string(err, test)
        ))

    def addUnexpectedSuccess(self, test):
        super(UnitTestScorerDetailResult, self).addUnexpectedSuccess(test)
        self.details.append(lazy_gettext(
            'UNEXPECTED SUCCESS: %(test)s.',
            test=self.getDescription(test)
        ))

    def printErrors(self):
        pass


class Pep8DetailReport(pep8.BaseReport):
    """Pep8 report class that records each message in memory."""

    def __init__(self, options):
        super(Pep8DetailReport, self).__init__(options)
        self.fmt = '%(path)s:%(row)d:%(col)d: %(text)s'
        self._errors = []
        self._show_source = options.show_source
        self._trouble_files = set()

    def init_file(self, filename, lines, expected, line_offset):
        """Signal a new file."""
        return super(Pep8DetailReport, self).init_file(
            filename, lines, expected, line_offset)

    def error(self, line_number, offset, text, check):
        """Report an error, according to options."""
        code = super(Pep8DetailReport, self).error(line_number, offset,
                                                   text, check)
        if code:
            source = self.lines[line_number - 1].rstrip()
            self._errors.append({
                'path': self.filename,
                'row': line_number + self.line_offset,
                'col': offset + 1,
                'offset': offset,
                'code': code,
                'text': text,
                'source': source,
            })
            self._trouble_files.add(self.filename)
        return code

    def get_file_results(self):
        return super(Pep8DetailReport, self).get_file_results()

    def count_trouble_files(self):
        return len(self._trouble_files)

    def count_errors(self):
        return len(self._errors)

    def build_report(self):
        """Build human readable report text."""

        # sort the errors in (path, row, col, code) order
        def Comparer(a, b):
            return cmp((a['path'], a['row'], a['col'], a['code']),
                       (b['path'], b['row'], b['col'], b['code']))
        self._errors.sort(cmp=Comparer)

        # format the detail report text
        ret = []
        for err in self._errors:
            mark = re.sub(r'\S', ' ', err['source'][: err['offset']]) + '^'
            tmp = [self.fmt % err]
            if self._show_source:
                tmp.append(err['source'])
                tmp.append(mark)
            ret.append('\n'.join(tmp))
        return ret


def format_exeception():
    """Format the exception traceback."""
    return traceback.format_exec().rstrip()
