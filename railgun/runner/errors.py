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
    """Error indicating that server meets some trouble."""

    def __init__(self):
        super(RunnerError, self).__init__(gettext_lazy(
            'Internal server error.'
        ))


class LanguageNotSupportError(RunnerError):
    """Error indicating that the handin requires a not supported language."""

    def __init__(self, lang):
        super(RunnerError, self).__init__(gettext_lazy(
            'Language "%(lang)s" is not supported by this homework.',
            lang=lang
        ))


class BadArchiveError(RunnerError):
    """Error indicating that the handin of a student is bad archive."""

    def __init__(self):
        super(RunnerError, self).__init__(gettext_lazy(
            'Your handin is not a valid archive file.'
        ))


class FileDenyError(RunnerError):
    """Error indicating that the handin contains a denied file."""

    def __init__(self, fname):
        super(RunnerError, self).__init__(gettext_lazy(
            'Archive contains denied file %(filename)s.',
            filename=fname
        ))


class RunnerTimeout(RunnerError):
    """Error indicating that the handin has run out of time."""

    def __init__(self):
        super(RunnerError, self).__init__(gettext_lazy(
            'Your handin has run out of time.'
        ))
