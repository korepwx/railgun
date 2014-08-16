#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/userauth.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import os

from werkzeug.security import generate_password_hash, check_password_hash
from wtforms.fields import Field, HiddenField

from railgun.common.csvdata import CsvSchema, CsvString, CsvBoolean
from .models import User
from .context import app, db
from .ldapauth import LdapAuthProvider


class AuthRequest(object):
    """Represent an authentication request.

    User can request to authenticate with login name and password. Login
    name can be either username or email.
    """

    def __init__(self, login, password):
        self.login = login
        self.password = password

        # Users created by railgun signup page cannot contain '@'.
        # I suppose that external `UserAuth` providers also assume this.
        self.email_login = ('@' in login)

    def __repr__(self):
        auth_type = 'email' if self.email_login else 'username'
        return '<AuthRequest(%s=%s)>' % (auth_type, self.login)


class AuthProvider(object):
    """The base class for all external user authenticate providers.

    If a user try to authenticate with login and password which does not
    exist in main database, the external user authenticate providers will
    be queried to find such user.

    What's more, when a user is trying to edit his profile, the authenticate
    provider will also receive certain updates.

    External auth provider can only store parts of user data. However,
    (username, email, password) are necessary fields that the provider should
    store.
    """

    def __init__(self, name):
        """Create a new `AuthProvider`."""
        self.name = name

    def __repr__(self):
        return '<AuthProvider(%s)>' % self.name

    def _log_pull(self, user, create=False, exception=False):
        """Log a pull request on given `user`."""
        if (not exception):
            if (create):
                app.logger.debug('Pulled new user (%s, %s) from %s.' %
                                 (user.name, user.email, self))
            else:
                app.logger.debug('Pulled existing user (%s, %s) from %s.' %
                                 (user.name, user.email, self))
        else:
            if (create):
                app.logger.exception(
                    'Could not pull new user (%s, %s) from %s.' %
                    (user.name, user.email, self)
                )
            else:
                app.logger.exception(
                    'Could not pull existing user (%s, %s) from %s.' %
                    (user.name, user.email, self)
                )

    def pull(self, auth_request, dbuser=None):
        """Try to authenticate with `auth_request`.

        Return None and do no update on database if `auth_request` cannot
        pass.

        When `auth_request` passed, if `dbuser` is None, construct a new db
        user and save to database with external information.

        If `auth_request` passed and `dbuser` is not None, any mismatch fields
        in `dbuser` should be updated by external user data.
        """

        raise NotImplementedError()

    def push(self, dbuser, password=None):
        """Update the external user information according to provided `dbuser`.
        External user authenticate providers is allowed to store only parts of
        user profile.

        If `password` is not None, then the password of target user should also
        be updated.
        """

        raise NotImplementedError()

    def _strip_form_helper(self, form, lock_fields):
        """Common strip_form helper lock all fields in `lock_fields`."""

        for k, v in form.__dict__.items():
            if (isinstance(v, Field) and not isinstance(v, HiddenField)):
                if (k in lock_fields):
                    del form[k]

    def strip_form(self, form):
        """Some providers may lock some fields of user data."""

        raise NotImplementedError()


class CsvFileUserObject(CsvSchema):
    """Schema of CSV file user database."""

    name = CsvString()
    email = CsvString()
    password = CsvString()
    is_admin = CsvBoolean(name='admin')


