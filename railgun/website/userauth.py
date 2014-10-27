#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/userauth.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

"""Railgun supports third-party authentication providers.

We cannot store and shouldn't store the up-to-time password of users from
third-party authentication providers.  Moreover we even cannot keep other
data of a third-party user fresh.

In Railgun, we store neither the plain password nor the hashed ones for
third-party users.  Instead, we store the `provider identity` for such
users.  Each time these users are trying to sign in, we query the upstream
provider with the user provided login name and password, and validate the
user according to the remote response.

The other data from third-party authentication providers, like the user
email address, or other information, will be pulled from the remote server
each time we make a third-party authentication.
On the other hand, each time a user edits his or her profile, we push the
new data to remote server.  We keep the user profile synchronized with
third-party providers in this way.
"""

import os

from werkzeug.security import generate_password_hash, check_password_hash
from wtforms.fields import Field, HiddenField
from flask.ext.babel import gettext as _

from railgun.common.csvdata import CsvSchema, CsvString, CsvBoolean
from railgun.common.pyutil import find_object
from .models import User
from .context import app, db
from .utility import is_email


class AuthProvider(object):
    """The base class for all third-party user authenticate providers.

    If a user try to authenticate with login and password which does not
    exist in main database, the external user authenticate providers will
    be queried to find such user.

    What's more, when a user is trying to edit his profile, the authenticate
    provider will also receive certain updates.

    External auth provider can only store parts of user data. However,
    `username` and `password` are necessary fields that the provider should
    store.

    :param name: The identity of this authentication provider, which will
        be used to associate user objects in the database with this instance.
    :type name: :class:`str`
    """

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<AuthProvider(%s)>' % self.name

    def _log_pull(self, user, create=False, exception=False):
        """Log a pull request on given user.

        :param user: The authentication user object.
        :param create: Whether we are trying to create a new database user?
        :param exception: Whether any exception occurred and should be logged?
        """
        if not exception:
            if create:
                app.logger.debug('Pulled new user (%s, %s) from %s.' %
                                 (user.name, user.email, self))
            else:
                app.logger.debug('Pulled existing user (%s, %s) from %s.' %
                                 (user.name, user.email, self))
        else:
            if create:
                app.logger.exception(
                    'Could not pull new user (%s, %s) from %s.' %
                    (user.name, user.email, self)
                )
            else:
                app.logger.exception(
                    'Could not pull existing user (%s, %s) from %s.' %
                    (user.name, user.email, self)
                )

    def display_name(self):
        """Get a translated name of this auth provider.  Derived classes
        should implement this.
        """
        raise NotImplementedError()

    def pull(self, name=None, email=None, dbuser=None):
        """Try to get user from remote provider by `name` or `email`.
        Derived classes should implement this.

        Return :data:`None` if requested user does not exist.

        If user exists, and if `dbuser` is None, construct a new database
        user and save it, filled with user data from the remote.

        If `dbuser` is not None, any mismatch fields in `dbuser` should be
        updated according to remote user.

        :return: A :class:`tuple` of (remote user, database user), or
            :data:`None` if the user does not exist on remote server.
        """
        raise NotImplementedError()

    def push(self, dbuser, password=None):
        """Update the user on remote server according to provided `dbuser`.
        If `password` is not None, then the password of remote user should also
        be updated.  Derived classes should implement this.

        :param dbuser: The database user object.
        :type dbuser: :class:`~railgun.website.models.User`
        :param password: The updated user password.
        :type password: :class:`str`
        """
        raise NotImplementedError()

    def authenticate(self, user, dbuser, password):
        """Try to authenticate the given remote `user` with `password`.
        Derived classes should implement this.

        :param user: The remote user object (created by :meth:`pull`)
        :param dbuser: The database user object.
        :type dbuser: :class:`~railgun.website.models.User`
        :param password: The provided password.
        :type password: :class:`str`

        :return: The database object if authenticated, :data:`None` otherwise.
        :rtype: :class:`~railgun.website.models.User` or :data:`None`
        """
        raise NotImplementedError()

    def _init_form_helper(self, form, lock_fields):
        """General :meth:`init_form` helper utility to remove all fields
        in `lock_fields`.

        :param form: The :class:`flask_wtf.Form` instance.
        :param lock_fields: :class:`list` of field names to be removed.
        """
        for k, v in form.__dict__.items():
            if isinstance(v, Field) and not isinstance(v, HiddenField):
                if k in lock_fields:
                    del form[k]

    def init_form(self, form):
        """Third-party providers may store only parts of the user data.
        Derived classes should implement this to modify the user profile
        form.

        :param form: The :class:`flask_wtf.Form` instance.
        """
        raise NotImplementedError()


