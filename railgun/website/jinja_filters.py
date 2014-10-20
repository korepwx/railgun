#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/jinja_filters.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.


from datetime import datetime

from flask import g
from flask.ext.babel import get_locale
from babel.dates import format_timedelta

from .context import app
from .utility import *


# format datetime object or timedelta object into timedelta string.
# if given paramter is datetime object, it will be compared to g.utcnow
@app.template_filter
def timedelta(o):
    if not o:
        return None
    if isinstance(o, datetime):
        o = o - g.utcnow
    return format_timedelta(o, locale=get_locale())


# format size into human readable string
@app.template_filter
def sizeformat(size):
    return format_size(size)


# get a suitable bootstrap class name according to time delta
@app.template_filter
def duecolor(delta_or_date):
    if not delta_or_date:
        return None
    if isinstance(delta_or_date, datetime):
        delta_or_date = delta_or_date - g.utcnow
    # exam the time delta through absolute second count
    val = delta_or_date.total_seconds() / (3.0 * 86400)
    if val < 0.0:
        val = 0.0
    if val > 1.0:
        val = 1.0
    # get the color of this time delta
    return float_color(val)


# get a suitable bootstrap class name according to scale
@app.template_filter
def scalecolor(scale):
    return float_color(scale)


# get a suitable bootstrap class name according to score
@app.template_filter
def scorecolor(score):
    return float_color(score / 100.0)


# get a suitable bootstrap "tr" class name according to handin state
@app.template_filter
def handinstyle(state):
    return {
        'Pending': 'warning',
        'Running': 'info',
        'Rejected': 'danger',
        'Accepted': 'success',
    }.get(state, 'default')


# Round score number to 0.1 precision
@app.template_filter
def roundscore(score):
    return round_score(score)


# Regular generated class name for css
@app.template_filter
def cssclass(s):
    return s.replace('.', '_')
