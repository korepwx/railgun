#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: hw/chkpath/code/python/run.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import os

from pyhost.scorer import CodeStyleScorer, ObjSchemaScorer, CoverageScorer
from pyhost.objschema import RootSchema
import SafeRunner


# Define the schema of unit test objects
schema = RootSchema(os.environ['RAILGUN_ROOT'])

test_arith = schema.module('test_arith').require()
test_minmax = schema.module('test_minmax').require()

add_test_case = test_arith.class_('AddTestCase').require()
pow_test_case = test_arith.class_('PowTestCase').require()
get_min_test_case = test_minmax.class_('GetMinTestCase').require()

add_test_case.method('test_positive_add_positive').require()
add_test_case.method('test_positive_add_negative').require()
add_test_case.method('test_negative_add_negative').require()

pow_test_case.method('test_positive_pow_positive').require()
pow_test_case.method('test_positive_pow_negative').require()
pow_test_case.method('test_negative_pow_positive_success').require()
pow_test_case.method('test_negative_pow_positive_failure').require()
pow_test_case.method('test_negative_pow_negative_success').require()
pow_test_case.method('test_negative_pow_negative_failure').require()

get_min_test_case.method('test_abc').require()
get_min_test_case.method('test_acb').require()
get_min_test_case.method('test_bac').require()
get_min_test_case.method('test_bca').require()
get_min_test_case.method('test_cab').require()
get_min_test_case.method('test_cba').require()


if (__name__ == '__main__'):
    scorers = [
        (CodeStyleScorer.FromHandinDir(ignore_files=['run.py']), 0.1),
        (CoverageScorer.FromHandinDir(
            files_to_cover=['arith.py', 'minmax.py'],
            stmt_weight=1.0,
            branch_weight=0.0,
        ), 0.2),
        (ObjSchemaScorer(schema), 0.7),
    ]
    SafeRunner.run(scorers)
