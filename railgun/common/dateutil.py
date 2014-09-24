#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/common/dateutil.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

from datetime import datetime

from pytz import UTC


def utc_now():
    """get the current date time in UTC timezone."""
    return UTC.normalize(UTC.localize(datetime.utcnow()))


def from_plain_date(dt, tz):
    """Convert a plain datetime to its best format in given timezone.

    Some timezone, such as Asia/Shanghai, is not on the exact boundary of
    timezones (Asia/Shanghai is +08:06).  This method will ensure the tzinfo
    attached to plain datetime object is on the boundary.

    Args:
        dt: the plain datetime object.
        tz: the timezone object.

    Returns:
        A localized datetime object with given timezone.
    """
    return tz.normalize(tz.localize(dt))


def to_plain_date(dt):
    """Replace the tzinfo of the date time object to None."""
    return dt.replace(tzinfo=None)


def to_utc_date(dt, tz):
    """Convert a localized datetime object to utc datetime object.

    Some timezone, such as Asia/Shanghai, is not on the exact boundary of
    timezones (Asia/Shanghai is +08:06).  Others may carry DST information.
    This method will ensure the conversion to UTC date time is correct.

    Args:
        dt: the localized datetime object.
        tz: the timezone object.

    Returns:
        A UTC datetime object.
    """
    return UTC.normalize(tz.astimezone(UTC))


def from_utc_date(dt, tz):
    """Convert a UTC datetime object to localized datetime object.

    Some timezone, such as Asia/Shanghai, is not on the exact boundary of
    timezones (Asia/Shanghai is +08:06).  Others may carry DST information.
    This method will ensure the conversion from UTC date time is correct.

    Args:
        dt: the UTC datetime object.
        tz: the timezone object.

    Returns:
        A UTC datetime object.
    """
    return tz.normalize(tz.astimezone(tz))
