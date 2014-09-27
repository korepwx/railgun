#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/runner/permcheck.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

"""
This module has the utility to check runner host file permissions.
"""

from railgun.maintain.permissions import RunnerPermissionCheckTask


class GlobalChecker(object):

    def __init__(self, logger):
        self.errcount = 0
        self.message = None
        self.logger = logger

    def execute(self):
        checker = RunnerPermissionCheckTask()
        checker.logger = self.logger
        checker.execute()
        self.errcount = checker.errcount

    def has_error(self):
        return self.errcount > 0

checker = GlobalChecker()
