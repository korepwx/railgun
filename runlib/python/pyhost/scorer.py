#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: runlib/python/pyhost/scorer.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

"""This module provides all the types of :class:`Scorer` classes.

A :class:`Scorer` is specialized to evaluate one aspect of the submission
data.  Each homework assignment provides the script to create and glue
one or more scorers toegether, to give the final score of a submission.

You may refer to :class:`~railgun.common.hw.HwScore` to see how scores
from multiple scorers are composed up.  Also, you may refer to
:ref:`hwpython` to check the usage of all Python scorers.
"""

import re
import os
from time import time
from functools import wraps

import pep8
import unittest
from coverage import coverage

from railgun.common.fileutil import dirtree
from railgun.common.lazy_i18n import lazy_gettext
from railgun.common.csvdata import CsvSchema
from .errors import ScorerFailure
from .utility import UnitTestScorerDetailResult, Pep8DetailReport
from .objschema import SchemaResultCollector


def load_suite(suite):
    """If the given testing suite is a :func:`callable` object and is not
    a :class:`~unittest.suite.TestSuite`, execute this method as if is a
    lazy loader to generate the testing suite.

    :param suite: A testing suite or a lazy loader.
    """
    if callable(suite) and \
            not isinstance(suite, unittest.suite.TestSuite):
        suite = suite()
    return suite


class Scorer(object):
    """The base class for all scorer types.

    :param name: The translated name of this scorer.
    :type name: :class:`~railgun.common.lazy_i18n.GetTextString`
    """

    def __init__(self, name):
        #: Store the translated name of this scorer.
        #: This name will be displayed to the students in detailed submission
        #: report.
        self.name = name
        #: The time consumed by this scorer.
        #: This attribute may keep :data:`None` if the scorer fails to run.
        self.time = None
        #: The final score given by this scorer.
        #:
        #: Derived class should set this attribute in :meth:`do_run` to give
        #: the score (where the value should fall in the range [0, 100]).
        self.score = None
        #: The brief explanation of the score, a translated string.
        #: (:class:`~railgun.common.lazy_i18n.GetTextString`)
        self.brief = None
        #: Detailed explanation of the score, a list of translated strings.
        #: You may initialize the list yourself in :meth:`do_run`.
        #: (:class:`list` of :class:`~railgun.common.lazy_i18n.GetTextString`)
        self.detail = None

    def do_run(self):
        """Derived classes should implement this to do actual evaluations."""
        raise NotImplementedError()

    def run(self):
        """Run the evaluation and give the :attr:`score`.

        If a :class:`~pyhost.errors.ScorerFailure` is raised, the score and
        explanation carried by the error will be copied into this scorer,
        as the final result.

        Other exceptions are not catched by this method.  We may just leave
        those errors not processed, so that the runner host will exit with
        a non-zero exit code, which will force the submission to be rejected.
        """
        try:
            startTime = time()
            self.do_run()
            self.time = time() - startTime
        except ScorerFailure, ex:
            self.brief = ex.brief
            self.detail = ex.detail
            self.score = ex.score


