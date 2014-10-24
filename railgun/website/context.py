#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/context.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import os
import logging.config

from flask import Flask
from flask_wtf.csrf import CsrfProtect
from flask.ext.sqlalchemy import SQLAlchemy

from . import webconfig

#: A :class:`~flask.Flask` object.  It implements a WSGI application and acts
#: as the central object of the website.
app = Flask(__name__)
app.config.from_object(webconfig)

# Initialize the logging according to webconfig
# NOTE: when DEBUG is on, I suppose that the user want to see logs directly
#       from console, so skip the logging configuration.
if not app.config['DEBUG']:
    dpath = os.path.split(app.config['LOG_FILE'])[0]
    if not os.path.isdir(dpath):
        os.makedirs(dpath, 0700)
    logging.config.dictConfig(app.config['WEBSITE_LOGGING'])

#: A :class:`flask_wtf.csrf.CsrfProtect` object.  It extends the
#: :data:`~railgun.website.context.app` so that all post requests will be
#: protected from csrf attack, unless disabled explicitly.
csrf = CsrfProtect(app)

#: A :class:`flask.ext.sqlalchemy.SQLAlchemy` object.  It extends the
#: :data:`~railgun.website.context.app` so that each request will bind
#: a database session.
db = SQLAlchemy(app)

# Create the debugging toolbar
if app.config['DEBUG'] and app.config.get('DEBUG_TOOLBAR', True):
    from flask_debugtoolbar import DebugToolbarExtension
    toolbar = DebugToolbarExtension(app)
