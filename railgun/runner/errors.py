#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/runner/errors.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

from railgun.common.lazy_i18n import lazy_gettext


class RunnerError(Exception):
    """Errors that carries an error report."""

    def __init__(self, message, compile_error=None):
        super(RunnerError, self).__init__(message)
        self.message = message
        self.compile_error = compile_error


class InternalServerError(RunnerError):
    """Error indicating that server meets some trouble."""

    def __init__(self, **kwargs):
        super(InternalServerError, self).__init__(lazy_gettext(
            'Internal server error.'
        ), **kwargs)


class RunnerPermissionError(RunnerError):
    """Error indicating that runner host is not configured properly."""

    def __init__(self, **kwargs):
        super(RunnerPermissionError, self).__init__(lazy_gettext(
            'Runner file permissions wrong, contact TA.'
        ), **kwargs)


class SpawnProcessFailure(RunnerError):
    """Error indicating that the external process cannot start."""

    def __init__(self, **kwargs):
        super(SpawnProcessFailure, self).__init__(lazy_gettext(
            "Couldn't start submitted program."
        ), **kwargs)


class RuntimeFileCopyFailure(RunnerError):
    """Error indicating that the runtime files could not be setup."""

    def __init__(self, **kwargs):
        super(RuntimeFileCopyFailure, self).__init__(lazy_gettext(
            "Couldn't copy runtime files, please contact TA."
        ), **kwargs)


class ExtractFileFailure(RunnerError):
    """Error indicating that the archive file could not be extracted."""

    def __init__(self, **kwargs):
        super(ExtractFileFailure, self).__init__(lazy_gettext(
            "Couldn't extract your archive file."
        ), **kwargs)


class ArchiveContainTooManyFileError(RunnerError):
    """Error indicating that the archive file contains too many entities."""

    def __init__(self, **kwargs):
        super(ArchiveContainTooManyFileError, self).__init__(lazy_gettext(
            "Archive contains too many files."
        ), **kwargs)


class LanguageNotSupportError(RunnerError):
    """Error indicating that the handin requires a not supported language."""

    def __init__(self, lang, **kwargs):
        super(LanguageNotSupportError, self).__init__(lazy_gettext(
            'Language "%(lang)s" is not provided.',
            lang=lang
        ), **kwargs)


class BadArchiveError(RunnerError):
    """Error indicating that the handin of a student is bad archive."""

    def __init__(self, **kwargs):
        super(BadArchiveError, self).__init__(lazy_gettext(
            'Your submission is not a valid archive file.'
        ), **kwargs)


class FileDenyError(RunnerError):
    """Error indicating that the handin contains a denied file."""

    def __init__(self, fname, **kwargs):
        super(FileDenyError, self).__init__(lazy_gettext(
            'Archive contains denied file %(filename)s.',
            filename=fname
        ), **kwargs)


class RunnerTimeout(RunnerError):
    """Error indicating that the handin has run out of time."""

    def __init__(self, **kwargs):
        super(RunnerTimeout, self).__init__(lazy_gettext(
            'Your submission has run out of time.'
        ), **kwargs)


class NonUTF8OutputError(RunnerError):
    """Error indicating that the handin produced non UTF-8 output."""

    def __init__(self, **kwargs):
        super(NonUTF8OutputError, self).__init__(lazy_gettext(
            'Not valid UTF-8 sequence produced.'
        ), **kwargs)


class NetApiAddressRejected(RunnerError):
    """Error indicating that the URL address in a NetAPI handin is invalid."""

    def __init__(self, **kwargs):
        super(NetApiAddressRejected, self).__init__(lazy_gettext(
            'Given address is rejected.'
        ), **kwargs)
