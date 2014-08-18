#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: hw/black_box/code/input/run.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

from railgun.common.csvdata import CsvSchema, CsvFloat
from pyhost.scorer import InputClassScorer
from pyhost import SafeRunner


# Initialize the scorer with CSV schema and data
class TriangleArgs(CsvSchema):
    """Data schema for `triangle_type` method arguments."""

    a = CsvFloat()
    b = CsvFloat()
    c = CsvFloat()

scorer = InputClassScorer(TriangleArgs, open('data.csv', 'rb'))


# Add input class rules
@scorer.rule('regular triangle')
def regular_triangle(obj):
    return (obj.a > 0 and obj.b > 0 and obj.c > 0) and \
        (obj.a == obj.b == obj.c)


@scorer.rule('isosceles triangle (a, b, c > 0) and (a == b != c)')
def isosceles_triangle_1(obj):
    return (obj.a > 0 and obj.b > 0 and obj.c > 0) and \
        (obj.a == obj.b) and (obj.a != obj.c) and \
        (obj.a + obj.b > obj.c)


@scorer.rule('isosceles triangle (a, b, c > 0) and (a == c != b)')
def isosceles_triangle_2(obj):
    return (obj.a > 0 and obj.b > 0 and obj.c > 0) and \
        (obj.a == obj.c) and (obj.a != obj.b) and \
        (obj.a + obj.c > obj.b)


@scorer.rule('isosceles triangle (a, b, c > 0) and (b == c != a)')
def isosceles_triangle_3(obj):
    return (obj.a > 0 and obj.b > 0 and obj.c > 0) and \
        (obj.b == obj.c) and (obj.b != obj.a) and \
        (obj.b + obj.c > obj.a)


@scorer.rule('normal triangle')
def normal_triangle(obj):
    return (obj.a > 0 and obj.b > 0 and obj.c > 0) and \
        (obj.a + obj.b > obj.c) and \
        (obj.a + obj.c > obj.b) and \
        (obj.b + obj.c > obj.a) and \
        not (obj.a == obj.b or obj.a == obj.c or obj.b == obj.c)


@scorer.rule('not triangle (a, b, c > 0) and (a + b < c)')
def not_triangle_1(obj):
    return (obj.a > 0 and obj.b > 0 and obj.c > 0) and \
        (obj.a + obj.b < obj.c)


@scorer.rule('not triangle (a, b, c > 0) and (b + c < a)')
def not_triangle_2(obj):
    return (obj.a > 0 and obj.b > 0 and obj.c > 0) and \
        (obj.b + obj.c < obj.a)


@scorer.rule('not triangle (a, b, c > 0) and (a + c < b)')
def not_triangle_3(obj):
    return (obj.a > 0 and obj.b > 0 and obj.c > 0) and \
        (obj.a + obj.c < obj.b)


@scorer.rule('degenerate triangle (a, b, c > 0) and (a + b == c)')
def degenerate_triangle_1(obj):
    return (obj.a > 0 and obj.b > 0 and obj.c > 0) and \
        (obj.a + obj.b == obj.c)


@scorer.rule('degenerate triangle (a, b, c > 0) and (b + c == a)')
def degenerate_triangle_2(obj):
    return (obj.a > 0 and obj.b > 0 and obj.c > 0) and \
        (obj.b + obj.c == obj.a)


@scorer.rule('degenerate triangle (a, b, c > 0) and (a + c == b)')
def degenerate_triangle_3(obj):
    return (obj.a > 0 and obj.b > 0 and obj.c > 0) and \
        (obj.a + obj.c == obj.b)


@scorer.rule('zero data (one of a, b, c == 0)')
def zero_data_1(obj):
    return (obj.a == 0 and obj.b != 0 and obj.c != 0) or \
        (obj.a != 0 and obj.b == 0 and obj.c != 0) or \
        (obj.a != 0 and obj.b != 0 and obj.c == 0)


@scorer.rule('zero data (all of a, b, c == 0)')
def zero_data_2(obj):
    return (obj.a == 0 and obj.b == 0 and obj.c == 0)


@scorer.rule('negative data (one of a, b, c < 0)')
def negative_data_1(obj):
    return (obj.a < 0 and obj.b >= 0 and obj.c >= 0) or \
        (obj.a >= 0 and obj.b < 0 and obj.c >= 0) or \
        (obj.a >= 0 and obj.b >= 0 and obj.c < 0)


@scorer.rule('negative data (all of a, b, c < 0)')
def negative_data_2(obj):
    return (obj.a < 0 and obj.b < 0 and obj.c < 0)


# Run this scorer
SafeRunner.run([
    (scorer, 1.0)
])
