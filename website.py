#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: website.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import os
import logging
from logging.handlers import RotatingFileHandler
from railgun.website.context import app


def init_log(app):
    handler = RotatingFileHandler(
        os.path.join(app.config['LOG_ROOT'], 'website.log'))
    handler.setLevel(logging.WARNING)
    app.logger.addHandler(handler)

# Whether the webserver runs individually or not, we should always init the log
init_log(app)


# We may run flask web server individually, or we may run through other
# interfaces like uWSGI. Only start the server when we start it as main.
if (__name__ == '__main__'):
    app.run()
