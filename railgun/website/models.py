#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/models.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Float, \
    PickleType, Enum, Sequence, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from babel.dates import UTC
from flask.ext.babel import gettext
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()

# define the states of all handins
_ = lambda s: s
HANDIN_STATES = (_('Pending'), _('Running'), _('Error'), _('Accepted'))


class User(Base):
    __tablename__ = 'users'

    # User passport
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    name = Column(String(50), unique=True)
    email = Column(String(80), unique=True)
    password = Column(String(50))

    # Relationship between User and Handin records
    handins = relationship('Handin')

    # Basic model object interfaces
    def __repr__(self):
        return "<User(%s)>" % (self.name)

    # Password should be stored as salted hash text. These methods provide
    # updating and validation of the password
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Handin(Base):
    __tablename__ = 'handins'

    # We use uuid to seek particular Handin, but we maintain an integral id.
    # This is because some databases lack a full support for UUIDs.
    id = Column(Integer, Sequence('handin_id_seq'), primary_key=True)
    uuid = Column(String(32), unique=True)

    # We store datetime in UTC anyway. But we do not store the timestamp
    # in database.
    ctime = Column(DateTime, default=datetime.utcnow())

    # A handin is associated with certain homework and programming language
    hwid = Column(String(32), index=True)
    lang = Column(String(32))

    # Options of this handin, set by `CodeLanguage.handle_upload`.
    options = Column(PickleType)

    # There should be states of handins:
    state = Column(Enum(*HANDIN_STATES), default='Pending', index=True)

    # The result of given handin should include score, scale, run_time,
    # brief report and detailed report
    #
    # the brief report and detailed report should be lazy_gettext instance,
    # so we should use PickleType to store these reports
    score = Column(Float)
    scale = Column(Float)
    run_time = Column(Float)
    brief_report = Column(PickleType)
    detail_report = Column(PickleType)

    # ForeignKey to the User
    user_id = Column(Integer, ForeignKey('users.id'))

    # Basic model object interface
    def __repr__(self):
        return '<Handin(%s)>' % self.uuid

    def get_ctime(self):
        """Get the ctime with UTC tzinfo"""
        return self.ctime.replace(tzinfo=UTC)

    def set_ctime(self, ctime):
        """Set UTC `ctime` with no tzinfo"""
        self.ctime = ctime.replace(tzinfo=None)

    def get_state(self):
        """Get translated state name"""
        return gettext(self.state)


def create_all(engine):
    """Initialize the SQLAlchemy models with given database engine."""
    Base.metadata.create_all(engine)
