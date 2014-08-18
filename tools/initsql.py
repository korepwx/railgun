#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: tools/initsql.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import sys

if (len(sys.argv) < 2):
    print('initsql.py sql-flavour')
    sys.exit(0)

key = open('keys/sqlKey.txt', 'rb').read().strip()
sql = open('sql/%s.sql' % sys.argv[1], 'rb').read()
sql = sql.replace('<the password>', key)

print(sql)