class UnitTestScorer(Scorer):
    """The scorer to give score according to a unit testing.

    Suppose the student has submitted some code, and we want to evaluate
    the functionality of the code.  We can provide our testing suite in
    the homework evaluation script, expecting the student code to pass
    these tests.

    Then we may feed the testing suite into :class:`UnitTestScorer`.
    This scorer will run all the testing cases, and give the score
    according to the amount of passing cases.

    :param suite: A :class:`~unittest.suite.TestSuite` or a lazy loader
        to generate the :class:`~unittest.suite.TestSuite` object.
    """

    def __init__(self, suite):
        super(UnitTestScorer, self).__init__(
            lazy_gettext('Functionality Scorer'))

        #: Store the testing suite. If it is a :func:`callable` object but not
        #: a #: :class:`~unittest.suite.TestSuite`, execute it to get the real
        #: testing suite.  Keep the :attr:`suite` lazy can prevent the scorer
        #: from exploits.
        self.suite = suite

    def do_run(self):
        self.suite = load_suite(self.suite)
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
        """Create a new :class:`UnitTestScorer` on the testing case class.
        This method makes a lazy loader so that the testing case object will
        not be constructed until :meth:`do_run` is called.

        :param testcase: A class derived from :class:`unittest.TestCase`.
        """
        return UnitTestScorer(
            lambda: unittest.TestLoader().loadTestsFromTestCase(testcase))

    @staticmethod
    def FromNames(names):
        """Create a new :class:`UnitTestScorer` on the given names.
        The testing cases specified by `names` will not be loaded until
        :meth:`do_run` is called.

        :param names: A sequence of object names that can be resolved
            into a :class:`unittest.suite.TestSuite`.
        :type names: :class:`list` of :class:`str`
        """
        suite = lambda: unittest.TestLoader().loadTestsFromNames(names)
        return UnitTestScorer(suite)

    @staticmethod
    def FromHandinDir(test_pattern='test_.*\\.py$'):
        """Create a new :class:`UnitTestScorer` on the given files.
        The :class:`unittest.suite.TestSuite` objects will be discovered
        and loaded from the files matching the given pattern when
        :meth:`do_run` is called.

        :param test_pattern: The regex pattern of file names.
        :type test_pattern: :class:`str`
        """

        p = re.compile(test_pattern)
        test_modules = []
        for f in dirtree('.'):
            fpath, fext = os.path.splitext(f)
            if fext.lower() == '.py' and p.match(f):
                test_modules.append(fpath.replace('/', '.'))

        suite = lambda: unittest.TestLoader().loadTestsFromNames(test_modules)
        return UnitTestScorer(suite=suite)


class CodeStyleScorer(Scorer):
    """The scorer to give a score according to the coding style.

    The most well-known coding style in Python world is probably `pep8`.
    This scorer will evaluate the student code with pep8.py, and will
    decrease `errcost` from the score for each warning.  The minimum
    score will be 0.

    :param filelist: Iterable names of files that should be checked.
    :param skipfile: A :func:`callable` object to filter the `filelist`.
        We only leave the names where `skipfile(name)` returns :data:`False`.
    :param errcost: The cost of each coding style error.
    """

    def __init__(self, filelist, skipfile=None, errcost=10.0):

        super(CodeStyleScorer, self).__init__(lazy_gettext('CodeStyle Scorer'))
        skipfile = skipfile or (lambda path: False)
        is_pyfile = lambda p: (p[-3:].lower() == '.py')
        self.filelist = [p for p in filelist
                         if not skipfile(p) and is_pyfile(p)]
        self.errcost = errcost

    def do_run(self):
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
        """Create a new :class:`CodeStyleScorer` for all files under the
        submission working directory unless they belong to `ignore_files`.

        :param ignore_files: A collection of file names to be ignored.
        """

        ignore_files = ignore_files or []
        if (isinstance(ignore_files, str) or
                isinstance(ignore_files, unicode)):
            ignore_files = [ignore_files]
        return CodeStyleScorer(dirtree('.'), (lambda p: p in ignore_files))


