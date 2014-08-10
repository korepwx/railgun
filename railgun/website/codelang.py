#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/codelang.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import base64

from flask import g
from flask.ext.babel import lazy_gettext
from flask.ext.login import current_user

from .context import app, db
from .forms import UploadHandinForm, AddressHandinForm
from .models import Handin
from railgun.runner.tasks import run_python
from railgun.common.lazy_i18n import gettext_lazy


class CodeLanguage(object):
    """the base class for all uploading utilities of particular language"""

    def __init__(self, lang, lang_name):
        self.lang = lang
        self.name = lang_name

    def make_db_record(self, handid, hw, lang):
        """Make a Handin record"""
        # Note: g.ddl_scale is setup in views.homework
        #       we must only rely on this scale, because such deadline may
        #       pass when processing the request
        handin = Handin(uuid=handid, hwid=hw.uuid, lang=lang, state='Pending',
                        user_id=current_user.id, scale=g.ddl_scale)
        db.session.add(handin)
        db.session.commit()
        return handin

    def upload_form(self, hw):
        """make handin form for given `hw`."""

    def handle_upload(self, handid, hw, lang, form):
        """handle upload request from student."""


class StandardLanguage(CodeLanguage):
    """standard code language that accepts a packed archive as handin"""

    def __init__(self, lang, lang_name):
        super(StandardLanguage, self).__init__(lang, lang_name)

    def upload_form(self, hw):
        """make a handin form that uploads an archive"""
        return UploadHandinForm()

    def handle_upload(self, handid, hw, lang, form):
        """save uploaded file as UPLOAD_DIR/[handid].[ext]"""

        # save handin into the database
        handin = self.make_db_record(handid, hw, lang)

        # post the job to run queue
        try:
            fcnt = base64.b64encode(form.handin.data.stream.read())
            run_python.delay(handid, hw.uuid, fcnt, {
                'filename': form.handin.data.filename
            })
        except Exception:
            # if we cannot post to run queue, modify the handin status to error
            handin.state = 'Rejected'
            handin.result = gettext_lazy('Could not commit to run queue.')
            handin.partials = []
            db.session.commit()
            # re-raise this exception
            raise


class PythonLanguage(StandardLanguage):
    """code language implementation of Python"""

    def __init__(self):
        super(PythonLanguage, self).__init__('python', lazy_gettext('Python'))


class JavaLanguage(StandardLanguage):
    """code language implementation of Java"""

    def __init__(self):
        super(JavaLanguage, self).__init__('java', lazy_gettext('Java'))


class NetApiLanguage(CodeLanguage):
    """code language that accepts a URL address as handin"""

    def __init__(self):
        super(NetApiLanguage, self).__init__('netapi', 'NetAPI')

    def upload_form(self, hw):
        """make a handin form that inputs an address"""
        return AddressHandinForm()

languages = {
    'python': PythonLanguage(),
    'java': JavaLanguage(),
    'netapi': NetApiLanguage()
}


# get human readable name for given code lang
@app.template_filter(name='codelang')
def __inject_template_codelang(s):
    lang = languages.get(s, None)
    if (lang):
        return lang.name


# inject languages dictionary into template context
@app.context_processor
def __inject_languages():
    return dict(languages=languages)
