#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/utility.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

from datetime import datetime

from markdown import markdown
from flask import g
from flask.ext.babel import gettext as _
from babel.dates import format_timedelta

from .context import app


# hw.info.desc should be formatted by markdown parser
# so inject such filter into Jinja2 template
@app.template_filter(name='markdown')
def __inject_markdown_filter(text):
    return markdown(
        text=text,
        output_format='xhtml1',
        extensions=[
            'extra',
            'tables',
            'smart_strong',
            'codehilite',
            'nl2br',
            'toc',
            'fenced_code',
        ]
    )


# format datetime object or timedelta object into timedelta string.
# if given paramter is datetime object, it will be compared to g.utcnow
@app.template_filter(name='timedelta')
def __inject_template_timedelta(o):
    if (isinstance(o, datetime)):
        o = o - g.utcnow
    return format_timedelta(o)


# format size into human readable string
@app.template_filter(name='sizeformat')
def __inject_template_sizeformat(size):
    if (not size):
        return None
    if (size > 1e9):
        return _('%(size).2fG', size=size / (1024.0 * 1024.0 * 1024.0))
    if (size > 1e6):
        return _('%(size).2fM', size=size / (1024.0 * 1024.0))
    if (size > 1e3):
        return _('%(size).2fK', size=size / 1024.0)
    return _('%(size)dB', size=int(size))


# get a suitable bootstrap class name according to time delta
@app.template_filter(name='duestyle')
def __inject_template_duestyle(delta_or_date):
    if (isinstance(delta_or_date, datetime)):
        delta_or_date = delta_or_date - g.utcnow
    # exam the time delta through absolute second count
    totsec = delta_or_date.total_seconds()
    # if delta <= 0, we should report 'danger'
    if (totsec <= 0):
        return 'danger'
    # if delta <= 3days, we should report 'warning'
    if (totsec <= 3 * 86400):
        return 'warning'
    # otherwise we should report all right
    return 'success'


# get a suitable bootstrap class name according to scale
@app.template_filter(name='scalestyle')
def __inject_template_scalestyle(scale):
    if (scale >= 1.0 - 1e-6):
        return 'success'
    if (scale >= 0.5):
        return 'warning'
    return 'danger'
