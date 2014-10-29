#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/runner/handin.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

"""This module provides :class:`BaseHandin` as the basic interface of
a submission handler, as well as derived classes targeted to different
submission types.

Submissions may be various in programming languages.  Each programming
language should have a corresponding handler, which decodes the user
uploaded data (for example, extracting the archive files, or parsing
the csv data), and prepares for the runner host.
"""

import os
import base64

from . import runconfig
from .hw import homeworks
from .errors import (InternalServerError, LanguageNotSupportError,
                     ExtractFileFailure)
from .host import PythonHost, NetApiHost, InputClassHost
from railgun.common.fileutil import Extractor


class TempDiskUploadFile(object):
    """Decode base64 file content and save to disk as a temporary file.

    The file will be placed under ``config.TEMPORARY_DIR``.  If you manage
    the :class:`TempDiskUploadFile` via ``with`` statement, then the file
    will be removed automatically.  For example::

        with TempDiskUploadFile(upload, '%s.zip' % uuid) as tempFile:
            os.system('7z x "%s"' % tempeFile.path)

    :param upload: The base64 encoded file content.
    :type upload: :class:`str`
    :param fname: The temporary file name.  If the chosen file name exists,
        it will be overwritten.
    :type fname: :class:`str`
    :param ignore_error: A :class:`bool` indicating whether we should ignore
        system exceptions when we are trying to delete the temporary file?
    :type ignore_error: :class:`bool`
    """

    def __init__(self, upload, fname, ignore_error=False):
        #: Store the full path of this temporary file.
        self.path = os.path.join(runconfig.TEMPORARY_DIR, fname)
        #: The original base64 encoded file content.
        self.upload = upload
        #: Whether we should ignore the system exceptions when we are trying
        #: to delete the temporary file?
        self.ignore_error = ignore_error

    def __enter__(self):
        with open(self.path, 'wb') as f:
            f.write(base64.b64decode(self.upload))
        return self

    def __exit__(self, ignore1, ignore2, ignore3):
        try:
            if os.path.isfile(self.path):
                os.remove(self.path)
        except Exception:
            if not self.ignore_error:
                raise


class BaseHandin(object):
    """The basic interface of a submission handler.

    :param lang: The programming language name of this handler.
        Derived classes should provide this value in contructors.
    :type lang: :class:`str`
    :param handid: The uuid of this submission.
    :type handid: :class:`str`
    :param hwid: The uuid of the homework.
    :type hwid: :class:`str`
    :param upload: The uploaded data of this submission.
        It may be base64 encoded byte sequence to represent an archive file
        in a `Python` submission, or a url address in a `NetAPI` submission.
    :type upload: :class:`str`
    :param options: The extra options of this submission.
        Vary for different types of submissions.
    :type options: :class:`dict`
    """

    def __init__(self, lang, handid, hwid, upload, options):
        #: The programming language of this handler.
        self.lang = lang
        # We require `options` to be a :class:`dict`
        if not isinstance(options, dict):
            raise TypeError("`options` should be dictionary.")
        #: Store the corresponding :class:`~railgun.common.hw.Homework`
        #: to `hwid`.
        self.hw = homeworks.get_by_uuid(hwid)
        if not self.hw:
            raise InternalServerError()
        # We require `lang` to be a valid programming language of this
        # homework.
        if lang not in self.hw.get_code_languages():
            raise LanguageNotSupportError(lang)
        #: The uuid of this submission.
        self.handid = handid
        #: The original uploaded data of this submission.
        self.upload = upload
        #: The extra options of this submission.
        self.options = options

    def execute(self):
        """Run this submission and store the result.  Derived classes should
        at least implement this.

        :return: A :class:`tuple` of (`exitcode`, `stdout`, `stderr`).
        """
        raise NotImplementedError()


class PythonHandin(BaseHandin):
    """Python submission handler, derived from :class:`BaseHandin`.

    :param handid: The uuid of this submission.
    :type handid: :class:`str`
    :param hwid: The uuid of the homework.
    :type hwid: :class:`str`
    :param upload: The base64 encoded archive file content.
    :type upload: :class:`str`
    :param options: {'filename': the original uploaded file name}
    :type options: :class:`dict`
    """

    def __init__(self, handid, hwid, upload, options):
        super(PythonHandin, self).__init__('python', handid, hwid, upload,
                                           options)

    def execute(self):
        with PythonHost(self.handid, self.hw) as host:
            # put uploaded file content onto disk and then open the archive
            # this is because some Extractors may rely on disk files.
            archive_fext = os.path.splitext(self.options['filename'])[1]
            archive_file = '%s%s' % (self.handid, archive_fext)
            with TempDiskUploadFile(self.upload, archive_file) as f:
                try:
                    extractor = Extractor.open(f.path)
                except Exception:
                    raise ExtractFileFailure()
                host.prepare_hwcode()
                host.extract_handin(extractor)
                return host.run()


class NetApiHandin(BaseHandin):
    """NetAPI submission handler, derived from :class:`BaseHandin`.

    :param handid: The uuid of this submission.
    :type handid: :class:`str`
    :param hwid: The uuid of the homework.
    :type hwid: :class:`str`
    :param upload: The submitted url address.
    :type upload: :class:`str`
    :param options: {}
    :type options: :class:`dict`
    """

    def __init__(self, handid, hwid, upload, options):
        super(NetApiHandin, self).__init__('netapi', handid, hwid, upload,
                                           options)
        #: Store the user submitted url address.
        self.remote_addr = upload

    def execute(self):
        with NetApiHost(self.remote_addr, self.handid, self.hw) as host:
            host.prepare_hwcode()
            host.compile()
            return host.run()


class InputClassHandin(BaseHandin):
    """CSV data submission handler, derived from :class:`BaseHandin`.

    :param handid: The uuid of this submission.
    :type handid: :class:`str`
    :param hwid: The uuid of the homework.
    :type hwid: :class:`str`
    :param upload: The submitted csv file data.
    :type upload: :class:`str`
    :param options: {}
    :type options: :class:`dict`
    """

    def __init__(self, handid, hwid, upload, options):
        super(InputClassHandin, self).__init__('input', handid, hwid, upload,
                                               options)

    def execute(self):
        with InputClassHost(self.handid, self.hw) as host:
            host.prepare_hwcode()
            with open(os.path.join(host.tempdir.path, 'data.csv'), 'wb') as f:
                f.write(self.upload)
            return host.run()
