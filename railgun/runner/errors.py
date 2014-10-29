#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/runner/errors.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

"""This module provides the pre-defined errors that holds the messages
to describe what errors a submission produces.
"""

from railgun.common.lazy_i18n import lazy_gettext


class RunnerError(Exception):
    """The base class for all submission errors.

    :param message: The translated error message.  Usually set by
        derived classes in the contructor.
    :type message: :class:`~railgun.common.lazy_i18n.GetTextString`
    :param compiler_error: The compiler error of this submission.
        Compiler error is not part of :class:`~railgun.common.hw.HwScore`,
        not can it be reported to server via :ref:`design_webapi`.
    :type compiler_error: :class:`~railgun.common.lazy_i18n.GetTextString`
    """

    def __init__(self, message, compile_error=None):
        super(RunnerError, self).__init__(message)
        self.message = message
        self.compile_error = compile_error


class InternalServerError(RunnerError):
    """The server has come across some technique error.

    Since :func:`~railgun.runner.tasks.run_handin` is wrapped with a large
    `try-catch`, all the un-expected errors can be catched.  This error
    is then generated and reported to user.
    """

    def __init__(self, **kwargs):
        super(InternalServerError, self).__init__(lazy_gettext(
            'Internal server error.'
        ), **kwargs)


class RunnerPermissionError(RunnerError):
    """The file permission of runner is not configured correctly.

    The runner will check the file system permissions to guarantee
    that the execution environment is safe if ``runconfig.RUNNER_CHECK_PERM``
    is set to :data:`True`.
    If the validation does not pass, all the new submissions will be
    rejected with this error.
    """

    def __init__(self, **kwargs):
        super(RunnerPermissionError, self).__init__(lazy_gettext(
            'File permissions of the runner is wrong.'
        ), **kwargs)


class SpawnProcessFailure(RunnerError):
    """The external process cannot be launched to run the submission.
    This is often due to a false configuration of the runner hosts."""

    def __init__(self, **kwargs):
        super(SpawnProcessFailure, self).__init__(lazy_gettext(
            "Couldn't start submitted program."
        ), **kwargs)


class RuntimeFileCopyFailure(RunnerError):
    """The system cannot copy runtime files into working directory.
    You may refer to :meth:`~railgun.runner.host.BaseHost.prepare_hwcode`
    of :class:`~railgun.runner.host.BaseHost` to see more details.
    """

    def __init__(self, **kwargs):
        super(RuntimeFileCopyFailure, self).__init__(lazy_gettext(
            "Couldn't copy runtime files, please contact TA."
        ), **kwargs)


class ExtractFileFailure(RunnerError):
    """The system cannot extract submission archive into working directory.
    You may refer to :meth:`~railgun.runner.host.BaseHost.extract_handin`
    of :class:`~railgun.runner.host.BaseHost` to see more details.
    """

    def __init__(self, **kwargs):
        super(ExtractFileFailure, self).__init__(lazy_gettext(
            "Couldn't extract your archive file."
        ), **kwargs)


class ArchiveContainTooManyFileError(RunnerError):
    """The submission archive contains too many files.
    You may refer to :meth:`~railgun.runner.host.BaseHost.extract_handin`
    of :class:`~railgun.runner.host.BaseHost` to see more details.
    """

    def __init__(self, **kwargs):
        super(ArchiveContainTooManyFileError, self).__init__(lazy_gettext(
            "Archive contains too many files."
        ), **kwargs)


class LanguageNotSupportError(RunnerError):
    """The submission language doesn't belong to corresponding homework.

    :param lang: The provided programming language.
    :type lang: :class:`str`
    """

    def __init__(self, lang, **kwargs):
        super(LanguageNotSupportError, self).__init__(lazy_gettext(
            'Language "%(lang)s" is not provided.',
            lang=lang
        ), **kwargs)


class BadArchiveError(RunnerError):
    """The submitted archive file is in bad format.
    This error may also be raised if the user uploads an archive file with
    wrong extension in file name.
    """

    def __init__(self, **kwargs):
        super(BadArchiveError, self).__init__(lazy_gettext(
            'Your submission is not a valid archive file.'
        ), **kwargs)


class FileDenyError(RunnerError):
    """There exist some entity that is denied by `hw.xml` or `code.xml` in
    the submitted archive file.

    :param fname: The name of the denied entity.
    :type fname: :class:`str`
    """

    def __init__(self, fname, **kwargs):
        super(FileDenyError, self).__init__(lazy_gettext(
            'Archive contains denied file %(filename)s.',
            filename=fname
        ), **kwargs)


class RunnerTimeout(RunnerError):
    """The submission runs out of time."""

    def __init__(self, **kwargs):
        super(RunnerTimeout, self).__init__(lazy_gettext(
            'Your submission has run out of time.'
        ), **kwargs)


class NonUTF8OutputError(RunnerError):
    """The runner host produces invalid UTF-8 sequence.
    You should tell the students to encode their source code in UTF-8.
    """

    def __init__(self, **kwargs):
        super(NonUTF8OutputError, self).__init__(lazy_gettext(
            'Not valid UTF-8 sequence produced.'
        ), **kwargs)


class NetApiAddressRejected(RunnerError):
    """The URL address submitted by user is rejected by regex patterns
    defined in `code.xml`.
    You may refer to :meth:`~railgun.runner.host.NetApiHost.compile`
    of :class:`~railgun.runner.host.NetApiHost` to see more details.
    """

    def __init__(self, **kwargs):
        super(NetApiAddressRejected, self).__init__(lazy_gettext(
            'Given address is rejected.'
        ), **kwargs)
