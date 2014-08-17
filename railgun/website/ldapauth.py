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
from .webconfig import LDAP_ADMIN_DN, LDAP_URL, LDAP_ADMIN_KEY, LDAP_BASE_DN, \
    LDAP_RAILGUN_ADMIN_GROUP_DN
from .models import User
from .context import db, app
from .userauth import auth_providers


class LdapAuthProvider(AuthProvider):

    '''LDAP user authentication provider.'''

    def __init__(self, name):
        '''Initialize LDAP using config in webconfig.'''
        AuthProvider.__init__(self, name)
        self.__adapter = LdapEntryAdapter()

    def __del__(self):
        del self.__adapter

    def pull(self, auth_request, dbuser):
        admin_group = self.__adapter.query_admin_group()
        if auth_request.email_login:
            ldap_user = self.__adapter.query_by_mail(auth_request.login)
        else:
            ldap_user = self.__adapter.query_by_uid(auth_request.login)

        if not (ldap_user and self.__adapter.authenticate(ldap_user, auth_request.password)):
            return None

        user = ldap_user.to_user(admin_group)
        # Create new dbuser from LDAP user
        if dbuser is None:
            try:
                dbuser = User(
                    name=user.name, email=user.email, password=None,
                    is_admin=user.is_admin,
                    provider=self.name
                )
            except Exception:
                dbuser = None
                self._log_pull(user, create=True, exception=True)
            return dbuser

        # Update existing user.
        # NOTE: uid is not modifiable
        fields = ['email', 'is_admin']
        updated = False
        for key in fields:
            if getattr(dbuser, key) != getattr(user, key):
                updated = True
                setattr(dbuser, key, getattr(user, key))
        if updated:
            try:
                db.session.commit()
                self._log_pull(user, create=False)
            except Exception:
                dbuser = None
                self._log_pull(user, create=False, exception=True)
        return dbuser

    def push(self, dbuser, password=None):
        if password:
            encrypt = self.__adapter.make_password(password)
            self.__adapter.modify(dbuser.name, mail=dbuser.email, userPassword=encrypt)
        else:
            self.__adapter.modify(dbuser.name, mail=dbuser.email)


class Bundle(object):

    '''A class just for store attributes.'''
    pass


class LdapEntry(object):

    def __init__(self, attrs):
        for key in attrs:
            setattr(self, key, attrs[key])

    def to_user(self, ldap_group):
        user = Bundle()
        user.name = self.uid[0]
        user.email = self.mail[0]
        user.is_admin = (ldap_group is None) \
            or (self.uid[0] in ldap_group.memberUid)
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

    def query_admin_group(self):
        results = self.conn.search_s(
            LDAP_RAILGUN_ADMIN_GROUP_DN, ldap.SCOPE_SUBORDINATE
        )
        if len(results) == 0:
            return None
        return LdapEntry(results[0][1])

    def authenticate(self, entry, password):
        pwd = entry.userPassword[0]
        pos = pwd.find('}')
        method = pwd[1:pos]
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

        return mod.verify(password, pwd)

    def query(self, filt):
        results = self.conn.search_s(LDAP_BASE_DN, ldap.SCOPE_SUBTREE, filt)
        if len(results) == 0:
            return None
        else:
            return LdapEntry(results[0][1])

    def modify(self, uid, **kwargs):
        ldap_user = self.query_by_uid(uid)
        if not ldap_user:
            raise RuntimeWarning('LDAP modify failed: no such user(%s)!' % uid)
            return

        old = dict()
        new = dict()
        for key in kwargs:
            old[key] = getattr(ldap_user, key)[0]
            new[key] = kwargs[key]

        ldif = ldap.modlist.modifyModlist(old, new)
        self.conn.modify_s(ldap.filter.filter_format('uid=%s,' + LDAP_BASE_DN, (uid,)), ldif)

    def make_password(self, password):
        return ldap_salted_sha1.encrypt(password, salt_size=4)

if (app.config['LDAP_AUTH_ENABLED']):
    auth_providers.add(LdapAuthProvider('LDAP'))
