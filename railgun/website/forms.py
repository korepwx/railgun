#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/forms.py
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
from .context import db, app
from .i18n import list_locales
from .utility import format_size
from .userauth import has_user


class MultiRowsTextArea(TextArea):
    """HTML Text Area whose `rows` attribute can be set when define the
    :class:`~flask_wtf.Form` schema.

    :param rows: The `rows` attribute in HTML tag.
    :type rows: :class:`int`
    """

    def __init__(self, rows=10):
        super(MultiRowsTextArea, self).__init__()
        self.rows = rows

    def __call__(self, field, **kwargs):
        kwargs.setdefault('rows', self.rows)
        return super(MultiRowsTextArea, self).__call__(field, **kwargs)


class BaseForm(Form):

    def __init__(self, *args, **kwargs):
        super(self, BaseForm).__init__(*args, **kwargs)


class CreateUserForm(BaseForm):
    """The basic form to create a new user account.
    This form is used in :func:`~railgun.website.admin.adduser` view directly
    without modification.  Moreover, it is also derived by :class:`SignupForm`
    as a registration form for new users.
    """

    #: The username text input.  Valid pattern is ``[A-Za-z0-9_]``,
    #: minimum length is 3, and maximum length is 32.
    name = StringField(_('Username'), validators=[
        Regexp('^[A-Za-z0-9_]*$', message=_("Only letters, digits and '_' can "
                                            "appear in username.")),
        DataRequired(message=_("Username can't be blank")),
        Length(min=3, max=32, message=_("Username must be no shorter than 3 "
                                        "and no longer than 32 characters")),
    ])
    #: The password text input.  Minimum length is 7, and maximum length is 32.
    #: It must be equal to :attr:`confirm`.
    password = PasswordField(_('Password'), validators=[
        InputRequired(message=_("Password can't be blank")),
        EqualTo('confirm', message=_("Passwords must match")),
        Length(min=7, max=32, message=_("Password must be no shorter than 7 "
                                        "and no longer than 32 characters")),
    ])
    #: The password confirm text input.
    confirm = PasswordField(_('Confirm your password'))

    def validate_name(form, field):
        """Extra validation that the username has not been taken."""
        if has_user(field.data):
            raise ValidationError(_('Username already taken'))


class SignupForm(CreateUserForm):
    """The form for anonymous users to create a new account.  Derived from
    :class:`CreateUserForm`, used in :func:`~railgun.website.views.signup`.
    """

    #: The email address text input.  Input text must be a valid email
    #: address, and the maximum length is 80.
    email = StringField(_('Email Address'), validators=[
        DataRequired(message=_("Email can't be blank")),
        Email(message=_("Email is invalid")),
        Length(message=_("Email must be no longer than 80 characters"),
               max=80),
    ])

    def validate_email(form, field):
        """Extra validation that the email has not been taken."""
        if has_user(field.data):
            raise ValidationError(_('Email already taken'))


class SigninForm(BaseForm):
    """The form for users to sign in.
    Used in :func:`~railgun.website.views.signin`.
    """

    #: Username or email address text input.
    login = StringField(_('Username or Email'), validators=[InputRequired()])
    #: Password text input.
    password = PasswordField(_('Password'), validators=[InputRequired()])
    #: The checkbox indicating whether to make the user session persistent.
    #: A persistent session can live alive even after the user quits his or
    #: her web browser.
    remember = BooleanField(_('Remember me?'))


class ReAuthenticateForm(BaseForm):
    """The form for users to re-validate themselves by enter their passwords.
    Used in :func:`~railgun.website.views.reauthenticate`.
    """

    #: Password text input.
    password = PasswordField(_('Password'), validators=[InputRequired()])


def _MakeLocaleChoices():
    """Prepare data of available locales for :class:`~wtforms.SelectField`."""
    return [(str(l), l.display_name) for l in list_locales()]


