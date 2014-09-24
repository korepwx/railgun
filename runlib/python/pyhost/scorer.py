#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: runlib/python/pyhost/scorer.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import re
import os
from time import time

import pep8
import unittest
from coverage import coverage

from railgun.common.fileutil import dirtree
from railgun.common.lazy_i18n import lazy_gettext
from railgun.common.csvdata import CsvSchema
from .errors import ScorerFailure
from .utility import UnitTestScorerDetailResult, Pep8DetailReport
from .objschema import SchemaResultCollector


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
        super(UnitTestScorer, self).__init__(
            lazy_gettext('Functionality Scorer'))
        self.suite = suite

    def _run(self):
        # if self.suite is callable, then load the suite now
        # this is useful when dealing with student uploaded test case.
        if callable(self.suite):
            self.suite = self.suite()
        # get the result of unittest
        result = UnitTestScorerDetailResult()
        self.suite.run(result)
        # format score and reports according to unittest result
        total = self.suite.countTestCases()
        errors, failures = map(len, (result.errors, result.failures))
        # give out a score according to the above statistics
        success = total - (errors + failures)
        if total > 0:
            self.score = 100.0 * success / total
        else:
            self.score = 100.0
        # format the brief report
        self.brief = lazy_gettext(
            '%(rate).2f%% tests (%(success)d out of %(total)d) passed',
            rate=self.score, total=total, time=self.time, success=success
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

    def __init__(self, filelist, skipfile=None, errcost=10.0):
        """Check the code style of `filelist`, skip if `skipfile(path)` is
        True."""

        super(CodeStyleScorer, self).__init__(lazy_gettext('CodeStyle Scorer'))
        skipfile = skipfile or (lambda path: False)
        is_pyfile = lambda p: (p[-3:].lower() == '.py')
        self.filelist = [p for p in filelist
                         if not skipfile(p) and is_pyfile(p)]
        self.errcost = errcost

    def _run(self):
        guide = pep8.StyleGuide()
        guide.options.show_source = True
        guide.options.report = Pep8DetailReport(guide.options)
        result = guide.check_files(self.filelist)

        # Each error consumes 1 point.
        errcount = result.count_errors()
        self.score = 100.0 - errcount * self.errcost
        if self.score < 0.0:
            self.score = 0.0

        # format the brief report
        total_file = len(self.filelist)
        if errcount > 0:
            self.brief = lazy_gettext(
                '%(trouble)d problem(s) found in %(file)d file(s)',
                trouble=errcount, file=total_file
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
        if (isinstance(ignore_files, str) or
                isinstance(ignore_files, unicode)):
            ignore_files = [ignore_files]
        return CodeStyleScorer(dirtree('.'), (lambda p: p in ignore_files))


class CoverageScorer(Scorer):
    """scorer according to the result of coverage."""

    def __init__(self, suite, filelist, stmt_weight=0.5, branch_weight=0.5):
        '''
        Run all test cases in `suite` and then get the coverage of all files
        in `filelist`.
        '''
        super(CoverageScorer, self).__init__(lazy_gettext('Coverage Scorer'))

        self.suite = suite
        self.brief = []
        self.filelist = filelist
        self.stmt_weight = stmt_weight
        self.branch_weight = branch_weight

    def _run(self):
        def safe_divide(a, b, default=1.0):
            if b > 0:
                return float(a) / float(b)
            return default

        cov = coverage(branch=True)
        cov.start()

        # If self.suite is callable, generate test suite first
        if callable(self.suite):
            self.suite = self.suite()

        # Run the test suite
        # the `result` is now ignored, but we can get use of it if necessary
        result = UnitTestScorerDetailResult()
        self.suite.run(result)
        cov.stop()

        # the 1st part: total view of the coverage stats
        self.detail = ['']
        total_cov = []

        # statement coverage rate
        total_exec = total_miss = 0
        total_branch = total_taken = total_partial = total_notaken = 0
        for filename in self.filelist:
            # get the analysis on given filename
            ana = cov._analyze(filename)
            # gather statement coverage on this file
            exec_stmt = set(ana.statements)
            miss_stmt = set(ana.missing)
            total_exec += len(exec_stmt)
            total_miss += len(miss_stmt)
            # gather branch coverage on this file
            # branch: {lineno: (total_exit, taken_exit)}
            branch = ana.branch_stats()
            file_branch = len(branch)
            file_taken = len([b for b in branch.itervalues() if b[0] == b[1]])
            file_notaken = len([b for b in branch.itervalues()
                                if b[0] != b[1] and b[1] == 0])
            file_partial = file_branch - file_taken - file_notaken
            # add the file stats to total coverage results
            total_cov.append(
                '%(file)s, %(stmt)d, %(stmt_taken)d, %(stmt_cov).2f%%, '
                '%(branch)d, %(branch_taken)d, %(branch_partial)d, '
                '%(branch_cov).2f%%, %(branch_partial_cov).2f%%' % {
                    'file': filename,
                    'stmt': len(exec_stmt),
                    'stmt_taken': len(exec_stmt) - len(miss_stmt),
                    'stmt_cov': 100.0 * safe_divide(
                        len(exec_stmt) - len(miss_stmt), len(exec_stmt)),
                    'branch': file_branch,
                    'branch_taken': file_taken,
                    'branch_partial': file_partial,
                    'branch_cov': 100.0 * safe_divide(file_taken, file_branch),
                    'branch_partial_cov': 100.0 * safe_divide(
                        file_partial, file_branch, default=0.0)
                }
            )
            # apply file branch to global
            total_branch += file_branch
            total_taken += file_taken
            total_partial += file_partial
            total_notaken += file_notaken

            # gather all source lines into detail report
            stmt_text = []
            branch_text = []
            with open(filename, 'rb') as fsrc:
                for i, s in enumerate(fsrc, 1):
                    # first, format statement cover report
                    if i in miss_stmt:
                        stmt_text.append('- %s' % s.rstrip())
                    elif i in exec_stmt:
                        stmt_text.append('+ %s' % s.rstrip())
                    else:
                        stmt_text.append('  %s' % s.rstrip())
                    # next, format branch cover report
                    branch_exec = branch.get(i, None)
                    if not branch_exec:
                        branch_text.append('  %s' % s.rstrip())
                    elif branch_exec[1] == branch_exec[0]:
                        # branch taken
                        branch_text.append('+ %s' % s.rstrip())
                    elif branch_exec[1] == 0:
                        # branch not taken
                        branch_text.append('- %s' % s.rstrip())
                    else:
                        # branch partial taken
                        branch_text.append('* %s' % s.rstrip())
            # compose final detail
            stmt_text = '\n'.join(stmt_text)
            branch_text = '\n'.join(branch_text)

            # the statement coverage
            self.detail.append(lazy_gettext(
                '%(filename)s: %(miss)d statement(s) not covered.\n'
                '%(sep)s\n'
                '%(source)s',
                filename=filename, sep='-' * 70, miss=len(miss_stmt),
                source=stmt_text
            ))

            # the branch coverage
            self.detail.append(lazy_gettext(
                '%(filename)s: '
                '%(partial)d branch(es) partially taken and '
                '%(notaken)d branch(es) not taken.\n'
                '%(sep)s\n'
                '%(source)s',
                filename=filename, sep='-' * 70, miss=len(miss_stmt),
                source=branch_text, taken=file_taken, notaken=file_notaken,
                partial=file_partial
            ))

        self.stmt_cover = 100.0 - 100.0 * safe_divide(total_miss, total_exec)
        self.branch_cover = 100.0 * safe_divide(total_taken, total_branch)
        self.branch_partial = 100.0 * safe_divide(
            total_partial, total_branch, default=0.0)

        # Add final total report
        self.detail[0] = lazy_gettext(
            'Coverage Results:\n'
            '%(delim1)s\n'
            'file, stmts, taken, covered, branches, taken, partially taken, '
            'covered, partially covered\n'
            '%(delim2)s\n'
            '%(detail)s\n'
            '%(delim2)s\n'
            'total, %(stmt)d, %(stmt_taken)d, %(stmt_cov).2f%%, '
            '%(branch)d, %(branch_taken)d, %(branch_partial)d, '
            '%(branch_cov).2f%%, %(branch_partial_cov).2f%%',
            delim1='=' * 70,
            delim2='-' * 70,
            detail='\n'.join(total_cov),
            stmt=total_exec,
            stmt_taken=total_exec - total_miss,
            stmt_cov=self.stmt_cover,
            branch=total_branch,
            branch_taken=total_taken,
            branch_partial=total_partial,
            branch_cov=self.branch_cover,
            branch_partial_cov=self.branch_partial,
        )

        # final score
        stmt_score = self.stmt_cover * self.stmt_weight
        full_branch_score = self.branch_cover * self.branch_weight
        partial_branch_score = self.branch_partial * self.branch_weight * 0.5

        self.score = stmt_score + full_branch_score + partial_branch_score
        self.brief = lazy_gettext(
            '%(stmt).2f%% statements covered (%(stmt_score).2f pts), '
            '%(branch).2f%% branches fully covered (%(branch_score).2f pts) '
            'and '
            '%(partial).2f%% partially covered (%(partial_score).2f pts).',
            stmt=self.stmt_cover,
            branch=self.branch_cover,
            partial=self.branch_partial,
            stmt_score=stmt_score,
            branch_score=full_branch_score,
            partial_score=partial_branch_score,
        )

    @staticmethod
    def FromHandinDir(files_to_cover, test_pattern='test_.*\\.py$',
                      stmt_weight=0.5, branch_weight=0.5):
        """Create a `CoverageScorer` to get score for all unit tests provided
        by students according to the coverage of files in `files_to_cover`.

        Only the files matching `test_pattern` will be regarded as unit test
        file.
        """

        p = re.compile(test_pattern)
        test_modules = []
        for f in dirtree('.'):
            fpath, fext = os.path.splitext(f)
            if fext.lower() == '.py' and p.match(f):
                test_modules.append(fpath.replace('/', '.'))

        suite = lambda: unittest.TestLoader().loadTestsFromNames(test_modules)
        return CoverageScorer(
            suite=suite,
            filelist=files_to_cover,
            stmt_weight=stmt_weight,
            branch_weight=branch_weight,
        )


class InputDataScorer(Scorer):
    """Scorer to the input data for BlackBox testing."""

    def __init__(self, name, schema, csvdata, check_classes=None):
        """Construct a new `InputClassScorer` on given `csvdata`, checked by
        rules defined in `check_classes`."""

        super(InputDataScorer, self).__init__(name)

        self.schema = schema
        self.csvdata = csvdata
        self.check_classes = check_classes or []

    def empty(self):
        """Whether this scorer does not contain rules?"""
        return not self.check_classes

    def getDescription(self, check_class):
        """Get the description for given `check_class`."""

        if hasattr(check_class, 'description'):
            return getattr(check_class, 'description')
        if hasattr(check_class, '__name__'):
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
                '%(rate).2f%% rules (%(cover)s out of %(total)s) covered',
                cover=len(covered), total=len(self.check_classes),
                rate=self.score
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


class InputClassScorer(InputDataScorer):

    def __init__(self, schema, csvdata, check_classes=None):
        super(InputClassScorer, self).__init__(
            name=lazy_gettext('InputClass Scorer'),
            schema=schema,
            csvdata=csvdata,
            check_classes=check_classes,
        )


class BoundaryValueScorer(InputDataScorer):

    def __init__(self, schema, csvdata, check_classes=None):
        super(BoundaryValueScorer, self).__init__(
            name=lazy_gettext('BoundaryValue Scorer'),
            schema=schema,
            csvdata=csvdata,
            check_classes=check_classes,
        )


class BlackBoxScorerMaker(object):

    def __init__(self, schema, csvdata, input_class_weight=0.6,
                 boundary_value_weight=0.4):
        csvdata = list(csvdata)
        self._input_class = InputClassScorer(schema, csvdata)
        self._boundary_value = BoundaryValueScorer(schema, csvdata)
        self.input_class_weight = input_class_weight
        self.boundary_value_weight = boundary_value_weight

    def class_(self, description):
        """Define an input class rule."""
        return self._input_class.rule(description)

    def boundary(self, description):
        """Define a boundary value rule."""
        return self._boundary_value.rule(description)

    def get_scorers(self, weight=1.0):
        """Get the list of contained scorers."""
        ret = []
        if not self._input_class.empty():
            ret.append(
                (self._input_class, self.input_class_weight * weight)
            )
        if not self._boundary_value.empty():
            ret.append(
                (self._boundary_value, self.boundary_value_weight * weight)
            )
        return ret


class ObjSchemaScorer(Scorer):
    """Scorer of object structure."""

    def __init__(self, schema):
        """Construct a new `ObjSchemaScorer` for given `schema`."""
        super(ObjSchemaScorer, self) .__init__(
            lazy_gettext('Object Structure Scorer')
        )
        self.schema = schema

    def _run(self):
        try:
            collector = SchemaResultCollector()
            self.schema.check(collector)
            self.score = 100.0 * (collector.total - collector.error) / float(
                collector.total)
            self.brief = lazy_gettext(
                '%(rate).2f%% check points (%(success)d out of %(total)d) '
                'passed',
                rate=self.score,
                total=collector.total,
                success=collector.total - collector.error,
            )
            self.detail = collector.errors
        except:
            raise
            raise ScorerFailure(
                brief=lazy_gettext(
                    'Object Structure Scorer exited with error.'),
                detail=[]
            )
