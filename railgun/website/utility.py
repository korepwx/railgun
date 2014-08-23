#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/utility.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import colorsys
from datetime import datetime

from flask import g
from flask.ext.babel import get_locale
from flask.ext.babel import gettext as _
from babel.dates import format_timedelta

from .context import app


def float_color(v):
    """Get a color to describe the float `v`.

    When `v` is close to 1.0 the color will be close to green,
    and when `v` is close to 0.0 the color will be close to red.

    Args:
        v (float): The float number in range [0.0, 1.0].

    Returns:
        An HTML color string, for example "#ffffff".
    """

    h = v / 3.0
    l = 0.3
    s = 1.0
    rgb = map((lambda i: int(i * 255)), colorsys.hls_to_rgb(h, l, s))
    return '#%02X%02X%02X' % tuple(rgb)


def format_size(size):
    """Format `size` into human readable string.

    Args:
        size (int): Integral file size in bytes.

    Returns:
        A human readable string to represent the `size`.
    """

    if (not size):
        return None
    if (size > 1e9):
        return _('%(size).2fG', size=size / (1024.0 * 1024.0 * 1024.0))
    if (size > 1e6):
        return _('%(size).2fM', size=size / (1024.0 * 1024.0))
    if (size > 1e3):
        return _('%(size).2fK', size=size / 1024.0)
    return _('%(size)dB', size=int(size))


def round_score(score):
    """Round `score` to closest float whose precision is 0.1.

    Args:
        score (float): Score of floating number.

    Returns:
        Rounded score number.
    """

    return round(score * 10) * 0.1


# format datetime object or timedelta object into timedelta string.
# if given paramter is datetime object, it will be compared to g.utcnow
@app.template_filter(name='timedelta')
def __inject_template_timedelta(o):
    if (not o):
        return None
    if (isinstance(o, datetime)):
        o = o - g.utcnow
    return format_timedelta(o, locale=get_locale())


# format size into human readable string
@app.template_filter(name='sizeformat')
def __inject_template_sizeformat(size):
    return format_size(size)


# get a suitable bootstrap class name according to time delta
@app.template_filter(name='duecolor')
def __inject_template_duecolor(delta_or_date):
    if (not delta_or_date):
        return None
    if (isinstance(delta_or_date, datetime)):
        delta_or_date = delta_or_date - g.utcnow
    # exam the time delta through absolute second count
    val = delta_or_date.total_seconds() / (3.0 * 86400)
    if (val < 0.0):
        val = 0.0
    if (val > 1.0):
        val = 1.0
    # get the color of this time delta
    return float_color(val)


# get a suitable bootstrap class name according to scale
@app.template_filter(name='scalecolor')
def __inject_template_scalecolor(scale):
    return float_color(scale)


# get a suitable bootstrap class name according to score
@app.template_filter(name='scorecolor')
def __inject_template_scorecolor(score):
    return float_color(score / 100.0)


# get a suitable bootstrap "tr" class name according to handin state
@app.template_filter(name='handinstyle')
def __inject_template_handinstyle(state):
    return {
        'Pending': 'warning',
        'Running': 'info',
        'Rejected': 'danger',
        'Accepted': 'success',
    }.get(state, 'default')


# Round score number to 0.1 precision
@app.template_filter(name='roundscore')
def __inject_template_roundscore(score):
    return round_score(score)


# Regular generated class name for css
@app.template_filter(name='cssclass')
def __inject_template_cssclass(s):
    return s.replace('.', '_')
