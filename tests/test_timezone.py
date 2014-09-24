#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: tests/test_timezone.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import unittest
from datetime import datetime

from pytz import UTC, timezone


class PytzBehaviourTestCase(unittest.TestCase):
    """Test the behaviour of pytz module to make sure whether our code
    can run properly.
    """

    def test_localize(self):
        dt = datetime(1992, 10, 30, 12, 0, 0, 0, tzinfo=None)
        # plain to UTC
        dt2 = UTC.localize(dt)
        self.assertEqual(
            (dt2.month, dt2.day, dt2.hour, dt2.minute), (10, 30, 12, 0))
        # plain to Shanghai
        tz = timezone('Asia/Shanghai')
        dt3 = tz.localize(dt)
        self.assertEqual(
            (dt3.month, dt3.day, dt3.hour, dt3.minute), (10, 30, 12, 0))
        # UTC to Shanghai
        dt4 = dt2.astimezone(tz)
        self.assertEqual(
            (dt4.month, dt4.day, dt4.hour, dt4.minute), (10, 30, 20, 0))
        # Shanghai to UTC
        dt5 = dt3.astimezone(UTC)
        self.assertEqual(
            (dt5.month, dt5.day, dt5.hour, dt5.minute), (10, 30, 4, 0))

    def test_normalize(self):
        dt = datetime.utcfromtimestamp(1143408899)
        tz = timezone('Australia/Sydney')
        # plain to Sydney normalized
        dt3 = tz.normalize(tz.localize(dt))
        self.assertEqual(
            (dt3.month, dt3.day, dt3.hour, dt3.minute), (3, 26, 21, 34))
