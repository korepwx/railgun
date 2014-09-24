#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/models.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

from datetime import datetime

from babel.dates import UTC
from flask.ext.babel import gettext, get_locale
from werkzeug.security import generate_password_hash, check_password_hash

from railgun.common.dateutil import from_plain_date, to_plain_date
from .context import db, app

# define the states of all handins
_ = lambda s: s
HANDIN_STATES = (_('Pending'), _('Running'), _('Rejected'), _('Accepted'))


class User(db.Model):
    __tablename__ = 'users'

    # Table arguments. Inrecognized arguments will be ignored by certain
    # database engine.
    __table_args__ = {'mysql_engine': 'InnoDB'}

    # Primary key of the table
    id = db.Column(db.Integer, db.Sequence('user_id_seq'), primary_key=True)

    # Which authenticate provider does this user come from?
    # If None or empty, this user does not come from external providers.
    provider = db.Column(db.String(32), default='')

    # User passport
    name = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(255))

    # Whether this user is admin?
    is_admin = db.Column(db.Boolean, default=False)

    # User detail information
    given_name = db.Column(db.String(64), default='')
    family_name = db.Column(db.String(64), default='')

    # Language and timezone of this user
    locale = db.Column(db.String(16), default=app.config['DEFAULT_LOCALE'])
    timezone = db.Column(db.String(32), default=app.config['DEFAULT_TIMEZONE'])

    # Relationship between User and final score records
    scores = db.relationship('FinalScore')

    # Basic model object interfaces
    def __repr__(self):
        return "<User(%s)>" % (self.name)

    # Password should be stored as salted hash text. These methods provide
    # updating and validation of the password
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def gather_scores(self):
        """Gather dict(hwid => score) of this user."""
        return {sc.hwid: sc.score for sc in self.scores}

    # Initialize the locale and timezone from request
    def fill_i18n_from_request(self):
        """Initialize i18n from request when createing a new user."""
        self.locale = str(get_locale())
        # TODO: detect timezone from request


class FinalScore(db.Model):
    __tablename__ = 'finalscore'

    # Table arguments. Inrecognized arguments will be ignored by certain
    # database engine.
    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = db.Column(db.Integer, db.Sequence('finalscore_id_seq'),
                   primary_key=True)

    # db.ForeignKey to the User
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # associated with certain homework
    hwid = db.Column(db.String(32), index=True)

    # the final score of such homework
    score = db.Column(db.Float, default=0.0)

    # Basic model object interfaces
    def __repr__(self):
        return ("<FinalScore(uid=%d,hwid=%s,score=%f)>" %
                (self.user_id, self.hwid, self.score))


class Handin(db.Model):
    __tablename__ = 'handins'

    # Table arguments. Inrecognized arguments will be ignored by certain
    # database engine.
    __table_args__ = {'mysql_engine': 'InnoDB'}

    # We use uuid to seek particular Handin, but we maintain an integral id.
    # This is because some databases lack a full support for UUIDs.
    id = db.Column(db.Integer, db.Sequence('handin_id_seq'), primary_key=True)
    uuid = db.Column(db.String(32), unique=True)

    # We store datetime in UTC anyway. But we do not store the timestamp
    # in database.
    ctime = db.Column(db.DateTime, default=lambda: datetime.utcnow())

    # A handin is associated with certain homework and programming language
    hwid = db.Column(db.String(32), index=True)
    lang = db.Column(db.String(32))

    # There should be states of handins:
    state = db.Column(db.Enum(*HANDIN_STATES), default='Pending', index=True)

    # The result of given handin should include score, scale, run_time,
    # brief report and detailed report
    #
    # the brief report and detailed report should be lazy_gettext instance,
    # so we should use db.PickleType to store these reports
    score = db.Column(db.Float, default=0.0)
    scale = db.Column(db.Float, default=0.0)

    # handin result text
    result = db.Column(db.PickleType)

    # field for compile errors
    compile_error = db.Column(db.PickleType, default=None)

    # the exit code of the handin
    exitcode = db.Column(db.Integer)

    # the stdout of the handin
    stdout = db.Column(db.Text)

    # the stderr of the handin
    stderr = db.Column(db.Text)

    # list of HwPartialScore instance to record more details about this handin
    partials = db.Column(db.PickleType)

    # db.ForeignKey to the User
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Fast access to user
    user = db.relationship('User')

    # Basic model object interface
    def __repr__(self):
        return '<Handin(%s)>' % self.uuid

    def get_ctime(self):
        """Get the ctime with UTC tzinfo"""
        return from_plain_date(self.ctime, UTC)

    def set_ctime(self, ctime):
        """Set UTC `ctime` with no tzinfo"""
        self.ctime = to_plain_date(ctime)

    def get_state(self):
        """Get translated state name"""
        return gettext(self.state)

    def is_accepted(self):
        """Whether this handin has been accepted?"""
        return self.state == 'Accepted'

    def get_result(self):
        """Get the localized version of result."""
        return unicode(self.result) if self.result else u''

    def get_stdout(self):
        """Get the localized version of stdout."""
        return unicode(self.stdout) if self.stdout else u''

    def get_stderr(self):
        """Get the localized version of stderr."""
        return unicode(self.stderr) if self.stderr else u''

    def get_compile_error(self):
        """Get the localized version of compile error."""
        return unicode(self.compile_error) if self.compile_error else u''

db.create_all()
