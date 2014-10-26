#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/api.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import json
from functools import wraps

from flask import request, make_response

from .context import app, db, csrf
from .models import Handin, FinalScore
from railgun.common.hw import HwScore
from railgun.common.crypto import DecryptMessage
from railgun.common.lazy_i18n import lazy_gettext


def secret_api(method):
    """Decorate the view method so that the POST data will be first decrypted
    via AES cipher, then decoded as JSON message.  The resulted object will
    be stored in `flask.request.payload`.

    This decorator expects the request header
    ``Content-Type: application/octet-stream``, otherwise it will return
    a 400 http error.  Also, if it could not decrypt the POST data via
    AES cipher, or if it could not decode the JSON message, it will return
    a 400 http error as well.

    :param method: The method to be decorated.
    """
    @wraps(method)
    def inner(*args, **kwargs):
        if request.headers['content-type'] != 'application/octet-stream':
            return make_response(('not application/octet-stream', 400))

        # try to decrypt the secret message
        payload = request.data
        try:
            payload = DecryptMessage(payload, app.config['COMM_KEY'])
        except Exception:
            return make_response(('decryption failure', 400))

        # decode payload in json
        try:
            request.payload = json.loads(payload)
        except Exception:
            app.logger.debug('Not valid json: %s.' % repr(payload))
            return make_response(('not valid json', 400))

        return method(*args, **kwargs)
    return inner


@csrf.exempt
@app.route('/api/handin/report/<uuid>/', methods=['POST'])
@secret_api
def api_handin_report(uuid):
    """Store the final score and detailed reports of given submission.

    This view will compare `uuid` in POST object to the `uuid` argument.
    If they are not equal, the operation will be rejected, since it is
    likely to be an attack.

    If the submission state is neither `Running` nor `Pending`, the operation
    will be rejected, since it is likely to be a programmatic bug.

    If the reported score is 0.0, but the state is `Accepted`, then it
    will be modified to `Rejected`, since it is wired for a zero-score
    submission to be `Accepted`.

    If the reported brief result message is empty, it will be set to
    a translated version of `"Your submission is accepted."` or
    `"Your submission is rejected."`, depending on the reported state.

    The :class:`~railgun.website.models.FinalScore` table records will
    also be updated in this view.

    :route: /api/handin/report/<uuid>/
    :payload: A serialized :class:`~railgun.common.hw.HwScore` object.
    :param uuid: The uuid of submission.
    :type uuid: :class:`str`
    :return: ``OK`` if succeeded, error messages otherwise.
    """
    obj = request.payload

    # check uuid, so that we can prevent replay attack
    if obj['uuid'] != uuid:
        return 'uuid mismatch, do not attack'

    # construct HwScore object from payload
    try:
        score = HwScore.from_plain(obj)
    except Exception:
        return 'not valid score object'

    # load the handin object, and report error if not exist
    handin = Handin.query.filter(Handin.uuid == uuid).first()
    if not handin:
        return 'requested handin not found'

    # if handin.state not in ['Running', 'Pending'], it must already have a
    # score. reject the API call.
    if handin.state != 'Running' and handin.state != 'Pending':
        return 'score already reported'

    # Special hack: unittest will catch all exceptions.
    #
    # Such submissions may result 0.0 base score but marked as 'Accepted'.
    # I decide to treat these submissions 'Rejected', because no one
    # would accept a totally bad submission.
    handin.score = score.get_score()
    if handin.score < 1e-5 and score.accepted:
        score.accepted = False
        score.result = lazy_gettext('No test passed, submission rejected.')

    # update result of handin
    handin.state = 'Accepted' if score.accepted else 'Rejected'
    if score.accepted:
        handin.result = lazy_gettext('Your submission is accepted.')
    elif unicode(score.result):
        handin.result = score.result
    else:
        handin.result = lazy_gettext('Your submission is rejected.')
    handin.compile_error = score.compile_error
    handin.partials = score.partials

    # update hwscore table and set the final score of this homework
    if handin.is_accepted():
        final_score = handin.score * handin.scale
        hwscore = (FinalScore.query.filter(FinalScore.hwid == handin.hwid).
                   filter(FinalScore.user_id == handin.user_id)).first()
        if not hwscore:
            hwscore = FinalScore(user_id=handin.user_id, hwid=handin.hwid,
                                 score=final_score)
            db.session.add(hwscore)
        elif final_score > hwscore.score:
            hwscore.score = final_score

    try:
        db.session.commit()
    except Exception:
        app.logger.exception('Cannot update result of submission(%s).' % uuid)
        return 'update database failed'

    return 'OK'


