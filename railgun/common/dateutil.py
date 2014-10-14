#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/common/dateutil.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

"""
Utilities for conversions between `plain datetime`, `localized datetime` and
`UTC datetime`.  These three types are all :class:`datetime.datetime` objects,
while the only difference is their `tzinfo` property.  `tzinfo` is the timezone
information attached to :class:`datetime.datetime`.

.. tabularcolumns:: |p{4cm}|p{11cm}|

=============== ========================================================
Type            Description
=============== ========================================================
plain           `tzinfo` is None, which means no timezone is attached.
                Only (year, month, day, hour, min, sec, ms) tuple of
                such datetime objects are meaningful.
UTC             `tzinfo` is :class:`pytz.UTC`, which means the time
                tuple represents a datetime in UTC timezone.
localized       `tzinfo` neither None, nor :class:`pytz.UTC`,
                representing a datetime in given timezone.
=============== ========================================================

Be careful that some timezone, such as `Asia/Shanghai`, is not on the exact
boundary of hours (`Asia/Shanghai` is +08:06).  Others may carry DST data.
So you SHOULD ONLY use the methods provided in this module to do datetime
conversions.
"""

from datetime import datetime

from pytz import UTC


def utc_now():
    """Get the current UTC datetime object."""
    return UTC.normalize(UTC.localize(datetime.utcnow()))


def from_plain_date(dt, tz):
    """Attach timezone to a plain datetime object.

    This method only attaches the timezone data to `dt`, with no adjust
    performed on time data.  This method will ensure that the tzinfo attached
    to plain datetime object is on the exact boundary of hours.

    :param dt: the plain datetime object.
    :type dt: :class:`datetime.datetime`
    :param tz: the timezone object.
    :type tz: :class:`datetime.tzinfo`

    :return: a localized datetime object.
    """
    return tz.normalize(tz.localize(dt))


def to_plain_date(dt):
    """Strip timezone from a localized or UTC datetime object.

    This method only strips the timezone data from `dt`, with no adjust
    performed on time data.

    :param dt: the localized or UTC datetime object.
    :type dt: :class:`datetime.datetime`

    :return: a plain datetime object.
    """
    return dt.replace(tzinfo=None)


def to_utc_date(dt):
    """Convert a localized datetime object to UTC one.

    This method will adjust the time data, to make sure the conversion from
    localized timezone to UTC is correct.

    :param dt: a localized datetime object.
    :type dt: :class:`datetime.datetime`
    :return: a UTC datetime object.
    """
    return UTC.normalize(dt.astimezone(UTC))


def from_utc_date(dt, tz):
    """Convert a UTC datetime object to localized one.

    This method will adjust the time data, to make sure the conversion from
    UTC to localized timezone is correct.

    :param dt: a localized datetime object.
    :type dt: :class:`datetime.datetime`
    :param tz: the timezone object.
    :type tz: :class:`datetime.tzinfo`

    :return: a localized datetime object.
    """
    return tz.normalize(dt.astimezone(tz))
