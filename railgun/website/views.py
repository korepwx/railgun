#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/views.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

from flask import render_template, url_for, redirect, flash
from flask.ext.babel import lazy_gettext, gettext as _
from flask.ext.login import login_user, logout_user
from sqlalchemy import or_

from .context import app, db
from .navibar import navigates
from .forms import SignupForm, SigninForm
from .credential import UserContext
from railgun.common.models import User


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/signup/', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if (form.validate_on_submit()):
        # Construct user data object
        user = User()
        form.populate_obj(user)
        user.set_password(form.password.data)
        # Check whether username or password conflicts
        has_error = False
        if (db.session.query(User).filter(User.name == user.name).count()):
            form.name.errors.append(_('Username already taken'))
            has_error = True
        if (db.session.query(User).filter(User.email == user.email).count()):
            form.email.errors.append(_('Email already taken'))
            has_error = True
        # Add user if no error
        if (not has_error):
            try:
                db.session.add(user)
                db.session.commit()
                return redirect(url_for('signin'))
            except Exception:
                app.logger.exception('Cannot create account %s' % user.name)
            flash(_("I'm sorry but we may have met some trouble. "
                    "Please try again."))
    return render_template('signup.html', form=form)


@app.route('/signin/', methods=['GET', 'POST'])
def signin():
    form = SigninForm()
    if (form.validate_on_submit()):
        # Check whether the user exists
        user = db.session.query(User).filter(
            or_(User.name == form.login.data, User.email == form.login.data)
        ).first()
        # Check whether password match
        if (user):
            if (user.check_password(form.password.data)):
                # Now we can login this user and redirect to index!
                login_user(UserContext(user))
                return redirect(url_for('index'))
        # Report username or password error
        flash(_('Incorrect username or password.'), 'danger')
    return render_template('signin.html', form=form)


@app.route('/signout/')
def signout():
    logout_user()
    return redirect(url_for('index'))


# Register all pages into navibar
navigates.add_page(lazy_gettext('Home'), 'index')
