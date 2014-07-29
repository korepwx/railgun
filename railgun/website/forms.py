#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/forms.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

from flask_wtf import Form
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length, Email, InputRequired, \
    EqualTo, Regexp

from flask.ext.babel import lazy_gettext as _


class SignupForm(Form):
    """Form for `signup` view."""

    name = StringField(_('Username'), validators=[
        Regexp('^[A-Za-z0-9_]*$', message=_("Only letters, digits and '_' can "
                                            "appear in username.")),
        DataRequired(message=_("Username can't be blank")),
        Length(min=3, max=32, message=_("Username must be no shorter than 3 "
                                        "and no longer than 32 characters")),
    ])
    email = StringField(_('Email Address'), validators=[
        DataRequired(message=_("Email can't be blank")),
        Email(message=_("Email is invalid")),
        Length(max=80, message=_("Email must be no longer than 80 characters")),
    ])
    password = PasswordField(_('Password'), validators=[
        InputRequired(message=_("Password can't be blank")),
        EqualTo('confirm', message=_("Passwords must match")),
        Length(min=7, max=32, message=_("Password must be no shorter than 7 "
                                        "and no longer than 32 characters")),
    ])
    confirm = PasswordField(_('Confirm your password'))


class SigninForm(Form):
    """Form for `signin` view."""

    login = StringField(_('Username or Email'), validators=[InputRequired()])
    password = PasswordField(_('Password'), validators=[InputRequired()])