class CsvFileUserObject(CsvSchema):
    """Schema of CSV user database file."""

    #: The user name string field.
    name = CsvString()
    #: The email address string field.
    email = CsvString()
    #: The hashed password string field.
    password = CsvString()
    #: The boolean field that indicates whether this user is an admin.
    is_admin = CsvBoolean(name='admin')


class CsvFileAuthProvider(AuthProvider):
    """CSV file authentication provider.

    This is a toy auth provider.  You may create your own auth provider
    on the basis of this one, and you may own the first administrator
    account by add the following text into ``config/users.csv``::

        name,password,email,admin
        "admin","pbkdf2:sha1:1000$aWa1MeYA$812c7fe6cfa00060b6e3fe0dfbbe99da98b6d1eb","admin@example.org",True

    Where the account name is ``admin``, and the password is ``admin123``.
    :class:`CsvFileAuthProvider` is enabled by default, with the following
    contents in ``railgun/website/webconfig.py``::

        AUTH_PROVIDERS = [
            ('railgun.website.userauth.CsvFileAuthProvider', {
                'name': 'csvfile',
                'path': os.path.join(RAILGUN_ROOT, 'config/users.csv'),
            }),
        ]

    :param name: The identity of this authentication provider.
    :type name: :class:`str`
    :param path: The path of the csv file.
    :type path: :class:`str`
    """

    def __init__(self, name, path):
        super(CsvFileAuthProvider, self).__init__(name)

        self.csvpath = path
        self.users = []
        self.__interested_fields = ('name', 'email', 'is_admin')
        self.reload()

    def __repr__(self):
        return '<CsvFileAuthProvider(%s)>' % self.name

    def display_name(self):
        return _('Csv File')

    def reload(self):
        if os.path.isfile(self.csvpath):
            with open(self.csvpath, 'rb') as f:
                self.users = list(CsvSchema.LoadCSV(CsvFileUserObject, f))
        self.__name_to_user = {u.name: u for u in self.users}
        self.__email_to_user = {u.email: u for u in self.users}

    def flush(self):
        with open(self.csvpath, 'wb') as f:
            CsvSchema.SaveCSV(CsvFileUserObject, f, self.users)
        app.logger.debug('%s flushed.' % self)

    def hash_password(self, plain):
        return generate_password_hash(plain)

    def check_password(self, hashed, plain):
        return check_password_hash(hashed, plain)

    def pull(self, name=None, email=None, dbuser=None):

        # Get the interested user by `auth_request`
        if email:
            user = self.__email_to_user.get(email, None)
        else:
            user = self.__name_to_user.get(name, None)

        # Return none if user not found, or password not match
        if not user:
            return None

        # dbuser is None, create new one
        if dbuser is None:
            try:
                dbuser = User(name=user.name, email=user.email, password=None,
                              is_admin=user.is_admin, provider=self.name)
                # Special hack: get locale & timezone from request
                dbuser.fill_i18n_from_request()
                # save to database
                db.session.add(dbuser)
                db.session.commit()
                self._log_pull(user, create=True)
            except Exception:
                dbuser = None
                self._log_pull(user, create=True, exception=True)
            return (user, dbuser)

        # dbuser is not None, update existing one
        updated = False
        for k in self.__interested_fields:
            if getattr(dbuser, k) != getattr(user, k):
                updated = True
                setattr(dbuser, k, getattr(user, k))
        if updated:
            try:
                db.session.commit()
                self._log_pull(user, create=False)
            except Exception:
                dbuser = None
                self._log_pull(user, create=False, exception=True)
        return (user, dbuser)

    def push(self, dbuser, password=None):
        user = self.__name_to_user[dbuser.name]

        # If password is not None, store and update the password hash
        if password:
            user.password = self.hash_password(password)

        # Set other cleartext fields
        for k in self.__interested_fields:
            setattr(user, k, getattr(dbuser, k))

        self.flush()

    def authenticate(self, user, dbuser, password):
        if self.check_password(user.password, password):
            return dbuser

    def init_form(self, form):
        self._init_form_helper(form, ('name', 'email'))


