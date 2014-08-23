#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: hw/chkpath/code/python/run.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import unittest
from pyhost.scorer import UnitTestScorer, CodeStyleScorer
import SafeRunner


class ReformPathTestCase(unittest.TestCase):

    def _reform_path(self, s):
        # NOTE: any modules upload by student should only be loaded until the
        #       test is actually called. This is because the test runner will
        #       guarded by C module instead of Python, so that the result
        #       reporter will be prevent from injection.
        from path import reform_path
        return reform_path(s)

    def test_translateWinPathSep(self):
        self.assertEqual(self._reform_path('1\\2'), '1/2')
        self.assertEqual(self._reform_path('\\1\\2'), '/1/2')
        self.assertEqual(self._reform_path('\\\\1\\\\2'), '/1/2')

    def test_continousSlash(self):
        self.assertEqual(self._reform_path('1//2'), '1/2')
        self.assertEqual(self._reform_path('//1//2'), '/1/2')
        self.assertEqual(self._reform_path('////1////2'), '/1/2')

    def test_removeSingleDots(self):
        self.assertEqual(self._reform_path('1/./2'), '1/2')
        self.assertEqual(self._reform_path('./1/./2'), '1/2')
        self.assertEqual(self._reform_path('1/./2/.'), '1/2')
        self.assertEqual(self._reform_path('/1/./2'), '/1/2')
        self.assertEqual(self._reform_path('/./1/./2'), '/1/2')
        self.assertEqual(self._reform_path('/1/./2/./.'), '/1/2')

    def test_removeDoubleDots(self):
        self.assertEqual(self._reform_path('1/../2'), '2')
        self.assertEqual(self._reform_path('/1/../2'), '/2')
        self.assertEqual(self._reform_path('/1/2/3/../4/../..'), '/1')
        self.assertRaises(ValueError, self._reform_path, '..')
        self.assertRaises(ValueError, self._reform_path, '/..')
        self.assertRaises(ValueError, self._reform_path, '1/../..')
        self.assertRaises(ValueError, self._reform_path, '/1/../..')

    def test_emptyPath(self):
        self.assertEqual(self._reform_path(''), '')
        self.assertEqual(self._reform_path('/'), '/')
        self.assertEqual(self._reform_path('.'), '')
        self.assertEqual(self._reform_path('/.'), '/')
        self.assertEqual(self._reform_path('1/..'), '')
        self.assertEqual(self._reform_path('1/../'), '')
        self.assertEqual(self._reform_path('/1/..'), '/')
        self.assertEqual(self._reform_path('/1/../'), '/')

    def test_tailSlash(self):
        self.assertEqual(self._reform_path('\\1\\2\\'), '/1/2')
        self.assertEqual(self._reform_path('//1//2//'), '/1/2')
        self.assertEqual(self._reform_path('1/./2/./'), '1/2')
        self.assertEqual(self._reform_path('/1/./2/./'), '/1/2')
        self.assertEqual(self._reform_path('1/2/3/../4/../../'), '1')
        self.assertEqual(self._reform_path('/1/2/3/../4/../../'), '/1')
        self.assertRaises(ValueError, self._reform_path, '../')
        self.assertRaises(ValueError, self._reform_path, '/../')
        self.assertRaises(ValueError, self._reform_path, '1/../../')
        self.assertRaises(ValueError, self._reform_path, '/1/../../')

if (__name__ == '__main__'):
    scorers = [
        (CodeStyleScorer.FromHandinDir(ignore_files=['run.py']), 0.1),
        (UnitTestScorer.FromTestCase(ReformPathTestCase), 0.9),
    ]
    SafeRunner.run(scorers)
