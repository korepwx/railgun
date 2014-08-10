#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/runner/handin.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import os
import base64

from . import runconfig
from .hw import homeworks
from .errors import InternalServerError, LanguageNotSupportError
from .host import PythonHost
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
            if (os.path.isfile(self.path)):
                os.remove(self.path)
        except Exception:
            if not self.ignore_error:
                raise


class BaseHandin(object):
    """Basic handin management class."""

    def __init__(self, handid, hwid, lang, upload, options):
        # check whether options is dict
        if (not isinstance(options, dict)):
            raise TypeError("`options` should be dictionary.")
        # get homework instance from all loaded homeworks
        self.hw = homeworks.get_by_uuid(hwid)
        if (not self.hw):
            raise InternalServerError()
        # check whether the desired language is supported by this homework.
        if (lang not in self.hw.get_code_languages()):
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
                self.archive = Extractor.open(f.path)
                host.prepare_hwcode()
                host.extract_handin(self.archive)
                return host.run()
