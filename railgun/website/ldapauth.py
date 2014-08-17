#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/userauth.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   Dawei Yang           <davy.pristina@gmail.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

from passlib.hash import ldap_salted_sha1, ldap_salted_md5, ldap_md5, \
    ldap_sha1, ldap_plaintext
import ldap
import ldap.filter
import ldap.modlist

from .userauth import AuthProvider
from .webconfig import LDAP_ADMIN_DN, LDAP_URL, LDAP_ADMIN_KEY, LDAP_BASE_DN
from .models import User
from .context import db, app
from .userauth import auth_providers


class LdapAuthProvider(AuthProvider):

    '''LDAP user authentication provider.'''

    def __init__(self, name):
        '''Initialize LDAP using config in webconfig.'''
        AuthProvider.__init__(self, name)
        self.__adapter = LdapEntryAdapter()
        self.__interested_fields = ('email', 'given_name',
                                    'family_name')

    def __del__(self):
        del self.__adapter

    def hash_password(self, plain):
        return ldap_salted_sha1.encrypt(plain, salt_size=4)

    def check_password(self, hashed, plain):
        pos = hashed.find('}')
        method = hashed[1:pos]
        method_module = {
            'MD5': ldap_md5,
            'SMD5': ldap_salted_md5,
            'SHA': ldap_sha1,
            'SSHA': ldap_salted_sha1
        }
        if pos == -1:
            mod = ldap_plaintext
        else:
            mod = method_module[method]
        return mod.verify(plain, hashed)

    def pull(self, name=None, email=None, dbuser=None):
        # Fetch the user from LDAP server
        if (email):
            ldap_user = self.__adapter.query_by_mail(email)
        else:
            ldap_user = self.__adapter.query_by_uid(name)

        # Return None if user not exist on LDAP server
        if (not ldap_user):
            return None
        user = ldap_user.to_user()

        # Create new dbuser from LDAP user
        if (dbuser is None):
            try:
                dbuser = User(
                    name=user.name, email=user.email, password=None,
                    given_name=user.given_name,
                    family_name=user.family_name, provider=self.name)
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

        # Update existing user.
        # NOTE: uid is not modifiable, so we should assert it!
        if (dbuser.name != user.name):
            raise ValueError(
                'Username "%s" cannot be changed to "%s" as a LDAP user.' %
                (user.name, dbuser.name)
            )

        updated = False
        for key in self.__interested_fields:
            if getattr(dbuser, key) != getattr(user, key):
                updated = True
                setattr(dbuser, key, getattr(user, key))
        if (updated):
            try:
                db.session.commit()
                self._log_pull(user, create=False)
            except Exception:
                dbuser = None
                self._log_pull(user, create=False, exception=True)
        return (user, dbuser)

    def push(self, dbuser, password=None):
        if password:
            encrypt = self.hash_password(password)
            self.__adapter.modify(
                dbuser.name, mail=dbuser.email, givenName=dbuser.given_name,
                sn=dbuser.family_name, userPassword=encrypt
            )
        else:
            self.__adapter.modify(
                dbuser.name, mail=dbuser.email, givenName=dbuser.given_name,
                sn=dbuser.family_name
            )

    def init_form(self, form):
        self._init_form_helper(form, ('name', ))


class Bundle(object):

    '''A class just for store attributes.'''
    pass


def from_ldap_str(s):
    """Strings are stored as UTF-8 in LDAP server."""
    if (s is None):
        return None
    if (isinstance(s, unicode)):
        return s
    return unicode(s, 'utf-8')


def to_ldap_str(u):
    """Strings should be stored as UTF-8 in LDAP server."""
    if (u is None):
        return None
    if (not isinstance(u, unicode)):
        return str(u)
    return u.encode('utf-8')


class LdapEntry(object):

    def __init__(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

    def to_user(self):
        # Shortcut to fetch particular value from object and does not raise
        # exceptions if given key not found.
        getval = lambda k: getattr(self, k)[0] if hasattr(self, k) else None
        # Construct the user object
        user = Bundle()
        user.name = from_ldap_str(self.uid[0])
        user.email = from_ldap_str(self.mail[0])
        user.password = from_ldap_str(self.userPassword[0])
        user.given_name = from_ldap_str(getval('givenName'))
        user.family_name = from_ldap_str(getval('sn'))
        return user


class LdapEntryAdapter(object):

    '''LDAP operations encapsulation.'''

    def __init__(self):
        self.conn = ldap.initialize(LDAP_URL)
        self.conn.simple_bind_s(LDAP_ADMIN_DN, LDAP_ADMIN_KEY)

    def __del__(self):
        self.conn.unbind_s()

    def query_by_uid(self, uid):
        return self.query(ldap.filter.filter_format('uid=%s', (uid,)))

    def query_by_mail(self, mail):
        return self.query(ldap.filter.filter_format('mail=%s', (mail,)))

    def query(self, filt):
        results = self.conn.search_s(LDAP_BASE_DN, ldap.SCOPE_SUBTREE, filt)
        if len(results) == 0:
            return None
        else:
            return LdapEntry(**results[0][1])

    def modify(self, uid, **kwargs):
        ldap_user = self.query_by_uid(uid)
        if not ldap_user:
            raise KeyError('LDAP modify failed: no such user(%s)!' % uid)

        old = dict()
        new = dict()
        for key in kwargs:
            old[key] = getattr(ldap_user, key)[0]
            new[key] = to_ldap_str(kwargs[key])

        ldif = ldap.modlist.modifyModlist(old, new)
        self.conn.modify_s(
            ldap.filter.filter_format('uid=%s,' + LDAP_BASE_DN, (uid,)),
            ldif
        )

if (app.config['LDAP_AUTH_ENABLED']):
    auth_providers.add(LdapAuthProvider('ldap'))
