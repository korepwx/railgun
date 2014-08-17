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
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, SelectField, BooleanField
from wtforms.widgets import TextArea
from wtforms.validators import DataRequired, Length, Email, InputRequired, \
    EqualTo, Regexp, URL, ValidationError
from babel import UnknownLocaleError
from pytz import timezone, UnknownTimeZoneError
from flask.ext.babel import Locale, lazy_gettext as _
from flask.ext.login import current_user

from .models import User
from .context import db
from .i18n import list_locales


class HandinTextArea(TextArea):
    """Text area that is customized to be put in Handin Form."""

    def __init__(self, rows=10):
        super(HandinTextArea, self).__init__()
        self.rows = rows

    def __call__(self, field, **kwargs):
        kwargs.setdefault('rows', self.rows)
        return super(HandinTextArea, self).__call__(field, **kwargs)


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

    def validate_name(form, field):
        if (db.session.query(User).filter(User.name == field.data).count()):
            raise ValidationError(_('Username already taken'))

    def validate_email(form, field):
        if (db.session.query(User).filter(User.email == field.data).count()):
            raise ValidationError(_('Email already taken'))


class SigninForm(Form):
    """Form for `signin` view."""

    login = StringField(_('Username or Email'), validators=[InputRequired()])
    password = PasswordField(_('Password'), validators=[InputRequired()])
    remember = BooleanField(_('Remember me?'))


def _MakeLocaleChoices():
    """Make choices of available locales."""
    return [(str(l), l.display_name) for l in list_locales()]


class ProfileForm(Form):
    """Form for `profile_edit` view."""

    # Passport fields
    email = StringField(_('Email Address'), validators=[
        DataRequired(message=_("Email can't be blank")),
        Email(message=_("Email is invalid")),
        Length(max=80, message=_("Email must be no longer than 80 characters")),
    ])
    password = PasswordField(_('Password'), validators=[
        EqualTo('confirm', message=_("Passwords must match")),
    ])
    confirm = PasswordField(_('Confirm your password'))

    # User profile
    given_name = StringField(_('Given Name'), validators=[
        Length(max=64, message=_("Given name must be no longer than 64 "
                                 "characters")),
    ])
    family_name = StringField(_('Family Name'), validators=[
        Length(max=64, message=_("Family name must be no longer than 64 "
                                 "characters")),
    ])

    # i18n fields
    locale = SelectField(
        _('Speaking Language'),
        choices=_MakeLocaleChoices(),
        validators=[
            DataRequired(message=_("Speaking language can't be blank")),
        ]
    )
    timezone = StringField(_('Timezone'), validators=[
        DataRequired(message=_("Timezone can't be blank")),
    ])

    # Get or set the user object assosicated with this form.
    @property
    def _the_user(self):
        return getattr(self, '_m_the_user', current_user)

    @_the_user.setter
    def _the_user(self, value):
        self._m_the_user = value

    # Special inline validators on email and password
    def validate_email(form, field):
        if (db.session.query(User).
                filter(User.email == field.data).
                filter(User.id != form._the_user.id).
                count()):
            raise ValidationError(_('Email already taken'))

    def validate_password(form, field):
        pwd_len = len(field.data)
        if (field.data and (pwd_len < 7 or pwd_len > 32)):
            raise ValidationError(
                _("Password must be no shorter than 7 and no longer than "
                  "32 characters")
            )

    def validate_locale(form, field):
        try:
            Locale(field.data)
        except UnknownLocaleError:
            raise ValidationError(_("Please select a valid locale from above."))

    def validate_timezone(form, field):
        try:
            timezone(field.data)
        except UnknownTimeZoneError:
            raise ValidationError(_("Please enter a valid timezone."))


class AdminUserEditForm(ProfileForm):
    """Form for `admin.user_edit` view."""

    is_admin = BooleanField(_('Is administrator?'))


class UploadHandinForm(Form):
    """Form for `homework` view that uploads an archive."""

    handin = FileField(
        _('Please choose an archive to submit:'),
        validators=[
            FileRequired(),
            FileAllowed(
                ['rar', 'zip', 'tar', 'tgz', 'tbz', 'gz', 'bz2'],
                message=_('Only these file formats are accepted: '
                          'rar, zip, tar, tar.gz, tgz, tar.bz2, tbz')
            )
        ])


class AddressHandinForm(Form):
    """Form for `homework` view that handin an address."""

    address = StringField(
        _('Please enter your API address:'),
        validators=[
            InputRequired(),
            URL(message=_('Please input a valid url address!'),
                require_tld=False)
        ])


class CsvHandinForm(Form):
    """Form form `homework` view that handin a CSV file."""

    csvdata = StringField(
        _('Csv data:'),
        validators=[InputRequired()],
        widget=HandinTextArea()
    )
