#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/models.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

"""Database models are defined with `SQLAlchemy <http://www.sqlalchemy.org>`_.
You may refer to `SQLAlchemy Object Relational Tutorial
<http://docs.sqlalchemy.org/en/latest/orm/tutorial.html>`_ to have a glance
at the usage of this library.
"""

import os
from datetime import datetime

from babel.dates import UTC
from flask.ext.babel import gettext, get_locale
from werkzeug.security import generate_password_hash, check_password_hash

from railgun.common.dateutil import from_plain_date, to_plain_date
from .context import db, app

# define the states of all handins
_ = lambda s: s

#: The tuple of possible submission states.
HANDIN_STATES = (_('Pending'), _('Running'), _('Rejected'), _('Accepted'))


class User(db.Model):
    """A user represents a registered account in Railgun."""

    __tablename__ = 'users'

    # Table arguments. Inrecognized arguments will be ignored by certain
    # database engine.
    __table_args__ = {'mysql_engine': 'InnoDB'}

    #: Primary key of the table
    id = db.Column(db.Integer, db.Sequence('user_id_seq'), primary_key=True)

    #: Which authentication provider does this user come from?
    #:
    #: An authentication provider is a third-party service that validates
    #: the login name and password, and provide account information if the
    #: user passes validation.
    #:
    #: :class:`railgun.website.TsinghuaAuthProvider` is the authentication
    #: provider to connect to Tsinghua account.  Other providers may connect
    #: to csv account files, or ldap account servers.
    #:
    #: :token:`None` or empty indicates that this user does not come from
    #: any external provider.
    provider = db.Column(db.String(32), default='')

    #: The user's login name, maximum 50 characters, unique among users.
    name = db.Column(db.String(50), unique=True)

    #: The user's email address, maximum 70 characters, unique among users.
    #:
    #: Note that some authentication providers may not give the user's email
    #: address.  Railgun will create a dummy email address like
    #: "[name]@not-a-email.secoder.net" for these users, and guide the user
    #: to fill in their actual email address at their first login.
    #:
    #: You may modify the suffix of dummy email addresses in
    #: ``config.EXAMPLE_USER_EMAIL_SUFFIX``.
    email = db.Column(db.String(80), unique=True)

    #: The hashed user password, maximum 255 characters.
    #: Users from third-party authentication providers will have :token:`None`
    #: in `password` field.
    password = db.Column(db.String(255))

    #: Is this user an administrator?
    is_admin = db.Column(db.Boolean, default=False)

    #: Is this user active?  If not active, the user will not be allowed to
    #: sign in the system.
    is_active = db.Column(db.Boolean, default=True)

    #: The user's given name, maximum 64 characters.
    given_name = db.Column(db.String(64), default='')

    #: The user's family name, maximum 64 characters.
    family_name = db.Column(db.String(64), default='')

    #: Locale name of this user.  It will be set to the browser locale
    #: name when a user is created.
    #: If browser locale is not known, it will be set to
    #: ``config.DEFAULT_LOCALE``.
    locale = db.Column(db.String(16), default=app.config['DEFAULT_LOCALE'])

    #: Timezone of this user.  It will be set to ``config.DEFAULT_TIMEZONE``
    #: when a user is created.
    timezone = db.Column(db.String(32), default=app.config['DEFAULT_TIMEZONE'])

    #: Refer to the final scores of this user on each homework assignment.
    scores = db.relationship('FinalScore')

    def __repr__(self):
        return "<User(%s)>" % (self.name)

    def set_password(self, password):
        """Update the hashed :attr:`password` by given plain text `password`.

        :param password: The plain text password.
        :type password: :class:`str`
        """
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """Validate the plain text `password`.

        Since all users from third-party users will store :token:`None`
        in this attribute, you may call
        :func:`railgun.website.userauth.authenticate` if you just want
        to validate a user login at a very high-level stage.  This method,
        however, is called mainly by the utilities in
        :mod:`railgun.website.userauth`.

        :param password: The plain text password.
        :type password: :class:`str`

        :return: True if `password` passes validation, False otherwise.
        """
        return check_password_hash(self.password, password)

    def gather_scores(self):
        """Collect the final scores for each homework belong to this user.

        :return: :class:`dict` of ("homework uuid" -> "final score").
        """
        return {sc.hwid: sc.score for sc in self.scores}

    def fill_i18n_from_request(self):
        """Fill :attr:`locale` and :attr:`timezone` according to current
        browser request.

        This method only works if it is called in a request context.
        """
        self.locale = str(get_locale())
        # TODO: detect timezone from request


class FinalScore(db.Model):
    """A final score stores the highest score among all submissions
    for a particular homework assignment belong to a given user.
    """

    __tablename__ = 'finalscore'

    # Table arguments. Inrecognized arguments will be ignored by certain
    # database engine.
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = db.Column(db.Integer, db.Sequence('finalscore_id_seq'),
                   primary_key=True)

    #: Link with the associated user, usually mapped to a foreign key.
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    #: Link with the associated homework.
    #:
    #: Since we do not have a homework table, we just store the uuid
    #: of the homework assignment.  Maximum 32 characters.
    hwid = db.Column(db.String(32), index=True)

    #: The final score value.
    score = db.Column(db.Float, default=0.0)

    def __repr__(self):
        return ("<FinalScore(uid=%d,hwid=%s,score=%f)>" %
                (self.user_id, self.hwid, self.score))


