#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: tests/sample_test.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import unittest
from sample import sample


class SampleTestCase(unittest.TestCase):
    def test_abc(self):
        self.assertEqual(1, sample(1, 2, 3))

    def test_acb(self):
        self.assertEqual(1, sample(1, 3, 2))

    def test_bac(self):
        self.assertEqual(1, sample(2, 1, 3))

    def test_bca(self):
        self.assertEqual(1, sample(2, 3, 1))

    def test_cab(self):
        self.assertEqual(1, sample(3, 1, 2))

    def test_cba(self):
        self.assertEqual(1, sample(3, 2, 1))
