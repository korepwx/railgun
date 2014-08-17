#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/runner/errors.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

from railgun.common.lazy_i18n import lazy_gettext


class RunnerError(Exception):
    """Errors that carries an error report."""

    def __init__(self, message):
        super(RunnerError, self).__init__(message)
        self.message = message


class InternalServerError(RunnerError):
    """Error indicating that server meets some trouble."""

    def __init__(self):
        super(RunnerError, self).__init__(lazy_gettext(
            'Internal server error.'
        ))


class LanguageNotSupportError(RunnerError):
    """Error indicating that the handin requires a not supported language."""

    def __init__(self, lang):
        super(RunnerError, self).__init__(lazy_gettext(
            'Language "%(lang)s" is not provided.',
            lang=lang
        ))


class BadArchiveError(RunnerError):
    """Error indicating that the handin of a student is bad archive."""

    def __init__(self):
        super(RunnerError, self).__init__(lazy_gettext(
            'Your submission is not a valid archive file.'
        ))


class FileDenyError(RunnerError):
    """Error indicating that the handin contains a denied file."""

    def __init__(self, fname):
        super(RunnerError, self).__init__(lazy_gettext(
            'Archive contains denied file %(filename)s.',
            filename=fname
        ))


class RunnerTimeout(RunnerError):
    """Error indicating that the handin has run out of time."""

    def __init__(self):
        super(RunnerError, self).__init__(lazy_gettext(
            'Your submission has run out of time.'
        ))


class NonUTF8OutputError(RunnerError):
    """Error indicating that the handin produced non UTF-8 output."""

    def __init__(self):
        super(RunnerError, self).__init__(lazy_gettext(
            'Not valid UTF-8 sequence produced.'
        ))
