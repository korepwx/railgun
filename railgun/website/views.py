#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/views.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import os
import uuid

from flask import render_template, url_for, redirect, flash, request, g, \
    send_from_directory
from flask.ext.babel import lazy_gettext, get_locale, gettext as _
from flask.ext.login import login_user, logout_user, current_user, \
    confirm_login
from werkzeug.exceptions import NotFound

from .context import app, db
from .navibar import navigates, NaviItem, set_navibar_identity
from .forms import SignupForm, SigninForm, ProfileForm, ReAuthenticateForm
from .credential import UserContext, login_required, fresh_login_required, \
    should_update_email, redirect_update_email
from .userauth import authenticate, auth_providers
from .codelang import languages
from .models import User, Handin
from .i18n import get_best_locale_name
from railgun.common.fileutil import dirtree


@app.route('/')
def index():
    g.scripts.headScripts()
    # check user email when authenticated
    if current_user.is_authenticated():
        if should_update_email():
            return redirect_update_email()
    return render_template('index.html')


@app.route('/signup/', methods=['GET', 'POST'])
def signup():
    # If railgun does not allow new user signup, show 403 forbidden
    # TODO: beautify this page.
    if not app.config['ALLOW_SIGNUP']:
        return _('Sign up is turned off.'), 403
    form = SignupForm()
    if form.validate_on_submit():
        # Construct user data object
        user = User()
        form.populate_obj(user)
        user.set_password(form.password.data)
        user.fill_i18n_from_request()
        try:
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('signin'))
        except Exception:
            app.logger.exception('Cannot create account %s' % user.name)
        flash(_("I'm sorry but we may have met some trouble. Please try "
                "again."), 'warning')
    return render_template('signup.html', form=form)


@app.route('/signin/', methods=['GET', 'POST'])
def signin():
    form = SigninForm()
    next_url = request.args.get('next')
    if form.validate_on_submit():
        # Check whether the user exists
        user = authenticate(form.login.data, form.password.data)
        if user:
            # Now we can login this user and redirect to index!
            login_user(UserContext(user), remember=form.remember.data)
            return redirect(next_url or url_for('index'))
        # Report username or password error
        flash(_('Incorrect username or password.'), 'danger')
    return render_template('signin.html', form=form, next=next_url)


@app.route('/reauthenticate/', methods=['GET', 'POST'])
@login_required
def reauthenticate():
    # Re-authenticate form is just like signin but do not contain "remember"
    form = ReAuthenticateForm()
    next_url = request.args.get('next')

    if form.validate_on_submit():
        # Check whether the user exists
        user = authenticate(current_user.name, form.password.data)
        if user:
            confirm_login()
            return redirect(next_url or url_for('index'))
        # Report password error
        flash(_('Incorrect password.'), 'danger')
    return render_template('reauthenticate.html', form=form, next=next_url)


@app.route('/signout/')
def signout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/profile/edit/', methods=['GET', 'POST'])
@fresh_login_required
def profile_edit():
    # Profile edit should use typeahead.js
    g.scripts.deps('typeahead.js')

    # Create the profile form.
    # Note that some fields cannot be edited in certain auth providers,
    # which should be stripped from from schema.
    form = ProfileForm(obj=current_user.dbo)
    if current_user.provider:
        auth_providers.init_form(current_user.provider, form)

    if form.validate_on_submit():
        # Set password if passwd field exists
        if 'password' in form:
            pwd = form.password.data
            if pwd:
                current_user.set_password(pwd)
            del form['password']
            del form['confirm']
        else:
            pwd = None

        # Copy values into current_user object
        form.populate_obj(current_user.dbo)

        # Commit to main database and auth provider
        try:
            if current_user.provider:
                auth_providers.push(current_user.dbo, pwd)
            db.session.commit()
            flash(_('Profile saved.'), 'info')
        except Exception:
            app.logger.exception('Cannot update account %s' %
                                 current_user.name)
            flash(_("I'm sorry but we may have met some trouble. Please try "
                    "again."), 'warning')
        return redirect(url_for('profile_edit'))

    # If form has errors, flash message to notify the user
    if form.errors:
        flash(
            _("You've got some errors in the form, please check your input."),
            'warning'
        )

    # Clear password & confirm here is ok.
    if 'password' in form:
        form.password.data = None
        form.confirm.data = None

    return render_template('profile_edit.html', locale_name=str(get_locale()),
                           form=form)


