#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: hw/arith_api/code/netapi/server/api.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import json
from functools import wraps
from flask import Flask, request, make_response

app = Flask(__name__)


def json_api(method):
    """Decorator that check Content-Type of request to make sure the request
    carries an application/json object, and convert response object into
    json representation."""

    def mkresp(obj, status=200):
        """Make json response object."""
        resp = make_response(json.dumps(obj), status)
        resp.headers['Content-Type'] = 'application/json'
        return resp

    @wraps(method)
    def inner(*args, **kwargs):
        if (request.method != 'POST' or
                request.headers['Content-Type'] != 'application/json'):
            return mkresp({'error': 1, 'message': 'not json request'}, 400)
        try:
            ret = method(*args, **kwargs)
        except Exception, ex:
            return mkresp({'error': 1, 'message': ex.message}, 500)
        return mkresp({'error': 0, 'result': ret})
    return inner


@app.route('/')
def index():
    return 'Your API address: <input type="text" value="%s" />' % request.url


@app.route('/add/', methods=['POST'])
@json_api
def add():
    return request.json['a'] + request.json['b']


@app.route('/pow/', methods=['POST'])
@json_api
def pow():
    return request.json['a'] ** request.json['b']


@app.route('/gcd/', methods=['POST'])
@json_api
def gcd():
    a, b = request.json['a'], request.json['b']
    if (a < b):
        a, b = b, a
    while b:
        t = b
        b = a % b
        a = t
    return a


if (__name__ == '__main__'):
    app.run(host='0.0.0.0', port=8080)
