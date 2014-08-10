#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/api.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import json
from functools import wraps

from flask import request, make_response

from .context import app, db, csrf
from .models import Handin
from railgun.common.hw import HwScore
from railgun.common.crypto import DecryptMessage
from railgun.common.lazy_i18n import gettext_lazy


def secret_api(method):
    @wraps(method)
    def inner(*args, **kwargs):
        if (request.headers['content-type'] != 'application/octet-stream'):
            return make_response(('not application/octet-stream', 400))

        # try to decrypt the secret message
        payload = request.data
        try:
            payload = DecryptMessage(payload, app.config['COMM_KEY'])
        except Exception:
            return 'decryption failure'

        # decode payload in json
        try:
            request.payload = json.loads(payload)
        except Exception:
            return 'not valid json'

        return method(*args, **kwargs)
    return inner


@csrf.exempt
@app.route('/api/handin/report/<uuid>/', methods=['POST'])
@secret_api
def api_handin_report(uuid):
    """Set handin score from the Runner."""
    obj = request.payload

    # check uuid, so that we can prevent replay attack
    if (obj['uuid'] != uuid):
        return 'uuid mismatch, do not attack'

    # construct HwScore object from payload
    try:
        score = HwScore.from_plain(obj)
    except Exception:
        return 'not valid score object'

    # load the handin object, and report error if not exist
    handin = Handin.query.filter(Handin.uuid == uuid).first()
    if (not handin):
        return 'requested handin not found'

    # update result of handin
    handin.state = 'Accepted' if score.accepted else 'Rejected'
    handin.score = score.get_score()
    handin.run_time = score.get_time()
    if (score.accepted):
        handin.result = gettext_lazy('Your handin is accepted.')
    elif (score.result):
        handin.result = score.result
    else:
        handin.result = gettext_lazy('Your handin is rejected.')
    handin.partials = score.partials

    try:
        db.session.commit()
    except Exception:
        app.logger.exception('Cannot update result of handin(%s).' % uuid)
        return 'update database failed'

    return 'OK'


@csrf.exempt
@app.route('/api/handin/start/<uuid>/', methods=['POST'])
@secret_api
def api_handin_start(uuid):
    """Update the progress of handin from "Pending" to "Running"."""
    obj = request.payload

    # check uuid, so that we can prevent replay attack
    if (obj['uuid'] != uuid):
        return 'uuid mismatch, do not attack'

    # load the handin object, and report error if not exist
    handin = Handin.query.filter(Handin.uuid == uuid).first()
    if (not handin):
        return 'requested handin not found'

    # we only update state from "Pending" to "Running"
    if (handin.state != 'Pending'):
        return 'handin is not pending'

    handin.state = 'Running'

    try:
        db.session.commit()
    except Exception:
        app.logger.exception('Cannot update state of handin(%s).' % uuid)
        return 'update database failed'

    return 'OK'


@csrf.exempt
@app.route('/api/handin/proclog/<uuid>/', methods=['POST'])
@secret_api
def api_handin_proclog(uuid):
    """Update (exitcode, stdout, stderr) of handin."""
    obj = request.payload

    # check uuid, so that we can prevent replay attack
    if (obj['uuid'] != uuid):
        return 'uuid mismatch, do not attack'

    # load the handin object, and report error if not exist
    handin = Handin.query.filter(Handin.uuid == uuid).first()
    if (not handin):
        return 'requested handin not found'

    try:
        handin.exitcode = obj['exitcode']
        handin.stdout = obj['stdout']
        handin.stderr = obj['stderr']
        db.session.commit()
    except Exception:
        app.logger.exception('Cannot log proccess of handin(%s).' % uuid)
        return 'update database failed'

    return 'OK'
