#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: tools/patchall.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import os
import re
import sys
sys.path.insert(0, os.path.split(os.path.dirname(__file__))[0])

from railgun.common.fileutil import dirtree


if (len(sys.argv) < 4):
    print('patchall.py from-string to-string pattern [--commit]')
    sys.exit(0)

fromstr = sys.argv[1]
tostr = sys.argv[2]
pattern = re.compile(sys.argv[3])
preview = not (len(sys.argv) >= 5 and sys.argv[4] == '--commit')


flist = dirtree('.')
for f in flist:
    if (not pattern.match(f) or f.startswith('env')):
        continue
    with open(f, 'rb') as fobj:
        inlines = fobj.read().split('\n')

    changed = False
    for i, line in enumerate(inlines, 1):
        pos = line.find(fromstr)
        if (pos < 0):
            continue
        print('%s:%d: %s' % (f, i, line))
        inlines[i-1] = line.replace(fromstr, tostr)
        changed = True

    if (not preview and changed):
        with open(f, 'wb') as fobj:
            fobj.write('\n'.join(inlines))
