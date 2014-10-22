#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/codelang.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import os
import base64
import cPickle as pickle
from cStringIO import StringIO

from flask import g, send_file, abort, make_response
from flask.ext.babel import lazy_gettext
from flask.ext.login import current_user

from .context import app, db
from .forms import UploadHandinForm, AddressHandinForm, CsvHandinForm
from .models import Handin
from railgun.runner.tasks import run_python, run_netapi, run_input


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

    def _store_content(self, handid, content):
        """store `content` into upload store directory"""
        if not app.config['STORE_UPLOAD']:
            return
        if not os.path.isdir(app.config['UPLOAD_STORE_DIR']):
            os.makedirs(app.config['UPLOAD_STORE_DIR'], 0700)
        fpath = os.path.join(app.config['UPLOAD_STORE_DIR'], handid)
        with open(fpath, 'wb') as f:
            f.write(pickle.dumps(content))

    def _load_content(self, handid):
        """load `content` from upload store directory."""
        fpath = os.path.join(app.config['UPLOAD_STORE_DIR'], handid)
        if os.path.isfile(fpath):
            with open(fpath, 'rb') as f:
                return pickle.loads(f.read())

    def _handle_upload(self, handid, hw, lang, form):
        pass

    def handle_upload(self, handid, hw, lang, form):
        """handle upload request from student."""
        # save handin into the database
        handin = self.make_db_record(handid, hw, lang)

        # post the job to run queue
        try:
            self._handle_upload(handid, hw, lang, form)
        except Exception:
            # if we cannot post to run queue, modify the handin status to error
            handin.state = 'Rejected'
            handin.result = lazy_gettext('Could not commit to run queue.')
            handin.partials = []
            db.session.commit()
            # re-raise this exception
            raise

    def _handle_download(self, stored_content):
        pass

    def handle_download(self, handid):
        """handle download request from student."""
        payload = self._load_content(handid)
        if not payload:
            abort(404)
        return self._handle_download(payload)


class StandardLanguage(CodeLanguage):
    """standard code language that accepts a packed archive as handin"""

    def __init__(self, lang, lang_name):
        super(StandardLanguage, self).__init__(lang, lang_name)

    def upload_form(self, hw):
        """make a handin form that uploads an archive"""
        return UploadHandinForm()

    def _handle_upload(self, handid, hw, lang, form):
        filename = form.handin.data.filename
        fcnt = base64.b64encode(form.handin.data.stream.read())
        # We store the user uploaded file in local storage!
        self._store_content(handid, {'fname': filename, 'fcnt': fcnt})
        # Push the submission to run queue
        run_python.delay(handid, hw.uuid, fcnt, {'filename': filename})

    def _handle_download(self, stored_content):
        fcnt = base64.b64decode(stored_content['fcnt'])
        fname = stored_content['fname']
        return send_file(StringIO(fcnt), as_attachment=True,
                         attachment_filename=fname)


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

    def _handle_upload(self, handid, hw, lang, form):
        # We store the user uploaded file in local storage!
        self._store_content(handid, form.address.data)
        # Push the submission to run queue
        run_netapi.delay(handid, hw.uuid, form.address.data, {})

    def _handle_download(self, stored_content):
        resp = make_response(stored_content)
        resp.headers['Content-Type'] = 'text/plain'
        return resp

    def upload_form(self, hw):
        """make a handin form that inputs an address"""
        return AddressHandinForm()


class InputLanguage(CodeLanguage):
    """code language that accepts a CSV data as black-box input."""

    def __init__(self):
        super(InputLanguage, self).__init__('input', 'CsvData')

    def _handle_upload(self, handid, hw, lang, form):
        # We store the user uploaded file in local storage!
        self._store_content(handid, form.csvdata.data)
        # Push the submission to run queue
        run_input.delay(handid, hw.uuid, form.csvdata.data, {})

    def _handle_download(self, stored_content):
        resp = make_response(stored_content)
        resp.headers['Content-Type'] = 'text/csv'
        return resp

    def upload_form(self, hw):
        """make a handin form that inputs CSV data"""
        return CsvHandinForm()


languages = {
    'python': PythonLanguage(),
    'java': JavaLanguage(),
    'netapi': NetApiLanguage(),
    'input': InputLanguage(),
}


@app.context_processor
def __inject_languages():
    return dict(languages=languages)
