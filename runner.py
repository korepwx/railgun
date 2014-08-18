#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: runner.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import os
import sys
import copy

# there are two run queues: `default` for standard handins, and `online` for
# netapi handins.
queue = sys.argv[1] if len(sys.argv) > 1 else 'default'

# construct the new running environment
env = copy.copy(os.environ)
env['PYTHONPATH'] = os.pathsep.join([
    os.path.realpath(os.path.dirname(__file__))
])

# execute the runner according to arguments
args = [
    'celery',
    '-A',
    'railgun.runner.context',
    'worker',
    '-Q',
    queue,
    '--loglevel=info',
]
os.execvpe('celery', args, env)
