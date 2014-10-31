#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/utility.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import colorsys
import hashlib

from flask import request
from flask.ext.babel import to_user_timezone, gettext as _


def float_color(value):
    """Get a color to describe the safety level.

    Safety level should be a floating number in range [0.0, 1.0].
    The color will be more close to green if the safety level is more close
    to 1.0, and more close to red if level is more close to 0.0.

    :param value: The value of safety level.
    :type value: :class:`float`
    :return: An html color string, for example, "#ffffff".
    """

    h = value / 3.0
    l = 0.3
    s = 1.0
    rgb = map((lambda i: int(i * 255)), colorsys.hls_to_rgb(h, l, s))
    return '#%02X%02X%02X' % tuple(rgb)


def format_size(size):
    """Get a human readable string of the given size in bytes.

    Returns two-digit floating number with the size unit following, unless
    it is smaller than 1000B, the number part will be an integer.

    The conversion between size units is `1G = 1024M = 1048576K = 1073741824B`.
    However, if the size is larger than 10^3 the size of a smaller unit,
    it will be formatted as the larger unit.

    For example::

        >>> format_size(10)
        '10B'

        >>> format_size(1000)
        '0.98K'

        >>> format_size(1048576)
        '1.00M'

    :param size: Given size in bytes.
    :type size: :class:`int`
    :return: A human readable string to represent the size.
    """

    if not size:
        return None
    if size >= 1e9:
        return _('%(size).2fG', size=size / (1024.0 * 1024.0 * 1024.0))
    if size >= 1e6:
        return _('%(size).2fM', size=size / (1024.0 * 1024.0))
    if size >= 1e3:
        return _('%(size).2fK', size=size / 1024.0)
    return _('%(size)dB', size=int(size))


def round_score(score):
    """Get the closest number to given score, whose precision is 0.1.

    :param score: The given score in floating number.
    :type score: :class:`float`
    :return: The rounded score.
    """

    return round(score * 10) * 0.1


def get_avatar(user_or_email, size):
    """Get the gravatar url of given user.

    :param user_or_email: If it is a :class:`basestring`, representing the
        email address; otherwise it must carry an attribute `email`.
    :type user_or_email: :class:`basestring` or :class:`object`
    :param size: Size of avatar in pixels.
    :type size: :class:`int`

    :return: The url to the gavatar image.
    """

    if isinstance(user_or_email, str) or isinstance(user_or_email, unicode):
        email = user_or_email
    else:
        email = getattr(user_or_email, 'email', None)
    if email:
        hashcode = hashlib.md5(email.lower()).hexdigest()
    else:
        hashcode = '00000000000000000000000000000000'
    schema = 'http://' if request.url.startswith('http://') else 'https://'
    ret = '%(schema)swww.gravatar.com/avatar/%(hashcode)s.jpg?s=%(size)d&d=mm'
    return ret % {'schema': schema, 'hashcode': hashcode, 'size': size}


def is_email(login):
    """Check whether the given login name is an email address.

    :param login: The login name.
    :type login: :class:`str`
    :return: :data:`True` if is email, :data:`False` otherwise.
    """
    # TODO: Since the sign up and admin create user page all restrict the
    #       characters to A-Za-z0-9_, just test whether '@' exists is enough.
    return '@' in login


def group_histogram(data, getter):
    """Get the group histogram from given objects.

    The frequency of each group will be counted and the histogram will be
    based on the groups.

    :param data: Iterable objects to be analyzed.
    :param getter: A :func:`callable` object to get the group name from
        an object.

    :return: A :class:`dict` {group: frequency}.
    """
    ret = {}

    for d in data:
        g = getter(d)
        if g in ret:
            ret[g] += 1
        else:
            ret[g] = 1

    return ret


def date_histogram(data, getter, ignore_year=False):
    """Get the date histogram from given objects.

    :param data: Iterable objects to be analyzed.
    :param getter: A :func:`callable` object to get a
        :class:`~datetime.datetime` from an object.
    :param ignore_year: Ignore the year in the date.  Only month and day
        will be used in histogram.

    :return: A sorted :class:`list` of :class:`tuple`
        ((year, month, day), freq).
    """
    ret = {}
    if ignore_year:
        get_key = lambda dt: (dt.month, dt.day)
    else:
        get_key = lambda dt: (dt.year, dt.month, dt.day)

    for obj in data:
        key = get_key(to_user_timezone(getter(obj)))
        if key in ret:
            ret[key] += 1
        else:
            ret[key] = 1
    return sorted(ret.items())
