#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/utility.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import colorsys
from flask.ext.babel import gettext as _


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

    if not size:
        return None
    if size > 1e9:
        return _('%(size).2fG', size=size / (1024.0 * 1024.0 * 1024.0))
    if size > 1e6:
        return _('%(size).2fM', size=size / (1024.0 * 1024.0))
    if size > 1e3:
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
