#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: runlib/python/pyhost/scorer.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import re
import os
import pep8
import unittest
from time import time

from railgun.common.fileutil import dirtree
from railgun.common.lazy_i18n import lazy_gettext
from railgun.common.csvdata import CsvSchema
from .errors import ScorerFailure
from .utility import UnitTestScorerDetailResult, Pep8DetailReport
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
            startTime = time()
            self._run()
            self.time = time() - startTime
        except ScorerFailure, ex:
            self.brief = ex.brief
            self.detail = ex.detail
            self.score = ex.score


class UnitTestScorer(Scorer):
    """scorer according to the result of unit test"""

    def __init__(self, suite):
        super(UnitTestScorer, self).__init__(lazy_gettext('UnitTest Scorer'))
        self.suite = suite

    def _run(self):
        # if self.suite is callable, then load the suite now
        # this is useful when dealing with student uploaded test case.
        if (callable(self.suite)):
            self.suite = self.suite()
        # get the result of unittest
        result = UnitTestScorerDetailResult()
        self.suite.run(result)
        # format score and reports according to unittest result
        total = self.suite.countTestCases()
        errors, failures = map(len, (result.errors, result.failures))
        # give out a score according to the above statistics
        success = total - (errors + failures)
        self.score = 100.0 * success / total
        # format the brief report
        self.brief = lazy_gettext(
            '%(success)d out of %(total)d tests passed',
            total=total, time=self.time, success=success
        )
        # format the detailed report
        self.detail = result.details

    @staticmethod
    def FromTestCase(testcase):
        """Make a `UnitTestScorer` instance from `testcase`"""
        return UnitTestScorer(
            lambda: unittest.TestLoader().loadTestsFromTestCase(testcase))

    @staticmethod
    def FromNames(names):
        """Make a `UnitTestScorer` instance from test case `names`."""
        suite = lambda: unittest.TestLoader().loadTestsFromNames(names)
        return UnitTestScorer(suite)


class CodeStyleScorer(Scorer):
    """scorer according to the code style."""

    def __init__(self, filelist, skipfile=None):
        """Check the code style of `filelist`, skip if `skipfile(path)` is
        True."""

        super(CodeStyleScorer, self).__init__(lazy_gettext('CodeStyle Scorer'))
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
            self.brief = lazy_gettext(
                '%(trouble)d files out of %(total)d did not pass PEP8 code '
                'style check',
                total=total_file, trouble=trouble_file
            )
        else:
            self.brief = lazy_gettext('All files passed PEP8 code style check')

        # format detailed reports
        self.detail = result.build_report()

    @staticmethod
    def FromHandinDir(ignore_files=None):
        """Create a `CodeStyleScorer` for all files under handin directory
        except `ignore_files`."""

        ignore_files = ignore_files or []
        if (isinstance(ignore_files, str) or isinstance(ignore_files, unicode)):
            ignore_files = [ignore_files]
        return CodeStyleScorer(dirtree('.'), (lambda p: p in ignore_files))