class CoverageScorer(Scorer):
    """The scorer to give score according to the coverage rate.

    The coverage rate is a very important score when it comes to unit
    testing.  We may provide a module, tell the students to write unit
    testing code, and give them score according to the coverage rate
    of their testing code on our module.

    This scorer measures two types of coverage rate: the statement
    coverage rate and the branch coverage rate.  Each type of coverage
    rate will result in a score, and the final score will be composed
    up according to :attr:`stmt_weight` and :attr:`branch_weight`.

    :param suite: A :class:`~unittest.suite.TestSuite` or a lazy loader
        to generate the :class:`~unittest.suite.TestSuite` object.
    :param filelist: Iterable names of files that should be tested
        by the students.  The coverage rate will be measured on these
        files.
    :param stmt_weight: The weight of statement coverage rate.
    :type stmt_weight: :class:`float`
    :param branch_weight: The weight of branch coverage rate.
    :type branch_weight: :class:`float`
    """

    def __init__(self, suite, filelist, stmt_weight=0.5, branch_weight=0.5):
        super(CoverageScorer, self).__init__(lazy_gettext('Coverage Scorer'))

        self.suite = suite
        self.brief = []
        self.filelist = list(filelist)
        self.stmt_weight = stmt_weight
        self.branch_weight = branch_weight

    def do_run(self):
        def safe_divide(a, b, default=1.0):
            if b > 0:
                return float(a) / float(b)
            return default

        cov = coverage(branch=True)
        cov.start()
        self.suite = load_suite(self.suite)

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
        """Create a new :class:`CoverageScorer`.

        The files for the students to test is provided in `files_to_cover`,
        and the file name patterns of unit testing code is defined in
        `test_pattern`.
        The `stmt_weight` and the `branch_weight` may also be specified.

        :param files_to_cover: List of files to measure the coverage rate on.
        :type files_to_cover: :class:`list` of :class:`str`
        :param test_pattern: The regex pattern of testing code file names.
        :type test_pattern: :class:`str`
        :param stmt_weight: The weight of statement coverage rate.
        :type stmt_weight: :class:`float`
        :param branch_weight: The weight of branch coverage rate.
        :type branch_weight: :class:`float`
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
    """The base class for input data scorers.

    Input data scorers are mainly used in BlackBox testing homework.
    The students may provide some structured data in CSV format,
    and we want to check whether the data covers all the equivalent
    classes and boundary values.

    To achieve that goal, I introduced :class:`InputDataScorer`.
    It can takes a set of methods as `condition` validators, where
    each methods only returns :data:`True` on a certain class of
    input data or boundary value.

    Then the student submitted data will be checked by all the
    `condition` validators one row after another.  The scorer will
    count the number of validators who have ever reported :data:`True`,
    and give the score according to that portion.

    :param name: The name of this scorer, should be set by derived classes.
    :type name: :class:`~railgun.common.lazy_i18n.GetTestString`
    :param schema: The schema for this scorer to parse csv data.
    :type schema: :class:`~railgun.common.csvdata.CsvSchema`
    :param csvdata: Iterable object over :class:`str`, each representing a
        row in the csv data.  Usually a :class:`file` object.
    :type csvdata: :class:`object`
    :param check_classes: The initial list of input data validators.
    :type check_classes: :class:`list` of :func:`callable` objects
    """

    def __init__(self, name, schema, csvdata, check_classes=None):
        """Construct a new `InputClassScorer` on given `csvdata`, checked by
        rules defined in `check_classes`."""

        super(InputDataScorer, self).__init__(name)

        #: Store the :class:`~railgun.common.csvdata.CsvSchema`.
        self.schema = schema
        #: Rows of csv data.
        self.csvdata = csvdata
        #: The input data validators.
        self.check_classes = check_classes or []

    def empty(self):
        """Whether or not this scorer has no input data validator?"""
        return not self.check_classes

    def getDescription(self, check_class):
        """Get the description for given validator.

        The `description` attribute of the given validator, or `__name__`
        if `description` doesn't exist, or the string representation of the
        given validator if `__name__` doesn't exist either.

        :param check_class: The :func:`callable` data validator.
        :return: The description of given validator.
        """

        if hasattr(check_class, 'description'):
            return getattr(check_class, 'description')
        if hasattr(check_class, '__name__'):
            return getattr(check_class, '__name__')
        return str(check_class)

    def rule(self, description):
        """Make a decorator to :func:`callable` objects which will add
        `description` attribute to the given method, and will add that
        method to :attr:`check_classes`.

        Usage::

            @scorer.rule('a >= 1 and b <= 2')
            def a_must_not_less_than_1_and_b_must_not_greater_than_2(a, b):
                return a >= 1 and b <= 2

        .. note::

            If the check method raises any exception, this rule will be
            regarded as `not matched`.  This design purpose is to ease
            the rules like `matching a string that can be converted into
            int`.

        :return: The decorator.
        """
        def outer(method):
            @wraps(method)
            def inner(*args, **kwargs):
                try:
                    return method(*args, **kwargs)
                except Exception:
                    return False

            setattr(inner, 'description', description)
            self.check_classes.append(inner)
            return method

        return outer

    def do_run(self):
        # First, load the data, and format the error message if schema
        # is not matched.
        try:
            loaded_data = list(CsvSchema.LoadCSV(self.schema, self.csvdata))
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
        # Next, check the loaded data
        self.detail = []
        covered = set()
        for obj in loaded_data:
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


class InputClassScorer(InputDataScorer):
    """A :class:`InputDataScorer` called `InputClass Scorer`.
    This class distinguishes from :class:`BoundaryValueScorer` only on the
    name.
    """

    def __init__(self, schema, csvdata, check_classes=None):
        super(InputClassScorer, self).__init__(
            name=lazy_gettext('InputClass Scorer'),
            schema=schema,
            csvdata=csvdata,
            check_classes=check_classes,
        )


class BoundaryValueScorer(InputDataScorer):
    """A :class:`InputDataScorer` called `BoundaryValue Scorer`.
    This class distinguishes from :class:`InputClassScorer` only on the
    name.
    """

    def __init__(self, schema, csvdata, check_classes=None):
        super(BoundaryValueScorer, self).__init__(
            name=lazy_gettext('BoundaryValue Scorer'),
            schema=schema,
            csvdata=csvdata,
            check_classes=check_classes,
        )


class BlackBoxScorerMaker(object):
    """A factory to create both :class:`InputClassScorer` and
    :class:`BoundaryValueScorer`.
    You may refer to :ref:`hwinput` for examples.

    :param schema: The schema for this scorer to parse csv data.
    :type schema: :class:`~railgun.common.csvdata.CsvSchema`
    :param csvdata: Iterable object over :class:`str`, each representing a
        row in the csv data.  Usually a :class:`file` object.
    :type csvdata: :class:`object`
    :param input_class_weight: The weight for :class:`InputClassScorer`.
    :type input_class_weight: :class:`float`
    :param boundary_value_weight: The weight for :class:`BoundaryValueScorer`.
    :type boundary_value_weight: :class:`float`
    """

    def __init__(self, schema, csvdata, input_class_weight=0.6,
                 boundary_value_weight=0.4):
        csvdata = list(csvdata)
        self._input_class = InputClassScorer(schema, csvdata)
        self._boundary_value = BoundaryValueScorer(schema, csvdata)
        self.input_class_weight = input_class_weight
        self.boundary_value_weight = boundary_value_weight

    def class_(self, description):
        """Get the decorator to a :class:`InputClassScorer` validator."""
        return self._input_class.rule(description)

    def boundary(self, description):
        """Get the decorator to a :class:`BoundaryValueScorer` validator."""
        return self._boundary_value.rule(description)

    def get_scorers(self, weight=1.0):
        """Get the :class:`list` of :class:`InputClassScorer` and
        :class:`BoundaryValueScorer` which can be appended to scorer list
        and fed into `SafeRunner.run`.

        :param weight: The total weight of two scorers.
        :type weight: :class:`float`
        :return: [(:class:`Scorer`, weight), ...].
        """
        ret = []

        # Get the real weight of two scorers
        weights = [self.input_class_weight, self.boundary_value_weight]
        if self._input_class.empty():
            weights[1] = 1.0
        if self._boundary_value.empty():
            weights[0] = 1.0

        # Then add the available scorers into return list
        if not self._input_class.empty():
            ret.append(
                (self._input_class, weight * weights[0])
            )
        if not self._boundary_value.empty():
            ret.append(
                (self._boundary_value, weight * weights[1])
            )
        return ret


class ObjSchemaScorer(Scorer):
    """In unit testing homework, we want the students to organize their
    testing code in the exact way we tell them.  So we need to validate
    the structure of objects.
    :class:`ObjSchemaScorer` can parse object structure and give the score.

    :param schema: A collection of object structure validators.
    :type schema: :class:`~railgun.runner.objschema.RootSchema`
    """

    def __init__(self, schema):
        super(ObjSchemaScorer, self) .__init__(
            lazy_gettext('Object Structure Scorer')
        )
        self.schema = schema

    def do_run(self):
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
            # Why do we catch all exceptions, not the exceptions derived
            # from :class:`Exception` here?  Because :class:`ObjSchemaScorer`
            # is usually considered not a `harmful` scorer, and the error
            # messages may not be hidden to the students.
            #
            # If we do not catch all the exceptions, then the student
            # may submit a code that `raises` something, where the evaluation
            # script may be revealed.
            raise ScorerFailure(
                brief=lazy_gettext(
                    'Object Structure Scorer exited with error.'),
                detail=[]
            )