@csrf.exempt
@app.route('/api/handin/start/<uuid>/', methods=['POST'])
@secret_api
def api_handin_start(uuid):
    """Change the state of given submission from `Pending` to `Running`.

    This view will compare `uuid` in POST object to the `uuid` argument.
    If they are not equal, the operation will be rejected, since it is
    likely to be an attack.

    If the submission is not `Pending`, the operation will also be rejected,
    since it may be a duplicated request from the runner.

    :payload: {"uuid": uuid of submission}
    :param uuid: The uuid of submission.
    :type uuid: :class:`str`
    :return: ``OK`` if succeeded, error messages otherwise.
    """
    obj = request.payload

    # check uuid, so that we can prevent replay attack
    if obj['uuid'] != uuid:
        return 'uuid mismatch, do not attack'

    # load the handin object, and report error if not exist
    handin = Handin.query.filter(Handin.uuid == uuid).first()
    if not handin:
        return 'requested submission not found'

    # we only update state from "Pending" to "Running"
    if handin.state != 'Pending':
        return 'submission is not pending'

    handin.state = 'Running'

    try:
        db.session.commit()
    except Exception:
        app.logger.exception('Cannot update state of submission(%s).' % uuid)
        return 'update database failed'

    return 'OK'


@csrf.exempt
@app.route('/api/handin/proclog/<uuid>/', methods=['POST'])
@secret_api
def api_handin_proclog(uuid):
    """Store the process outputs for a given submission.

    This api view is usually requested after the reports of the corresponding
    submission has been stored, so it would not change either the score or
    the state of the submission.

    If the submission state is still `Pending` or `Running`, indicating that
    the reports have not been stored (probably the process exited abnormally
    before report the score), the state will be updated to `Rejected`.

    This view will compare `uuid` in POST object to the `uuid` argument.
    If they are not equal, the operation will be rejected, since it is
    likely to be an attack.

    :route: /api/handin/proclog/<uuid>/
    :payload:

    .. code-block:: python

        {"uuid": uuid of submission,
         "exitcode": The exitcode of the process,
         "stdout": The standard output of the process,
         "stderr": The standard error output of the process}

    :param uuid: The uuid of submission.
    :type uuid: :class:`str`
    :return: ``OK`` if succeeded, error messages otherwise.
    """
    obj = request.payload

    # check uuid, so that we can prevent replay attack
    if obj['uuid'] != uuid:
        return 'uuid mismatch, do not attack'

    # load the handin object, and report error if not exist
    handin = Handin.query.filter(Handin.uuid == uuid).first()
    if not handin:
        return 'requested submission not found'

    # if handin.state != 'Accepted' and handin.state != 'Rejected',
    # the process must have exited without report the score.
    # mark such handin as "Rejected"
    if handin.state != 'Accepted' and handin.state != 'Rejected':
        handin.state = 'Rejected'
        handin.result = lazy_gettext('Process exited before reporting score.')
        handin.partials = []

    try:
        handin.exitcode = obj['exitcode']
        handin.stdout = obj['stdout']
        handin.stderr = obj['stderr']
        db.session.commit()
    except Exception:
        app.logger.exception('Cannot log proccess of submission(%s).' % uuid)
        return 'update database failed'

    return 'OK'


@csrf.exempt
@app.route('/api/myip/')
def api_myip():
    """API routing that send back the visitor's ip address.
    The Content-Type of response is `text/plain`.

    :route: /api/myip/
    :method: GET
    :return: The visitor's ip address.
    """
    return request.remote_addr, 200, {'Content-Type': 'text/plain'}