class ProfileForm(BaseForm):
    """The form to edit a user's profile.
    Used in :func:`~railgun.website.views.profile_edit` directly, and is
    derived by :class:`AdminUserEditForm` for admins to edit user profiles.

    Some fields in this form should be disabled, since users from third-party
    authentication providers may not allow to change these fields.
    You may refer to :class:`railgun.website.userauth.AuthProvider` for more
    details.
    """

    #: The email address text input.  Input text must be a valid email
    #: address, and the maximum length is 80.
    email = StringField(_('Email Address'), validators=[
        DataRequired(message=_("Email can't be blank")),
        Email(message=_("Email is invalid")),
        Length(message=_("Email must be no longer than 80 characters"),
               max=80),
    ])
    #: The password text input.  Minimum length is 7, and maximum length is 32.
    #: It must be equal to :attr:`confirm`.
    password = PasswordField(_('Password'), validators=[
        EqualTo('confirm', message=_("Passwords must match")),
    ])
    #: The password confirm text input.
    confirm = PasswordField(_('Confirm your password'))

    #: The given name text input.  Maximum length is 64.
    given_name = StringField(_('Given Name'), validators=[
        Length(max=64, message=_("Given name must be no longer than 64 "
                                 "characters")),
    ])
    #: The family name text input.  Maximum length is 64.
    family_name = StringField(_('Family Name'), validators=[
        Length(max=64, message=_("Family name must be no longer than 64 "
                                 "characters")),
    ])

    #: The language select field input.  Only the languages with translations
    #: installed are listed here.
    locale = SelectField(
        _('Speaking Language'),
        choices=_MakeLocaleChoices(),
        validators=[
            DataRequired(message=_("Speaking language can't be blank")),
        ]
    )
    #: The timezone text input.
    timezone = StringField(_('Timezone'), validators=[
        DataRequired(message=_("Timezone can't be blank")),
    ])

    @property
    def the_user(self):
        """Get the user object associated with this form.  Default is
        :data:`~flask.ext.login.current_user`.
        """
        return getattr(self, '_m_the_user', current_user)

    @the_user.setter
    def the_user(self, value):
        """Set the user object associated with this form."""
        self._m_the_user = value

    # Special inline validators on email and password
    def validate_email(form, field):
        """Extra validation that the email has not been taken.

        .. note::

            Email addresses ends with ``config.EXAMPLE_USER_EMAIL_SUFFIX``
            is not allowed.

        .. note::

            We need :attr:`the_user` to get associated user id, since we
            should allow the user to keep his or her email not changed,
            we then allow the user with same user id in the database
            has the same email address.
        """
        if (db.session.query(User).
                filter(User.email == field.data).
                filter(User.id != form.the_user.id).
                count()):
            raise ValidationError(_('Email already taken'))
        if (field.data and
                field.data.endswith(app.config['EXAMPLE_USER_EMAIL_SUFFIX'])):
            raise ValidationError(_('You should provide a valid email.'))

    def validate_password(form, field):
        """Validate whether the password length is within 7 and 32 characters.

        We move the validations of password from general validators to
        customized method, in that we may allow the user to keep the password
        input empty, which means to keep password unchanged.
        """
        pwd_len = len(field.data)
        if field.data and (pwd_len < 7 or pwd_len > 32):
            raise ValidationError(
                _("Password must be no shorter than 7 and no longer than "
                  "32 characters")
            )

    def validate_locale(form, field):
        """Validate whether the user provided locale is a valid locale."""
        try:
            Locale(field.data)
        except UnknownLocaleError:
            raise ValidationError(
                _("Please select a valid locale from above."))

    def validate_timezone(form, field):
        """Validate whether the user provided timezone is a valid timezone.
        Lists of valid timezones can be found on `Wikipedia
        <http://en.wikipedia.org/wiki/List_of_tz_database_time_zones>`_
        """
        try:
            timezone(field.data)
        except UnknownTimeZoneError:
            raise ValidationError(_("Please enter a valid timezone."))


class AdminUserEditForm(ProfileForm):
    """Derived from :class:`ProfileForm`, allow admins to edit a user's
    profile.  The only additional widget is :attr:`is_admin`.
    Used in :func:`~railgun.website.admin.user_edit`, where
    :attr:`~ProfileForm.the_user` would be set.
    """

    #: Checkbox input representing whether the user is an administrator.
    is_admin = BooleanField(_('Is administrator?'))


class UploadHandinForm(BaseForm):
    """The form for users to upload archive files as submissions."""

    #: File upload input.  Only archive files are allowed.
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

    def validate_handin(form, field):
        """Extra validation on :attr:`handin` that the uploaded file
        must not be larger than ``config.MAX_SUBMISSION_SIZE``.
        """
        if not field.data:
            return
        # try to get the file size of uploaded file
        field.data.stream.seek(0, 2)
        fsize = field.data.stream.tell()
        field.data.stream.seek(0)
        if fsize > app.config['MAX_SUBMISSION_SIZE']:
            raise ValidationError(_(
                "Archive files larger than %(size)s is not allowed.",
                size=format_size(app.config['MAX_SUBMISSION_SIZE'])
            ))


class AddressHandinForm(BaseForm):
    """The form for users to give url addresses as submissions."""

    #: The url address text input.  Must be valid url addresses.
    address = StringField(
        _('Please enter your API address:'),
        validators=[
            InputRequired(),
            URL(message=_('Please input a valid url address!'),
                require_tld=False)
        ])


class CsvHandinForm(BaseForm):
    """The form for users to give CSV data as submissions."""

    #: The CSV data text area.  Use :class:`MultiRowsTextArea` as the
    #: widget so that `rows` are defined.
    csvdata = StringField(
        _('Csv data:'),
        validators=[InputRequired()],
        widget=MultiRowsTextArea()
    )