class CsvFileAuthProvider(AuthProvider):
    """CSV file auth provider that only stores is_admin in addition."""

    def __init__(self, name, path):
        super(CsvFileAuthProvider, self).__init__(name)

        self.csvpath = path
        self.users = []
        self.__interested_fields = ('name', 'email', 'is_admin')
        self.reload()

    def __repr__(self):
        return '<CsvFileAuthProvider(%s)>' % self.name

    def reload(self):
        """Reload user database from external csv file."""
        if (os.path.isfile(self.csvpath)):
            with open(self.csvpath, 'rb') as f:
                self.users = list(CsvSchema.LoadCSV(CsvFileUserObject, f))
        self.__name_to_user = {u.name: u for u in self.users}
        self.__email_to_user = {u.email: u for u in self.users}

    def flush(self):
        """Flush user database to external csv file."""
        with open(self.csvpath, 'wb') as f:
            CsvSchema.SaveCSV(CsvFileUserObject, f, self.users)
        app.logger.debug('%s flushed.' % self)

    def pull(self, auth_request, dbuser=None):

        # Get the interested user by `auth_request`
        if (auth_request.email_login):
            user = self.__email_to_user.get(auth_request.login, None)
        else:
            user = self.__name_to_user.get(auth_request.login, None)

        # Return none if user not found, or password not match
        if (not user or
                not check_password_hash(user.password, auth_request.password)):
            return None

        # Auth passed, dbuser is None, create new one
        if (dbuser is None):
            try:
                dbuser = User(name=user.name, email=user.email, password=None,
                              is_admin=user.is_admin, provider=self.name)
                db.session.add(dbuser)
                db.session.commit()
                self._log_pull(user, create=True)
            except Exception:
                dbuser = None
                self._log_pull(user, create=True, exception=True)
            return dbuser

        # Auth passed, dbuser is not None, update existing one
        updated = False
        for k in self.__interested_fields:
            if (getattr(dbuser, k) != getattr(user, k)):
                updated = True
                setattr(dbuser, k, getattr(user, k))
        if (updated):
            try:
                db.session.commit()
                self._log_pull(user, create=False)
            except Exception:
                dbuser = None
                self._log_pull(user, create=False, exception=True)
        return dbuser

    def push(self, dbuser, password=None):
        user = self.__name_to_user[dbuser.name]

        # If password is not None, store and update the password hash
        if (password is not None):
            user.password = generate_password_hash(password)

        # Set other cleartext fields
        for k in self.__interested_fields:
            setattr(user, k, getattr(dbuser, k))

        self.flush()

    def strip_form(self, form):
        self._strip_form_helper(form, ('name', 'email'))


class AuthProviderSet(object):
    """Manage all of the auth providers."""

    def __init__(self):
        self.items = []
        self.__name_to_item = {}

    def __iter__(self):
        return iter(self.items)

    def add(self, provider):
        self.items.append(provider)
        self.__name_to_item[provider.name] = provider

    def get(self, name):
        """Get provider with `name`."""
        return self.__name_to_item[name]

    def pull(self, auth_request, dbuser=None):
        """Pull user from providers one by one."""
        for p in self.items:
            ret = p.pull(auth_request, dbuser)
            if (ret):
                return ret

    def push(self, dbuser, password=None):
        """Push user to providers according to dbuser.provider."""
        self.get(dbuser.provider).push(dbuser, password)

    def strip_form(self, provider, form):
        self.get(provider).strip_form(form)


def authenticate(login, password):
    """Top routine to authenticate with (login, password).
    Return the loaded dbuser object if auth passed.
    """

    # Make the auth request
    req = AuthRequest(login, password)

    # Load dbuser object from database if possible
    if (req.email_login):
        dbuser = db.session.query(User).filter(User.email == req.login).first()
    else:
        dbuser = db.session.query(User).filter(User.name == req.login).first()

    # If dbuser exists and dbuser.provider is empty, just check its password
    if (dbuser is not None and not dbuser.provider):
        if (check_password_hash(dbuser.password, req.password)):
            return dbuser
        return None

    # Otherwise query the auth providers
    return auth_providers.pull(req, dbuser=dbuser)


# Initialize the builtin auth providers
auth_providers = AuthProviderSet()
auth_providers.add(
    CsvFileAuthProvider(
        'csvfile',
        os.path.join(app.config['RAILGUN_ROOT'], 'config/users.csv')
    )
)
auth_providers.add(LdapAuthProvider('LDAP'))
