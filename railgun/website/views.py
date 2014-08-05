#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/views.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

from flask import render_template, url_for, redirect, flash, request, g
from flask.ext.babel import lazy_gettext, gettext as _
from flask.ext.login import login_user, logout_user, current_user, \
    login_required, fresh_login_required
from werkzeug.exceptions import NotFound
from sqlalchemy import or_, and_

from .hw import homeworks
from .context import app, db
from .navibar import navigates, NaviItem, set_navibar_identity
from .forms import SignupForm, SigninForm, ProfileForm
from .credential import UserContext
from railgun.common.models import User


@app.route('/')
def index():
    # only logged user can see the homeworks
    if (current_user.is_authenticated()):
        pass
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
    next_url = request.args.get('next')
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
                return redirect(next_url or url_for('index'))
        # Report username or password error
        flash(_('Incorrect username or password.'), 'danger')
    return render_template('signin.html', form=form, next=next_url)


@app.route('/signout/')
def signout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/profile/edit/', methods=['GET', 'POST'])
@fresh_login_required
def profile_edit():
    form = ProfileForm()
    if (form.validate_on_submit()):
        # Check whether the email is taken.
        is_taken = (db.session.query(User).filter(and_(
            User.email == form.email.data, User.id != current_user.id)
        ).count() > 0)
        if (is_taken):
            form.email.errors.append(_('Email already taken'))
        # Check whether password is correct
        pwd_ok = (not form.password.data or (len(form.password.data) >= 7 and
                                             len(form.password.data) <= 32))
        if (not pwd_ok):
            form.password.errors.append(_("Password must be no shorter than 7 "
                                          "and no longer than 32 characters"))
        # Do update the user
        if (not is_taken and pwd_ok):
            current_user.dbo.email = form.email.data
            if (form.password.data):
                current_user.dbo.set_password(form.password.data)
            db.session.commit()
            flash(_('Profile saved.'), 'info')
            return redirect(url_for('profile_edit'))
    # Initialize the form value if not POSTed
    if (request.method != 'POST'):
        form.email.data = current_user.email
    return render_template(
        'profile_edit.html', form=form, username=current_user.name
    )


@app.route('/homework/<slug>/')
@login_required
def homework(slug):
    set_navibar_identity('homework.%s' % slug)
    hw = g.homeworks.get_by_slug(slug)
    if (not hw):
        raise NotFound()
    return render_template('homework.html')


# Register all pages into navibar
navigates.add_view(title=lazy_gettext('Home'), endpoint='index')
navigates.add(
    NaviItem(
        title=lazy_gettext('Homework'),
        url=None,
        identity='homework',
        # title of homework is affected by request.accept_languages
        # so we should build subitems until they are used
        subitems=lambda: [
            NaviItem(title=hw.info.name, url=url_for('homework', slug=hw.slug),
                     identity='homework.%s' % hw.slug)
            for hw in g.homeworks
        ]
    )
)
