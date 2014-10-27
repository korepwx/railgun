#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/codelang.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

"""Railgun homework can be configured to accept submissions in different
programming languages.

The type of content for various languages may be different.  For example,
a Python submission may be an archive file, while a NetAPI submission
may be just a url address.
This requires Railgun to generate different forms for these languages,
and to handle the POST data differently according to the submission type.

Thid module provides :class:`CodeLanguage` as the base class to generate
forms and to handle requests.  Derived from :class:`CodeLanguage`,
:class:`PythonLanguage`, :class:`JavaLanguage`, :class:`NetApiLanguage`
and :class:`InputLanguage` are the actual implementations.
"""

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
    """The base class for all programming language handlers.
    A derived class must override three methods: :meth:`upload_form`,
    :meth:`do_handle_upload` and :meth:`do_handle_download`.

    :param lang: The programming language identity.
    :type lang: :class:`str`
    :param lang_name: The translated programming language name.
    :type lang_name: :class:`~railgun.common.lazy_i18n.GetTextString`
    """

    def __init__(self, lang, lang_name):
        self.lang = lang
        self.name = lang_name

    def make_db_record(self, handid, hw):
        """Create a new submission in the database.

        The state of the new submission will be `Pending`.  The associated
        user will be :data:`~flask.ext.login.current_user`, and the `scale`
        will be set to :token:`g.ddl_scale`.

        .. note::

            :token:`g.ddl_scale` is initialized in
            :func:`railgun.website.views.homework`. We use this scale instead
            of calculating on the fly because the time may change and the
            deadline may expire during the request lifetime.

        :param handid: The submission uuid.
        :type handid: :class:`str`
        :param hw: The homework this submission belongs to.
        :type hw: :class:`~railgun.common.hw.Homework`

        :return: The created :class:`~railgun.website.models.Handin` object.
        """
        # Note: g.ddl_scale is setup in :func:`railgun.website.
        #       we must only rely on this scale, because such deadline may
        #       expire just during the time we process the request!
        handin = Handin(uuid=handid, hwid=hw.uuid, lang=self.lang,
                        state='Pending', user_id=current_user.id,
                        scale=g.ddl_scale)
        db.session.add(handin)
        db.session.commit()
        return handin

    def upload_form(self, hw):
        """Generate an upload form for the given homework in this language.
        Derived classes must override this method.

        :param hw: The homework instance.
        :type hw: :class:`~railgun.common.hw.Homework`
        """
        raise NotImplementedError()

    def store_content(self, handid, content):
        """Store the original data of given submission onto disk.

        Data file is placed under ``config.UPLOAD_STORE_DIR``.
        If ``config.STORE_UPLOAD`` is disabled, this method will do nothing.
        `content` may be any type of object, which will be serialized before
        writing to disk file.

        :param handid: The submission uuid.
        :type handid: :class:`str`
        :param content: The original data object.
        :type content: :class:`object`
        """
        if not app.config['STORE_UPLOAD']:
            return
        if not os.path.isdir(app.config['UPLOAD_STORE_DIR']):
            os.makedirs(app.config['UPLOAD_STORE_DIR'], 0700)
        fpath = os.path.join(app.config['UPLOAD_STORE_DIR'], handid)
        with open(fpath, 'wb') as f:
            f.write(pickle.dumps(content))

    def load_content(self, handid):
        """Load the original data of given submission from disk file.

        :param handid: The submission uuid.
        :type handid: :class:`str`
        :return: The loaded object, or :data:`None` if data file not exist.
        """
        fpath = os.path.join(app.config['UPLOAD_STORE_DIR'], handid)
        if os.path.isfile(fpath):
            with open(fpath, 'rb') as f:
                return pickle.loads(f.read())

    def do_handle_upload(self, handid, hw, form):
        """Called by :meth:`handle_upload` to help handle the submission.
        Derived classes should implement this to store the submission data,
        and to put this submission into runner queue.

        :param handid: The submission uuid.
        :type handid: :class:`str`
        :param hw: The homework instance.
        :type hw: :class:`~railgun.common.hw.Homework`
        :param form: The upload form generated by :meth:`upload_form`
        :type form: Derived class of :class:`flask_wtf.Form`
        """
        raise NotImplementedError()

    def handle_upload(self, handid, hw, form):
        """Handle the uploaded form data submitted to the given homework
        in this programming language.

        :param handid: The submission uuid.
        :type handid: :class:`str`
        :param hw: The homework instance.
        :type hw: :class:`~railgun.common.hw.Homework`
        :param form: The upload form generated by :meth:`upload_form`
        :type form: Derived class of :class:`flask_wtf.Form`
        """
        # save handin into the database
        handin = self.make_db_record(handid, hw)

        # post the job to run queue
        try:
            self.do_handle_upload(handid, hw, form)
        except Exception:
            # if we cannot post to run queue, modify the handin status to error
            handin.state = 'Rejected'
            handin.result = lazy_gettext('Could not commit to run queue.')
            handin.partials = []
            db.session.commit()
            # re-raise this exception
            raise

    def do_handle_download(self, stored_content):
        """Called by :meth:`handle_download` to help send the original
        submission data to the client. Derived classes should override
        this to extract data from stored objects, to set http headers,
        and finish other necessary process.

        :param stored_content: The stored object of this submission.
            Loading object from disk is finished in :meth:`do_handle_download`.
        :type stored_content: :class:`object`
        """
        raise NotImplementedError()

    def handle_download(self, handid):
        """Handle user's request to download original uploaded data of
        the given submission.

        :param handid: The submission uuid.
        :type handid: :class:`str`
        """
        payload = self.load_content(handid)
        if not payload:
            abort(404)
        return self.do_handle_download(payload)