class CoverageScorer(Scorer):
    """scorer according to the result of coverage."""

    def __init__(self, suite, filelist):
        '''
        Run all test cases in `suite` and then get the coverage of all files
        in `filelist`.
        '''
        super(CoverageScorer, self).__init__(lazy_gettext('Coverage Scorer'))

        self.suite = suite
        self.filelist = filelist

    def _run(self):
        cov = coverage()
        cov.start()

        # If self.suite is callable, generate test suite first
        if (callable(self.suite)):
            self.suite = self.suite()

        # Run the test suite
        # the `result` is now ignored, but we can get use of it if necessary
        result = UnitTestScorerDetailResult()
        self.suite.run(result)

        cov.stop()

        # count coverage rate
        total_exec = 0
        total_miss = 0
        self.detail = []
        for filename in self.filelist:
            (name, exec_stmt, miss_stmt, formatted) = \
                cov.analysis(filename)
            total_exec += len(exec_stmt)
            total_miss += len(miss_stmt)
            # convert exec_stmt and miss_stmt to set so that we can query
            # about one line fastly
            exec_stmt = set(exec_stmt)
            miss_stmt = set(miss_stmt)
            # gather all lines into detail report
            srctext = []
            with open(filename, 'rb') as fsrc:
                for i, s in enumerate(fsrc, 1):
                    if i in miss_stmt:
                        srctext.append('- %s' % s.rstrip())
                    elif i in exec_stmt:
                        srctext.append('+ %s' % s.rstrip())
                    else:
                        srctext.append('  %s' % s.rstrip())
            # compose final detail
            srctext = '\n'.join(srctext)
            self.detail.append(lazy_gettext(
                '%(filename)s: %(miss)d lines not covered.\n'
                '%(sep)s\n'
                '%(source)s',
                filename=filename, sep='-' * 70, miss=len(miss_stmt),
                source=srctext
            ))

        self.cover_rate = 100 - 100.0 * total_miss / total_exec
        self.score = self.cover_rate

        self.brief = lazy_gettext(
            'Coverage rate: %(cover_rate)2.1f%%',
            time=self.time, cover_rate=self.cover_rate
        )

    @staticmethod
    def FromHandinDir(files_to_cover, test_pattern='test_.*\\.py$'):
        """Create a `CoverageScorer` to get score for all unit tests provided
        by students according to the coverage of files in `files_to_cover`.

        Only the files matching `test_pattern` will be regarded as unit test
        file.
        """

        p = re.compile(test_pattern)
        test_modules = []
        for f in dirtree('.'):
            fpath, fext = os.path.splitext(f)
            if (fext.lower() == '.py' and p.match(f)):
                test_modules.append(fpath.replace('/', '.'))

        suite = lambda: unittest.TestLoader().loadTestsFromNames(test_modules)
        return CoverageScorer(suite, files_to_cover)


class InputClassScorer(Scorer):
    """Scorer to the input data for BlackBox testing."""

    def __init__(self, schema, csvdata, check_classes=None):
        """Construct a new `InputClassScorer` on given `csvdata`, checked by
        rules defined in `check_classes`."""

        super(InputClassScorer, self).__init__(
            lazy_gettext('InputClass Scorer')
        )

        self.schema = schema
        self.csvdata = csvdata
        self.check_classes = check_classes or []

    def getDescription(self, check_class):
        """Get the description for given `check_class`."""

        if (hasattr(check_class, 'description')):
            return getattr(check_class, 'description')
        if (hasattr(check_class, '__name__')):
            return getattr(check_class, '__name__')
        return str(check_class)

    def rule(self, description):
        """Decorator to add given `method` into `check_classes`."""
        def outer(method):
            """Direct decorator on `method` which set method.description."""
            setattr(method, 'description', description)
            self.check_classes.append(method)
            return method
        return outer

    def _run(self):
        try:
            self.detail = []
            covered = set()
            for obj in CsvSchema.LoadCSV(self.schema, self.csvdata):
                # each record should be sent to all check classes, to see
                # what classes it covered
                for i, c in enumerate(self.check_classes):
                    if c(obj):
                        covered.add(i)
            # total up score by len(covered) / total_classes
            self.score = 100.0 * len(covered) / len(self.check_classes)
            self.brief = lazy_gettext(
                'Covered %(cover)s input classes out of %(total)s',
                cover=len(covered), total=len(self.check_classes)
            )
            # build more detailed report
            for i, c in enumerate(self.check_classes):
                if i in covered:
                    self.detail.append(lazy_gettext(
                        'COVERED: %(checker)s',
                        checker=self.getDescription(c)
                    ))
                else:
                    self.detail.append(lazy_gettext(
                        'NOT COVERED: %(checker)s',
                        checker=self.getDescription(c)
                    ))
        except KeyError, ex:
            raise ScorerFailure(
                brief=lazy_gettext('CSV data does not match schema.'),
                detail=[ex.args[0]]
            )
        except ValueError, ex:
            raise ScorerFailure(
                brief=lazy_gettext('CSV data does not match schema.'),
                detail=[ex.args[0]]
            )