class AuthProviderSet(object):
    """The registry for all :class:`AuthProvider` objects.

    This class manages all third-party authentication providers, and provide
    convenient methods to authenticate a user with these providers one
    after another.

    However, it does not take database users into account.  You may use
    the top-most function :func:`authenticate` to validate a user's
    credential.
    """

    def __init__(self):
        #: :class:`list` of :class:`AuthProvider` instances.
        self.items = []
        self.__name_to_item = {}

    def __iter__(self):
        return iter(self.items)

    def add(self, provider):
        """Add a :class:`AuthProvider` into this set.

        :param provider: The authentication provider.
        :type provider: :class:`AuthProvider`
        """
        self.items.append(provider)
        self.__name_to_item[provider.name] = provider

    def get(self, name):
        """Get a :class:`AuthProvider` according to its identity.

        :param name: The identity of authentication provider.
        :type name: :class:`str`
        :return: Requested :class:`AuthProvider` instance.
        :raises: :class:`KeyError` if requested provider does not exist.
        """
        return self.__name_to_item[name]

    def pull(self, name=None, email=None, dbuser=None):
        """Pull the user from third-party providers.

        Only one of the `name` and the `email` should be provided to fetch
        the user, otherwise the behaviour is undefined.

        :param name: The name of the requested user.
        :type name: :class:`str`
        :param email: The email of the requested user.
        :type email: :class:`str`
        :param dbuser: The database user object.
        :type dbuser: :class:`~railgun.website.models.User`

        :return: A :class:`tuple` of (remote user, database user), or
            :data:`None` if the user does not exist on remote server.
        """
        for p in self.items:
            ret = p.pull(name=name, email=email, dbuser=dbuser)
            if ret:
                return ret

    def authenticate(self, **kwargs):
        """Try to authenticate the user by third-party providers.

        Only one of the `name` and the `email` should be provided, otherwise
        the behaviour is undefined.

        :param name: Authenticate the user by username.
        :type name: :class:`str`
        :param email: Authenticate the user by email.
        :type email: :class:`str`
        :param password: The plain user password.
        :type password: :class:`str`
        :param dbuser: The database user object.
        :type dbuser: :class:`~railgun.website.models.User`

        :return: The database object if authenticated, :data:`None` otherwise.
        :rtype: :class:`~railgun.website.models.User` or :data:`None`
        """
        name = kwargs.get('name', None)
        email = kwargs.get('email', None)
        password = kwargs['password']
        dbuser = kwargs.get('dbuser', None)

        # which provider should we use?
        providers = self.items if not dbuser else [self.get(dbuser.provider)]

        # Query about each provider
        for p in providers:
            ret = p.pull(name=name, email=email, dbuser=dbuser)
            if ret:
                # Check whether user passes authentication
                user, dbuser = ret[0], ret[1]
                dbuser = p.authenticate(user, dbuser, password)
                if dbuser:
                    return dbuser

    def push(self, dbuser, password=None):
        """Push the given database user object to its corresponding
        third-party authentication provider.
        If `password` is given, the remote user password will also be
        updated.

        :param dbuser: The database user object.
        :type dbusr: :class:`~railgun.website.models.User`
        :param password: The plain user password.
        :type password: :class:`str`
        """
        self.get(dbuser.provider).push(dbuser, password)

    def init_form(self, provider, form):
        """Modify the given form according to given authentication provider.

        :param provider: The identity of auth provider.
        :type provider: :class:`str`
        :param form: The form to be modified.
        :type form: :class:`flask_wtf.Form`
        """
        self.get(provider).init_form(form)

    def init_providers(self):
        """Initialize the providers according to config value
        ``webconfig.AUTH_PROVIDERS``.
        """

        for objname, kwargs in app.config['AUTH_PROVIDERS']:
            obj = find_object(objname)
            provider = obj(**kwargs)
            app.logger.info('Created AuthProvider "%s".' % provider.name)
            self.add(provider)


def authenticate(login, password):
    """Try to authenticate the user with `login` and `password`.

    :param login: The username or email, depends on the string value.
    :type login: :class:`str`
    :param password: The plain user password.
    :type password: :class:`str`

    :return: The database object if authenticated, :data:`None` otherwise.
    :rtype: :class:`~railgun.website.models.User` or :data:`None`
    """

    # Load dbuser object from database if possible
    email_login = is_email(login)
    if email_login:
        dbuser = db.session.query(User).filter(User.email == login).first()
    else:
        dbuser = db.session.query(User).filter(User.name == login).first()

    # If dbuser exists and dbuser.provider is empty, just check its password
    if dbuser is not None and not dbuser.provider:
        if check_password_hash(dbuser.password, password):
            return dbuser
        return None

    # Otherwise authenticate through auth providers.
    if email_login:
        return auth_providers.authenticate(email=login, password=password,
                                           dbuser=dbuser)
    else:
        return auth_providers.authenticate(name=login, password=password,
                                           dbuser=dbuser)


def has_user(login):
    """Check whether there exists a user with given `login` as username
    or email (depending on `login` itself) in the database and on remote
    servers of third-party authentication providers.

    :param login: The username or email.
    :type login: :class:`str`
    :return: A :class:`bool` indicating the existence of user.
    """

    # Load dbuser object from database if possible
    email_login = is_email(login)
    if email_login:
        ucount = db.session.query(User).filter(User.email == login).count()
    else:
        ucount = db.session.query(User).filter(User.name == login).count()

    # If dbuser exists, then just return True
    if ucount > 0:
        return True

    # If not exist, try to pull user from auth providers
    if email_login:
        return auth_providers.pull(email=login) is not None
    else:
        return auth_providers.pull(name=login) is not None


#: The global :class:`AuthProviderSet` registry instance.
auth_providers = AuthProviderSet()
