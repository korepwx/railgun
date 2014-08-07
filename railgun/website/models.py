#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/models.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Sequence
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    # User passport
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    name = Column(String(50), unique=True)
    email = Column(String(80), unique=True)
    password = Column(String(50))

    # Basic model object interfaces
    def __repr__(self):
        return "<User(%s)>" % (self.name)

    # Password should be stored as salted hash text. These methods provide
    # updating and validation of the password
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


def create_all(engine):
    """Initialize the SQLAlchemy models with given database engine."""
    Base.metadata.create_all(engine)