@app.route('/homework/<slug>/', methods=['GET', 'POST'])
@login_required
def homework(slug):
    # set the identity for navibar (so that current page will be activated)
    set_navibar_identity('homework.%s' % slug)
    # load requested homework instance
    hw = g.homeworks.get_by_slug(slug)
    if not hw:
        raise NotFound()
    # generate multiple forms with different prefix
    hwlangs = hw.get_code_languages()
    forms = {
        k: languages[k].upload_form(hw) for k in hwlangs
    }
    # detect which form is used
    handin_lang = None
    if request.method == 'POST' and 'handin_lang' in request.form:
        # check the pending submission count of requested user
        user_pending = db.session.query(Handin)\
            .filter(Handin.state.in_(['Pending', 'Running'])) \
            .filter(Handin.hwid == hw.uuid) \
            .filter(Handin.user_id == current_user.id) \
            .count()
        if user_pending >= app.config['MAX_USER_PENDING_PER_HW']:
            flash(_('You can only have at most %(count)d pending or running '
                    'submission(s) for this homework.',
                    count=app.config['MAX_USER_PENDING_PER_HW']),
                  'danger')
            return redirect(url_for('homework', slug=slug))
        # check locked
        if hw.is_locked() and not current_user.is_admin:
            flash(_('This homework is locked and cannot be submitted.'),
                  'danger')
            return redirect(url_for('homework', slug=slug))
        # check deadline
        next_ddl = hw.get_next_deadline()
        if not next_ddl:
            flash(_('This homework is out of date! '
                    'You cannot upload your submission.'), 'danger')
            return redirect(url_for('homework', slug=slug))
        # we must record the current next_ddl. during the request processing,
        # such deadline may pass so that our program may fail later
        g.ddl_date = next_ddl[0]
        g.ddl_scale = next_ddl[1]
        handin_lang = request.form['handin_lang']
        # check the data integrity of uploaded data
        if forms[handin_lang].validate_on_submit():
            handid = uuid.uuid4().get_hex()
            try:
                languages[handin_lang].handle_upload(
                    handid, hw, handin_lang, forms[handin_lang]
                )
                flash(
                    _('You submission is accepted, please wait for results.'),
                    'success'
                )
            except Exception:
                app.logger.exception('Error when adding submission to run '
                                     'queue.')
                flash(_('Internal server error, please try again.'), 'danger')
            # homework page is too long, so redirect to handins page, to
            # let flashed message clearer
            return redirect(url_for('hwhandins', slug=hw.slug))

    # if handin_lang not determine, choose the first lang
    if handin_lang is None:
        handin_lang = hwlangs[0]
    return render_template(
        'homework.html', hw=hw, forms=forms, active_lang=handin_lang,
        hwlangs=hwlangs
    )


@app.route('/hwpack/<slug>/<lang>.zip')
def hwpack(slug, lang):
    # NOTE: I suppose that there's no need to guard the homework archives
    #       by @login_required. regarding this, the packed archives can be
    #       served by nginx, not flask framework, which should be much
    #       faster to be responded.
    filename = '%(slug)s/%(lang)s.zip' % {'slug': slug, 'lang': lang}
    return send_from_directory(app.config['HOMEWORK_PACK_DIR'], filename)


@app.route('/hwstatic/<path:filename>')
def hwstatic(filename):
    return send_from_directory(app.config['HOMEWORK_STATIC_DIR'], filename)