class StandardLanguage(CodeLanguage):
    """The basic handler for `standard` programming languages (like Python
    and Java) that accepts archive files as submissions.

    This handler class will store the uploaded file content as well as its
    file name onto disk, in that Railgun relies on file extension to detect
    the archive file format.

    :param lang: The programming language identity.
    :type lang: :class:`str`
    :param lang_name: The translated programming language name.
    :type lang_name: :class:`~railgun.common.lazy_i18n.GetTextString`
    """

    def __init__(self, lang, lang_name):
        super(StandardLanguage, self).__init__(lang, lang_name)

    def upload_form(self, hw):
        return UploadHandinForm()

    def do_handle_upload(self, handid, hw, form):
        filename = form.handin.data.filename
        fcnt = base64.b64encode(form.handin.data.stream.read())
        # We store the user uploaded file in local storage!
        self.store_content(handid, {'fname': filename, 'fcnt': fcnt})
        # Push the submission to run queue
        run_python.delay(handid, hw.uuid, fcnt, {'filename': filename})

    def do_handle_download(self, stored_content):
        fcnt = base64.b64decode(stored_content['fcnt'])
        fname = stored_content['fname']
        return send_file(StringIO(fcnt), as_attachment=True,
                         attachment_filename=fname)


class PythonLanguage(StandardLanguage):
    """The handler for Python programing language.
    This is a derived class from :class:`StandardLanguage`, which only
    overrides the language identity and translated name.
    """

    def __init__(self):
        super(PythonLanguage, self).__init__('python', lazy_gettext('Python'))


class JavaLanguage(StandardLanguage):
    """The handler for Java programing language.
    This is a derived class from :class:`StandardLanguage`, which only
    overrides the language identity and translated name.
    """

    def __init__(self):
        super(JavaLanguage, self).__init__('java', lazy_gettext('Java'))


class NetApiLanguage(CodeLanguage):
    """The handler for `netapi` programming languages that accepts a url
    address as submission data, to check whether the remote server mentioned
    by this url works properly.
    """

    def __init__(self):
        super(NetApiLanguage, self).__init__('netapi', 'NetAPI')

    def do_handle_upload(self, handid, hw, form):
        # We store the user uploaded file in local storage!
        self.store_content(handid, form.address.data)
        # Push the submission to run queue
        run_netapi.delay(handid, hw.uuid, form.address.data, {})

    def do_handle_download(self, stored_content):
        resp = make_response(stored_content)
        resp.headers['Content-Type'] = 'text/plain'
        return resp

    def upload_form(self, hw):
        return AddressHandinForm()


class InputLanguage(CodeLanguage):
    """The handler for `input` programming languages that accepts csv data
    as submission.
    """

    def __init__(self):
        super(InputLanguage, self).__init__('input', 'CsvData')

    def do_handle_upload(self, handid, hw, form):
        # We store the user uploaded file in local storage!
        self.store_content(handid, form.csvdata.data)
        # Push the submission to run queue
        run_input.delay(handid, hw.uuid, form.csvdata.data, {})

    def do_handle_download(self, stored_content):
        resp = make_response(stored_content)
        resp.headers['Content-Type'] = 'text/csv'
        return resp

    def upload_form(self, hw):
        return CsvHandinForm()


#: A `dict(Language Identity -> CodeLanguage`) that maps identities to
#: programming language handlers.
languages = {
    'python': PythonLanguage(),
    'java': JavaLanguage(),
    'netapi': NetApiLanguage(),
    'input': InputLanguage(),
}
