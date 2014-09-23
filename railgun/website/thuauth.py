#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/thuauth.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import re
import requests

from .userauth import AuthProvider
from .context import app, db
from .models import User


class TsinghuaAccount(object):
    """We can only know username when we are playing with Tsinghua account."""

    def __init__(self, name):
        self.name = name
        self.email = name + app.config['EXAMPLE_USER_EMAIL_SUFFIX']

    def __repr__(self):
        return '<ThuUser(%s)>' % self.name


class TsinghuaAuthProvider(AuthProvider):
    """Tsinghua auth provider that authenticates with info account."""

    def __init__(self, name, auth_url):
        super(TsinghuaAuthProvider, self).__init__(name)
        self.auth_url = auth_url
        self.name_pattern = re.compile(r'^\d+$')

    def __repr__(self):
        return '<TsinghuaAuthProvider(%s)>' % self.name

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
