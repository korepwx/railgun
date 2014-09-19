#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: hw/chkpath/code/python/run.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

from pyhost.scorer import CodeStyleScorer, CoverageScorer
import SafeRunner


if (__name__ == '__main__'):
    scorers = [
        (CodeStyleScorer.FromHandinDir(ignore_files=['run.py']), 0.1),
        # Note that the CoverageScorer takes 1.0 as total weight, but
        # uses stmt_weight=0.4, branch_weight=0.5 to control the score
        (CoverageScorer.FromHandinDir(
            files_to_cover=['myfunc.py'],
            stmt_weight=0.4,
            branch_weight=0.5,
        ), 1.0),
    ]
    SafeRunner.run(scorers)
