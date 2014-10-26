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

from .models import User
from .context import app, db
from .userauth import auth_providers

# Initialize all the external auth providers
auth_providers.init_providers()

#: A :class:`flask.ext.login.LoginManager` object.  It extends the
#: :data:`~railgun.website.context.app` to support login & logout.
login_manager = LoginManager()
login_manager.init_app(app)


# A class to represent a logged user
class UserContext(object):
    """A mixin object to integrate into :mod:`flask.ext.login` framework.
    It provides the credential information in a request session.

    In addition to this, :class:`UserContext` also acts as a proxy to the
    associated :class:`~railgun.website.models.User` model object, in that
    you may read all the attributes of :class:`~railgun.website.models.User`
    just from this class, for example::

        >>> current_user.name
        'Alice'
        >>> current_user.dbo.name
        'Alice'

    Where the latter is what actually executed.

    However, :class:`UserContext` does not proxy write operations to the
    model object.  So if you wish to update the user's name, you must
    assign on `current_user.dbo.name` instead of `current_user.name`::

        current_user.dbo.name = 'Bob'
    """

    def __init__(self, user_dbo):
        """Create a `UserContext` object according to database object."""
        self.dbo = user_dbo

    def is_authenticated(self):
        """Is this an authenticated user?
        Since :class:`UserContext` will be constructed only for authenticated
        users, this method will always return :data:`True`.

        However, for users not authenticated, :mod:`flask.ext.login` will
        create an :class:`flask.ext.login.AnonymousUser` instance and store
        in :data:`flask.ext.login.current_user`.  This object will return
        :data:`False` when called the same method.

        So you may check the return value of `current_user.is_authenticated()`,
        to see whether some attributes can be accessed, for example:

        .. code-block:: html

            {% if current_user.is_authenticated() %}
                {% for score in current_users.scores %}
                    <p>The score for {{ score.hwid }} is: {{ score.score }}</p>
                {% endfor %}
            {% else %}
                <p>Please login first!</p>
            {% endif %}

        :return: :data:`True`
        """
        return True

    def is_active(self):
        """Whether this is an active user?
        Refer to :class:`~railgun.website.models.User` model for more details
        about this attribute.

        :return: A :class:`bool` indicating whether the user is active.
        """
        return self.dbo.is_active

    def is_anonymous(self):
        """Whether this is an anonymous user?
        Since :class:`UserContext` will be constructed only for authenticated
        users, this method will always return :data:`False`.

        :return: :data:`False`
        """
        return not self.is_authenticated()

    def get_id(self):
        """Get the id of :class:`~railgun.website.models.User` model object.

        :return: The id of this user.
        :rtype: :class:`unicode`
        """
        return unicode(self.dbo.id)

    # Proxy the read-only properties to database object
    def __getattr__(self, key):
        return getattr(self.dbo, key)


def should_update_email():
    """Check whether the current user has not set his or her email address.

    Some authentication providers may not give the email addresses.
    However, Railgun relies on email addresss to finish login process.
    So the users from these providers will be given `fake` email addresses.

    :class:`should_update_email` should be called before a view is executed,
    check whether the user should be redirected to
    :func:`~railgun.website.views.profile_edit` to fill in his or her
    email address.

    :return: :data:`True` if the user has a fake email address, :data:`False`
        otherwise.

    .. note::

        If the current view is :func:`~railgun.website.views.profile_edit`,
        this method will return :data:`False`.
    """
    if (current_user.email.endswith(app.config['EXAMPLE_USER_EMAIL_SUFFIX'])
            and request.endpoint != 'profile_edit'):
        return True


def redirect_update_email():
    """Redirect to :class:`~railgun.website.views.profile_edit` with a
    notificatio.
    """
    flash(_('You should update your email before start working!'),
          'warning')
    return redirect(url_for('profile_edit'))


def login_required(method):
    """A decorator on Flask view functions that validate whether the visitor
    is authenticated.

    If not authenticated, the request user will be redirected to
    :func:`~railgun.website.views.signin`.
    If :func:`should_update_email` returns :data:`True`, the request user will
    be redirected to :func:`~railgun.website.views.profile_edit`.

    Usage::

        @bp.route('/')
        @login_required
        def foo():
            return 'This page can only be accessed by authenticated users.'
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
    """A decorator on Flask view functions that validate whether the visitor
    is authenticated and the session is not stale.

    If not authenticated, the request user will be redirected to
    :func:`~railgun.website.views.signin`.
    If the session is stale, the request user will be redirected to
    :func:`~railgun.website.views.reauthenticate`.
    If :func:`should_update_email` returns :data:`True`, the request user will
    be redirected to :func:`~railgun.website.views.profile_edit`.

    Usage::

        @bp.route('/')
        @fresh_login_required
        def foo():
            return 'This page can only be accessed by fresh users.'
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