@app.route('/homework/<slug>/handin/')
@login_required
def hwhandins(slug):
    # set the identity for navibar (so that current page will be activated)
    set_navibar_identity('homework.%s.handin' % slug)
    # load requested homework instance
    hw = g.homeworks.get_by_slug(slug)
    if not hw:
        raise NotFound()
    # get pagination argument
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
    try:
        perpage = int(request.args.get('perpage', 10))
    except ValueError:
        perpage = 10
    # query about all handins
    handins = (Handin.query.filter(Handin.user_id == current_user.id).
               filter(Handin.hwid == hw.uuid))
    # Sort the handins
    handins = handins.order_by(-Handin.id)
    # build pagination object
    return render_template(
        'homework.handins.html',
        the_page=handins.paginate(page, perpage),
        hw=hw
    )


@app.route('/handin/<uuid>/')
@login_required
def handin_detail(uuid):
    # Query about the handin record
    handin = Handin.query.filter(Handin.uuid == uuid)
    if not current_user.is_admin:
        handin = handin.filter(Handin.user_id == current_user.id)
    handin = handin.first()

    # If not found, result 404
    if not handin:
        return _('Submission not found'), 404

    # Get the homework
    hw = g.homeworks.get_by_uuid(handin.hwid)

    # check whether the original submission exists
    submit_file = os.path.join(app.config['UPLOAD_STORE_DIR'], uuid)
    original_submission_exist = os.path.isfile(submit_file)

    # render the handin
    return render_template('handin_detail.html', handin=handin, hw=hw,
                           original_submission_exist=original_submission_exist)


@app.route('/handin/<uuid>/download/')
@login_required
def handin_download(uuid):
    # Query about the handin record
    handin = Handin.query.filter(Handin.uuid == uuid)
    if not current_user.is_admin:
        handin = handin.filter(Handin.user_id == current_user.id)
    handin = handin.first()

    # If not found, result 404
    if not handin:
        return _('Submission not found'), 404

    # render the submitted payload
    return languages[handin.lang].handle_download(handin.uuid)


def translated_page(name, **kwargs):
    """Render the translated page `name` to client."""
    # List all user guide locales, and select the best one
    page_dir = os.path.join(app.root_path, 'templates/%s' % name)
    locales = []
    if os.path.isdir(page_dir):
        locales = [
            fname[:-5]
            for fname in dirtree(page_dir)
            if fname.endswith('.html')
        ]
    # Select the best matching locale according to user config
    best_locale = get_best_locale_name(locales)
    # Render the page in certain locale
    return render_template('%s/%s.html' % (name, best_locale), **kwargs)


@app.route('/manual/userguide/')
def userguide():
    return translated_page('userguide')


@app.route('/manual/scores/')
def scores():
    return translated_page('scores')


@app.route('/manual/faq/')
def faq():
    return translated_page(
        'faq',
        max_upload=app.config['MAX_SUBMISSION_SIZE'],
        max_archive_file=app.config['MAX_SUBMISSION_FILE_COUNT'],
        max_pending=app.config['MAX_USER_PENDING_PER_HW'],
    )


@app.route('/manual/about/')
def about():
    return translated_page('about')

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
navigates.add(
    NaviItem(
        title=lazy_gettext('Submissions'),
        url=None,
        identity='hwhandin',
        subitems=lambda: [
            NaviItem(
                title=hw.info.name,
                url=url_for('hwhandins', slug=hw.slug),
                identity='homework.%s.handin' % hw.slug
            )
            for hw in g.homeworks
        ]
    )
)
navigates.add(
    NaviItem(
        title=lazy_gettext('Manual'),
        url=None,
        identity='manual',
        subitems=[
            NaviItem.make_view(title=lazy_gettext('User Guide'),
                               endpoint='userguide'),
            NaviItem.make_view(title=lazy_gettext('Scoring Details'),
                               endpoint='scores'),
            NaviItem(
                title=lazy_gettext('Documentation'),
                url='http://secoder-railgun.readthedocs.org/',
                identity='documentation',
            ),
            NaviItem.make_view(title=lazy_gettext('FAQ'),
                               endpoint='faq'),
            NaviItem.make_view(title=lazy_gettext('About'),
                               endpoint='about'),
        ]
    )
)
