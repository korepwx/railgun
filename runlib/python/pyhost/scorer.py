#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: runlib/python/pyhost/scorer.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
#   Dawei Yang           <davy.pristina@gmail.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import pep8
import unittest
from time import time

from railgun.common.fileutil import dirtree
from railgun.common.lazy_i18n import gettext_lazy
from .errors import ScorerFailure
from .utility import UnitTestScorerDetailResult, Pep8DetailReport, \
    load_module_from_file
from coverage import coverage


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

    def _run(self):
        pass

    def run(self):
        """Run the testing module and generate the score. If a `ScorerFailure`
        is generated, the score will be set to 0.0."""
        try:
            self._run()
        except ScorerFailure, ex:
            self.brief = ex.brief
            self.detail = ex.detail
            self.score = ex.score


class UnitTestScorer(Scorer):
    """scorer according to the result of unit test"""

    def __init__(self, suite):
        super(UnitTestScorer, self).__init__(gettext_lazy('UnitTest Scorer'))
        self.suite = suite

    def _run(self):
        # if self.suite is callable, then load the suite now
        # this is useful when dealing with student uploaded test case.
        if (callable(self.suite)):
            self.suite = self.suite()
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
            'Ran %(total)d tests in %(time).3f seconds, while '
            '%(success)d tests passed.',
            total=total, time=self.time, success=success
        )
        # format the detailed report
        self.detail = result.details

    @staticmethod
    def FromTestCase(testcase):
        """Make a `UnitTestScorer` instance from `testcase`"""
        return UnitTestScorer(
            lambda: unittest.TestLoader().loadTestsFromTestCase(testcase)
        )


class CodeStyleScorer(Scorer):
    """scorer according to the code style."""

    def __init__(self, filelist, skipfile=None):
        """Check the code style of `filelist`, skip if `skipfile(path)` is
        True."""

        super(CodeStyleScorer, self).__init__(gettext_lazy('CodeStyle Scorer'))
        skipfile = skipfile or (lambda path: False)
        is_pyfile = lambda p: (p[-3:].lower() == '.py')
        self.filelist = [p for p in filelist
                         if not skipfile(p) and is_pyfile(p)]

    def _run(self):
        guide = pep8.StyleGuide()
        guide.options.show_source = True
        guide.options.report = Pep8DetailReport(guide.options)
        result = guide.check_files(self.filelist)

        # the final score should be count_trouble_files() / total_file
        total_file = len(self.filelist)
        trouble_file = result.count_trouble_files()
        self.score = 100.0 * (total_file - trouble_file) / total_file

        # format the brief report
        if (trouble_file > 0):
            self.brief = gettext_lazy(
                '%(trouble)d files out of %(total)d did not pass PEP8 code '
                'style check',
                total=total_file, trouble=trouble_file
            )
        else:
            self.brief = gettext_lazy('All files passed PEP8 code style check.')

        # format detailed reports
        self.detail = result.build_report()

    @staticmethod
    def FromHandinDir(ignore_files=None):
        """Create a `CodeStyleScorer` for all files under handin directory
        except `ignore_files`."""

        ignore_files = ignore_files or []
        return CodeStyleScorer(dirtree('.'), (lambda p: p in ignore_files))


class CoverageScorer(Scorer):
    """scorer according to the result of coverage."""

    def __init__(self, test_files, filelist):
        '''
        `test_files` is a list of filename, provided by students,
        to test files in `filelist`, provided by teachers.
        '''
        super(CoverageScorer, self).__init__(gettext_lazy('Coverage Scorer'))

        self.suites_list = map(
            lambda filename: unittest.TestLoader().loadTestsFromModule(load_module_from_file(filename)),
            test_files
        )

        self.filelist = filelist

    def _run(self):
        cov = coverage()
        cov.start()

        startTime = time()

        for suites in self.suites_list:
            for suite in suites:
                suite.run(unittest.TestResult())
        self.time = time() - startTime

        cov.stop()

        # count coverage rate
        total_exec = 0
        total_miss = 0
        self.detail = []
        for filename in self.filelist:
            (name, exec_statements, miss_statement, formatted) = cov.analysis(filename)
            total_exec += len(exec_statements)
            total_miss += len(miss_statement)
            self.detail.append(gettext_lazy(
                '%(filename)s: missing %(formatted)s\n',
                filename=filename, formatted=formatted
            ))

        self.cover_rate = 100 - 100.0 * total_miss / total_exec
        self.score = self.cover_rate

        self.brief = gettext_lazy(
            'Ran coverage in %(time).3f seconds,'
            ' coverage rate: %(cover_rate)2.1f%%',
            time=self.time, cover_rate=self.cover_rate
        )

    @staticmethod
    def FromHandinDir(files_to_coverage, ignore_files=None):
        """Create a `CodeStyleScorer` for all files under handin directory
        except `ignore_files`."""
        ignore_files = ignore_files or []
        all_files = dirtree('.')
        suite_files = set(all_files) - set(ignore_files)

        return CoverageScorer(suite_files, files_to_coverage)
