#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/runner/errors.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

from railgun.common.lazy_i18n import gettext_lazy


class RunnerError(Exception):
    """Errors that carries an error report."""

    def __init__(self, message):
        super(RunnerError, self).__init__(message)
        self.message = message


class InternalServerError(RunnerError):
    """Error that indicate that server meets some trouble."""

    def __init__(self):
        super(RunnerError, self).__init__(gettext_lazy(
            'Internal server error, please upload your handin again.'
        ))


class InvalidHandinError(RunnerError):
    """Error that indicate the handin of a student is invalid."""
