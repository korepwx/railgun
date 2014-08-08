#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/runner/handin.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

from cStringIO import StringIO

from .hw import homeworks
from .errors import InternalServerError, InvalidHandinError
from railgun.common.lazy_i18n import gettext_lazy


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

    def __init__(self, handid, hwid, upload):
        super(PythonHandin, self).__init__(handid, hwid, 'python')

        # make upload file object
        self.archive = StringIO(upload)

    def execute(self):
        """Execute this handin as Python script."""
