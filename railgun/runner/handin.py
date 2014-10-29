#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/runner/handin.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import os
import base64

from . import runconfig
from .hw import homeworks
from .errors import (InternalServerError, LanguageNotSupportError,
                     ExtractFileFailure)
from .host import PythonHost, NetApiHost, InputClassHost
from railgun.common.fileutil import Extractor


class TempDiskUploadFile(object):
    """Save base64 encoded upload data onto disk and delete it when leave."""

    def __init__(self, upload, fname, ignore_error=False):
        self.path = os.path.join(runconfig.TEMPORARY_DIR, fname)
        self.upload = upload
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
    """Basic handin management class.

    :param upload: The uploaded data of this submission.
        It may be base64 encoded byte sequence to represent an archive file
        in a `Python` submission, or a url address in a `NetAPI` submission.
    :type upload: :class:`str`
    :param options: The extra options of this submission.
        Vary for different types of submissions.
    :type options: :class:`dict`
    """

    def __init__(self, handid, hwid, lang, upload, options):
        # check whether options is dict
        if not isinstance(options, dict):
            raise TypeError("`options` should be dictionary.")
        # get homework instance from all loaded homeworks
        self.hw = homeworks.get_by_uuid(hwid)
        if not self.hw:
            raise InternalServerError()
        # check whether the desired language is supported by this homework.
        if lang not in self.hw.get_code_languages():
            raise LanguageNotSupportError(lang)
        # store handid & lang
        self.handid = handid
        self.lang = lang
        # store upload and options
        self.upload = upload
        self.options = options

    def execute(self):
        """Execute this handin, and report the result."""


class PythonHandin(BaseHandin):
    """Python handin management class."""

    def __init__(self, handid, hwid, upload, options):
        super(PythonHandin, self).__init__(handid, hwid, 'python', upload,
                                           options)
        self.archive = None

    def execute(self):
        """Execute this handin as Python script. Should return
        (exitcode, stdout, stderr)."""

        with PythonHost(self.handid, self.hw) as host:
            # put uploaded file content onto disk and then open the archive
            # this is because some Extractors may rely on disk files.
            archive_fext = os.path.splitext(self.options['filename'])[1]
            archive_file = '%s%s' % (self.handid, archive_fext)
            with TempDiskUploadFile(self.upload, archive_file) as f:
                try:
                    self.archive = Extractor.open(f.path)
                except Exception:
                    raise ExtractFileFailure()
                host.prepare_hwcode()
                host.extract_handin(self.archive)
                return host.run()


class NetApiHandin(BaseHandin):
    """NetApi handin management class."""

    def __init__(self, handid, hwid, upload, options):
        super(NetApiHandin, self).__init__(handid, hwid, 'netapi', upload,
                                           options)
        self.remote_addr = upload

    def execute(self):
        """Execute this handin as NetAPI script. Should return
        (exitcode, stdout, stderr)."""

        with NetApiHost(self.remote_addr, self.handid, self.hw) as host:
            host.prepare_hwcode()
            host.compile()
            return host.run()


class InputClassHandin(BaseHandin):
    """Input class handin management."""

    def __init__(self, handid, hwid, upload, options):
        super(InputClassHandin, self).__init__(handid, hwid, 'input', upload,
                                               options)

    def execute(self):
        """Execute this handin as InputClass script. Should return
        (exitcode, stdout, stderr)."""

        with InputClassHost(self.handid, self.hw) as host:
            host.prepare_hwcode()
            with open(os.path.join(host.tempdir.path, 'data.csv'), 'wb') as f:
                f.write(self.upload)
            return host.run()