class Handin(db.Model):
    """A handin stores the information of a submission from user."""

    __tablename__ = 'handins'

    # Table arguments. Inrecognized arguments will be ignored by certain
    # database engine.
    __table_args__ = {'mysql_engine': 'InnoDB'}

    #: We use uuid to seek locate submissions, but we maintain an integral id,
    #: in that some databases do not support uuids, and most databases handle
    #: integral primary keys much faster than string uuids.
    id = db.Column(db.Integer, db.Sequence('handin_id_seq'), primary_key=True)

    #: The uuid of this submission, used almost everywhere in Railgun system.
    uuid = db.Column(db.String(32), unique=True)

    #: The creation time of this submission.
    #: Value of datetime is in UTC timezone, however, tzinfo is not stored.
    ctime = db.Column(db.DateTime, default=lambda: datetime.utcnow())

    #: Link with the associated homework.
    hwid = db.Column(db.String(32), index=True)

    #: The programming language of this submission, maximum 32 characters.
    lang = db.Column(db.String(32))

    #: The state of this submission.  One of the following states:
    #:
    #: ============ ==============================================
    #: State        Description
    #: ============ ==============================================
    #: Pending      The submission is waiting to be executed.
    #: Running      The submission is being executed.
    #: Accepted     The submission successfully executed.
    #: Rejected     Some error occurred executing the submission.
    #: ============ ==============================================
    state = db.Column(db.Enum(*HANDIN_STATES), default='Pending', index=True)

    #: The total score of this submission.  Usually the sum of all scorers.
    score = db.Column(db.Float, default=0.0)

    #: The score scale of this submission, determined by `ctime` and the
    #: deadline configurations of the homework.
    scale = db.Column(db.Float, default=0.0)

    #: The brief comment of this submission.
    #:
    #: Actual type should be :class:`railgun.common.lazy_i18n.GetTextString`,
    #: serialized by :mod:`pickle` and stored as byte sequence.
    result = db.Column(db.PickleType)

    #: The compiler error of this submission.
    #:
    #: Actual type should be :class:`railgun.common.lazy_i18n.GetTextString`,
    #: serialized by :mod:`pickle` and stored as byte sequence.
    compile_error = db.Column(db.PickleType, default=None)

    #: The program exit code of this submission.
    exitcode = db.Column(db.Integer)

    #: The program standard output of this submission.
    stdout = db.Column(db.Text)

    #: The program standard error output of this submission.
    stderr = db.Column(db.Text)

    #: List of scores from each scorer.
    #:
    #: Actual type is :class:`list` of `railgun.common.hw.HwPartialScore`,
    #: serialized by :mod:`pickle` and stored as byte sequence.
    partials = db.Column(db.PickleType)

    #: Link with the associated user, usually mapped to a foreign key.
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    #: Refer to the associated user object.
    user = db.relationship('User')

    # Basic model object interface
    def __repr__(self):
        return '<Handin(%s)>' % self.uuid

    def get_ctime(self):
        """Attach `UTC` timezone object to :attr:`ctime` and return the new
        datetime object.
        """
        return from_plain_date(self.ctime, UTC)

    def set_ctime(self, ctime):
        """Set :attr:`ctime` to the value of `ctime`, but dettach timezone."""
        self.ctime = to_plain_date(ctime)

    def get_state(self):
        """The state is stored as plain text in the database.  Get the
        translated version of the state text.
        """
        return gettext(self.state)

    def is_accepted(self):
        """Whether this handin has been accepted?"""
        return self.state == 'Accepted'

    def get_result(self):
        """The brief comment on this submission may be instance of
        :class:`railgun.common.lazy_i18n.GetTextString` or `None`.

        If we call ``unicode(result)`` to get the translated text, we may
        have the risk to get the literal of "None".
        This is a safe method to get empty string if :attr:`result`
        is `None`, or the translated text.
        """
        return unicode(self.result) if self.result else u''

    def get_stdout(self):
        """Safe method to get empty string if :attr:`stdout` is `None`, or the
        translated :attr:`stdout`.
        """
        return unicode(self.stdout) if self.stdout else u''

    def get_stderr(self):
        """Safe method to get empty string if :attr:`stderr` is `None`, or the
        translated :attr:`stderr`.
        """
        return unicode(self.stderr) if self.stderr else u''

    def get_compile_error(self):
        """Safe method to get empty string if :attr:`compile_error` is `None`,
        or the translated :attr:`compile_error`.
        """
        return unicode(self.compile_error) if self.compile_error else u''


# If the system uses SQL database, we try to create "db" directory.
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite://'):
    dpath = os.path.join(app.config['RAILGUN_ROOT'], 'db')
    if not os.path.isdir(dpath):
        os.makedirs(dpath)

db.create_all()
