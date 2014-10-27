#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/thuauth.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import re
import requests

from flask.ext.babel import gettext as _

from .userauth import AuthProvider
from .context import app, db
from .models import User


class TsinghuaAccount(object):
    """Represent a Tsinghua remote account.

    We can only know the username of Tsinghua accounts.  So we just put
    a faked email into :attr:`email`.  Then the new users from Tsinghua
    will be required to fill in their real emails.

    You may refer to :func:`~railgun.website.credential.should_update_email`
    to know about this feature.

    :param name: The username of this user.
    :type name: :class:`str`
    """

    def __init__(self, name):
        self.name = name
        self.email = name + app.config['EXAMPLE_USER_EMAIL_SUFFIX']

    def __repr__(self):
        return '<ThuUser(%s)>' % self.name


class TsinghuaAuthProvider(AuthProvider):
    """The authentication provider that validates user with Tsinghua
    info account.

    You may activate this auth provider by adding the following contents
    into ``config/website.py``::

        AUTH_PROVIDERS += [(
            'railgun.website.thuauth.TsinghuaAuthProvider', {
                'name': 'tsinghua',
                'auth_url': 'http://student.tsinghua.edu.cn/practiceLogin.do',
            }
        )]
    """

    def __init__(self, name, auth_url):
        super(TsinghuaAuthProvider, self).__init__(name)
        self.auth_url = auth_url
        self.name_pattern = re.compile(r'^\d+$')

    def __repr__(self):
        return '<TsinghuaAuthProvider(%s)>' % self.name

    def display_name(self):
        return _('Tsinghua')

    def pull(self, name=None, email=None, dbuser=None):

        # Tsinghua account could only be (\d+).
        if email:
            return None
        if not self.name_pattern.match(name):
            return None

        # We should put the new user into database until `authenticate`.
        return TsinghuaAccount(name), dbuser

    def push(self, dbuser, password=None):
        if password is not None:
            raise ValueError('Could not set the password of Tsinghua account.')

    def authenticate(self, user, dbuser, password):
        # Check username by online api to see whether the user exists
        ret = requests.post(self.auth_url,
                            data={
                                'userName': user.name,
                                'password': password,
                            }).text
        if not ret:
            return False

        # Create the db object if not exist
        if dbuser is None:
            try:
                dbuser = User(name=user.name, email=user.email, password=None,
                              is_admin=False, provider=self.name)
                # Special hack: get locale & timezone from request
                dbuser.fill_i18n_from_request()
                # save to database
                db.session.add(dbuser)
                db.session.commit()
                self._log_pull(user, create=True)
            except Exception:
                dbuser = None
                self._log_pull(user, create=True, exception=True)

        # We do not need to update the db user, because THU auth only
        # stores username
        return dbuser

    def init_form(self, form):
        self._init_form_helper(form, ('name', 'password', 'confirm'))
