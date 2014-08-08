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

from . import runconfig
from .hw import homeworks
from .errors import InternalServerError, InvalidHandinError
from railgun.common.lazy_i18n import gettext_lazy
from railgun.common.fileutil import Extractor


class BaseHandin(object):
    """Basic handin management class."""

    def __init__(self, handid, hwid, lang):
        # get homework instance from all loaded homeworks
        self.hw = homeworks.get_by_uuid(hwid)
        if (not self.hw):
            raise InternalServerError()
        # check whether the desired language is supported by this homework.
        if (lang not in self.hw.get_code_languages()):
            raise InvalidHandinError(gettext_lazy(
                'Language "%(lang)s" is not supported by this homework.',
                lang=lang
            ))
        # store handid & lang
        self.handid = handid
        self.lang = lang

    def execute(self):
        """Execute this handin, and report the result."""


class PythonHandin(BaseHandin):
    """Python handin management class."""

    def __init__(self, handid, hwid, filename):
        super(PythonHandin, self).__init__(handid, hwid, 'python')

        # load uploaded archive
        self.archive = Extractor.open(
            os.path.join(runconfig.UPLOAD_DIR, filename)
        )

    def execute(self):
        """Execute this handin as Python script."""
