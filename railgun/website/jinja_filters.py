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


@app.template_filter('timedelta')
def timedelta_filter(delta_or_date):
    """Format :class:`~datetime.datetime` or :class:`~datetime.timedelta`
    into localized string.

    If given parameter is a :class:`~datetime.datetime`,
    it will be subtracted by :func:`railgun.common.dateutil.utcnow` to
    get the :class:`~datetime.timedelta`.

    Usage:

    .. code-block:: html

        {{ handin.get_ctime() | timedelta }}

    :param delta_or_date: A :class:`~datetime.datetime` or a
        :class:`~datetime.timedelta` object.
    :return: :token:`None` if `delta_or_date` is :token:`None`, otherwise the
        localized timedelta string.
    """

    if not delta_or_date:
        return None
    if isinstance(delta_or_date, datetime):
        delta_or_date = delta_or_date - g.utcnow
    return format_timedelta(delta_or_date, locale=get_locale())


@app.template_filter('sizeformat')
def sizeformat_filter(size):
    """Get a human readable string of the given size in bytes.
    Refer to :func:`~railgun.website.utility.format_size` for more details.

    Usage:

    .. code-block:: html

        <span>The attachment size is : {{ attach_size | sizeformat }}</span>

    :param size: Given size in bytes.
    :type size: :class:`int`
    :return: A human readable string to represent the size.
    """
    return format_size(size)


@app.template_filter('duecolor')
def duecolor_filter(delta_or_date):
    """Get a color to describe the emergency of given due date.

    If the deadline is within 3 days, the filter will return a color between
    green and red.  The closer the deadline, the redder the color.

    Usage:

    .. code-block:: html

        <span style="color: {{ next_deadline | duecolor }}">...</span>

    :param delta_or_date: A :class:`~datetime.datetime` or a
        :class:`~datetime.timedelta` object.
    :return: An html color string, for example, "#ffffff".
    """
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


@app.template_filter('scalecolor')
def scalecolor_filter(scale):
    """Get a color to describe the emergency of given score scale.

    The closer the `scale` is to 1.0, the greener the color should be.
    Refer to :func:`~railgun.website.utility.float_color` for more details.

    Usage:

    .. code-block:: html

        <span style="color: {{ deadline.scale | scalecolor }}">...</span>

    :param scale: The value of score scale.
    :type scale: :class:`float`
    :return: An html color string, for example, "#ffffff".
    """
    return float_color(scale)


@app.template_filter('scorecolor')
def scorecolor_filter(score):
    """Get a color to describe the ranking of score.

    The closer the `score` is to 100, the greener the color should be.
    Refer to :func:`~railgun.website.utility.float_color` for more details.

    Usage:

    .. code-block:: html

        <span style="color: {{ handin.score | scorecolor }}">...</span>

    :param score: The value of score.
    :type score: :class:`float`
    :return: An html color string, for example, "#ffffff".
    """
    return float_color(score / 100.0)


@app.template_filter('handinstyle')
def handinstyle_filter(state):
    """Get a bootstrap class name to describe the submission state.
    The relationships between submission state and bootstrap class name
    are:

    =============== ====================================
    State           Class Name
    =============== ====================================
    Pending         .warning
    Running         .info
    Rejected        .danger
    Accepted        .success
    =============== ====================================

    :param state: The submission state.
    :type state: :class:`str`
    :return: The bootstrap class name.
    """
    return {
        'Pending': 'warning',
        'Running': 'info',
        'Rejected': 'danger',
        'Accepted': 'success',
    }.get(state, 'default')


@app.template_filter('roundscore')
def roundscore_filter(score):
    """Get the closest number to given score, whose precision is 0.1.

    :param score: The given score in floating number.
    :type score: :class:`float`
    :return: The rounded score.
    """
    return round_score(score)


@app.template_filter('cssclass')
def cssclass_filter(s):
    """Replace invalid characters in given text so that it can be used as a
    css class name.

    :param s: The given text.
    :type s: :class:`str`
    :return: The processed css class name.
    """
    return s.replace('.', '_')


@app.template_filter('codelang')
def codelang_filter(s):
    """Get the translated name for given programming language.

    If the given language name could not be understood, return the original
    language identifier.  Here are some examples::

        >>> {{ 'python' | codelang }}
        'Python'

        >>> {{ 'unknown' | codelang }}
        'unknown'

    :param s: The identifier of programming language.
    :type s: :class:`str`
    """
    from .codelang import languages
    lang = languages.get(s, None)
    if lang:
        return lang.name
    return s


@app.template_filter('gravatar')
def gravatar_filter(user, size=24):
    """Get the gravatar url of given user.
    Refer to :func:`~railgun.website.utility.get_avatar` for more details.

    :param user: A user object with the `email` attribute, or an email string.
    :type user: :class:`object` or :class:`str`
    :param size: The requested avatar size.
    :type size: :class:`int`

    :return: The gravatar image url.
    """
    return get_avatar(user, size)


@app.template_filter(name='provider_name')
def provider_name_filter(name):
    """Get the translated name for a given authentication provider.

    If requested authentication provider not found, return the original
    identity name.  For example::

        >>> {{ 'csvfile' | provider_name }}
        'Csv文件'

        >>> {{ 'tsinghua' | provider_name }}
        '网络学堂'

        >>> {{ 'unknown' | provider_name }}
        'unknown'

    :param name: The identify name of authentication provider.
    :type name: :class:`str`
    """
    from .userauth import auth_providers
    p = auth_providers.get(name)
    if not p:
        return name
    return p.display_name()
