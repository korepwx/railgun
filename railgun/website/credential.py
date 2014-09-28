#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/credential.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

from functools import wraps

from flask import redirect, flash, request, url_for
from flask.ext.login import LoginManager, current_user, login_fresh
from flask.ext.babel import gettext as _

from railgun.common.gravatar import get_avatar
from .models import User
from .context import app, db
from .userauth import auth_providers

# Initialize all the external auth providers
auth_providers.init_providers()

# The global login manager for web application
login_manager = LoginManager()
login_manager.init_app(app)


# A class to represent a logged user
class UserContext(object):

    def __init__(self, user_dbo):
        """Create a `UserContext` object according to database object."""
        self.dbo = user_dbo

    def is_authenticated(self):
        return True

    def is_active(self):
        return self.dbo.is_active

    def is_anonymous(self):
        return not self.is_authenticated()

    def get_id(self):
        return unicode(self.dbo.id)

    # Proxy the read-only properties to database object
    def __getattr__(self, key):
        return getattr(self.dbo, key)


def should_update_email():
    """Should the user be redirected to profile_edit and update his email?"""
    if (current_user.email.endswith(app.config['EXAMPLE_USER_EMAIL_SUFFIX'])
            and request.endpoint != 'profile_edit'):
        return True


def redirect_update_email():
    """Make a redirect response that update user email."""
    flash(_('You should update your email before start working!'),
          'warning')
    return redirect(url_for('profile_edit'))


def login_required(method):
    """Extend flask.ext.login.login_required, that the user must provide
    a valid email before using the system.
    """
    @wraps(method)
    def inner(*args, **kwargs):
        if not current_user.is_authenticated():
            return login_manager.unauthorized()
        if should_update_email():
            return redirect_update_email()
        return method(*args, **kwargs)
    return inner


def fresh_login_required(method):
    """Extend flask.ext.login.fresh_login_required, that the user must provide
    a valid email before using the system.
    """
    @wraps(method)
    def inner(*args, **kwargs):
        if not current_user.is_authenticated():
            return login_manager.unauthorized()
        if not login_fresh():
            return login_manager.needs_refresh()
        if should_update_email():
            return redirect_update_email()
        return method(*args, **kwargs)
    return inner


# Load the user object before processing request
@login_manager.user_loader
def __load_user_before_request(uid):
    ret = db.session.query(User).filter(User.id == uid).first()
    if ret and ret.is_active:
        return UserContext(ret)


# Inject current user into template
@app.context_processor
def __inject_template_context():
    return dict(
        current_user=current_user,
        allow_signup=app.config['ALLOW_SIGNUP']
    )


# Response to unauthorized requests
@login_manager.unauthorized_handler
def unauthorized_handler():
    flash(_('Please log in to access this page.'), 'danger')
    return redirect(url_for('signin', next=request.script_root + request.path))


# Response to need_refresh requests
@login_manager.needs_refresh_handler
def needs_refresh_handler():
    flash(_('To protect your account, please reauthenticate to access this '
            'page.'), 'info')
    return redirect(url_for('reauthenticate',
                            next=request.script_root + request.path))


# Inject `get_avatar` as `gravatar` filter into Jinja2 template engine.
app.template_filter('gravatar')(lambda user, size=24: get_avatar(user, size))
