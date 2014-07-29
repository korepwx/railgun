#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/common/gravatar.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import hashlib
from flask import request


def get_avatar(user_or_email, size):
    """Get the url of avatar to given user object, or email if is string."""
    if (isinstance(user_or_email, str) or isinstance(user_or_email, unicode)):
        email = user_or_email
    else:
        email = getattr(user_or_email, 'email', None)
    if (email):
        hashcode = hashlib.md5(email.lower()).hexdigest()
    else:
        hashcode = '00000000000000000000000000000000'
    schema = 'http://' if request.url.startswith('http://') else 'https://'
    ret = '%(schema)swww.gravatar.com/avatar/%(hashcode)s.jpg?s=%(size)d&d=mm'
    return ret % {'schema': schema, 'hashcode': hashcode, 'size': size}
