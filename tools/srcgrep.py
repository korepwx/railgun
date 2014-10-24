#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: tools/srcgrep.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import os
import sys
from termcolor import colored

# whether or not to use colored output?
color_output = False
if os.environ['TERM'] in ('xterm-color'):
    color_output = True

pattern = sys.argv[1]
SOURCE_EXT = ('.py', '.h', '.cpp', '.rst')

for pkg in ('railgun', 'runlib', 'docs'):
    for dpath, dnames, fnames in os.walk(pkg):
        for fname in fnames:
            fpath = os.path.join(dpath, fname)
            if os.path.splitext(fname)[1] not in SOURCE_EXT:
                continue
            lines = [l.rstrip() for l in open(fpath, 'rb')]
            for i, line in enumerate(lines, 1):
                if line.find(pattern) >= 0:
                    if color_output:
                        line = line.replace(pattern, colored(pattern, 'red'))
                    print('%s:%d:%s' % (fpath, i, line))
