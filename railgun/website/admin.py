#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/admin.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import csv
from functools import wraps
from cStringIO import StringIO

from flask import Blueprint, render_template, request, g, flash, redirect, \
    url_for, send_file
from flask.ext.babel import get_locale, lazy_gettext, gettext as _
from flask.ext.login import login_fresh, current_user
from sqlalchemy import func
from sqlalchemy.orm import contains_eager
from werkzeug.exceptions import NotFound

from railgun.maintain.hwcache import HwCacheTask
from railgun.maintain.tzcache import TzCacheTask
from .context import app, db
from .models import User, Handin
from .forms import AdminUserEditForm
from .userauth import auth_providers
from .credential import login_manager
from .navibar import navigates, NaviItem
from .utility import round_score

# The admin application blueprint
bp = Blueprint('admin', __name__)


def admin_required(method):
    """Decorator that protects a given view to only accessible to admins."""
    @wraps(method)
    def inner(*args, **kwargs):
        if (not current_user.is_authenticated()):
            return login_manager.unauthorized()
        if (not login_fresh()):
            return login_manager.needs_refresh()
        if (not current_user.is_admin):
            return 'You are not admin!', 403
        return method(*args, **kwargs)
    return inner


@bp.route('/users/')
@admin_required
def users():
    """Manage all users."""
    # get pagination argument
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
    try:
        perpage = int(request.args.get('perpage', 10))
    except ValueError:
        perpage = 10
    # query about all users
    users = User.query.filter()
    # build pagination object
    return render_template(
        'admin.users.html',
        the_page=users.paginate(page, perpage)
    )


@bp.route('/users/<name>/', methods=['GET', 'POST'])
@admin_required
def user_edit(name):
    """Edit given user `name`."""
    # Profile edit should use typeahead.js
    g.scripts.deps('typeahead.js')

    # Get the user object
    the_user = User.query.filter(User.name == name).one()

    # Create the profile form.
    # Note that some fields cannot be edited in certain auth providers,
    # which should be stripped from from schema.
    form = AdminUserEditForm(obj=the_user)
    if (the_user.provider):
        auth_providers.init_form(the_user.provider, form)
    form._the_user = the_user

    if (form.validate_on_submit()):
        # Set password if passwd field exists
        if ('password' in form):
            pwd = form.password.data
            if (pwd):
                the_user.set_password(pwd)
            del form['password']
            del form['confirm']
        else:
            pwd = None

        # Copy values into current_user object
        form.populate_obj(the_user)

        # Commit to main database and auth provider
        try:
            if (the_user.provider):
                auth_providers.push(the_user, pwd)
            db.session.commit()
            flash(_('Profile saved.'), 'info')
        except Exception:
            app.logger.exception('Cannot update account %s' % the_user.name)
            flash(_("I'm sorry but we may have met some trouble. Please try "
                    "again."), 'warning')
        return redirect(url_for('admin.users'))

    # Clear password & confirm here is ok.
    if ('password' in form):
        form.password.data = None
        form.confirm.data = None

    return render_template(
        'admin.user_edit.html',
        locale_name=str(get_locale()),
        form=form,
        the_user=the_user,
    )


@bp.route('/handin/')
@admin_required
def handins():
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
    handins = Handin.query.join(Handin.user). \
        options(contains_eager(Handin.user)).filter()
    # Sort the handins
    handins = handins.order_by(-Handin.id)
    # build pagination object
    return render_template(
        'admin.handins.html', the_page=handins.paginate(page, perpage))


@bp.route('/scores/')
@admin_required
def scores():
    return render_template('admin.scores.html')


def make_csv_report(q, display_headers, raw_headers, pagetitle, filename):
    def make_record(itm, hdr):
        if (isinstance(itm, dict)):
            return tuple(itm[h] for h in hdr)
        return tuple(getattr(itm, h) for h in hdr)

    # If a direct csv file is request
    if (request.args.get('csvfile', None) == '1'):
        io = StringIO()
        writer = csv.writer(io)
        writer.writerow(raw_headers)
        for itm in q:
            writer.writerow(make_record(itm, raw_headers))
        io.flush()
        return send_file(
            io,
            as_attachment=True,
            attachment_filename='%s.csv' % filename
        )

    # Otherwise show the page.
    return render_template(
        'admin.csvdata.html',
        headers=display_headers,
        items=[make_record(itm, raw_headers) for itm in q],
        pagetitle=pagetitle,
    )


@bp.route('/hwscores/<hwid>/')
@admin_required
def hwscores(hwid):
    def make_record(itm, hdr):
        return tuple([getattr(itm, h) for h in hdr])

    # Query about given homework
    hw = g.homeworks.get_by_uuid(hwid)
    if (hw is None):
        raise NotFound(lazy_gettext('Requested homework not found.'))

    # Get max score for each user
    q = (db.session.query(Handin.user_id,
                          Handin.state,
                          User.name,
                          func.max(Handin.score * Handin.scale).label('score')).
         filter(Handin.hwid == hwid).
         join(User).
         group_by(Handin.user_id, Handin.state).
         having(Handin.state == 'Accepted'))

    # Show the report
    raw_headers = ['name', 'score']
    display_headers = [lazy_gettext('Username'), lazy_gettext('Score')]
    pagetitle = _('Scores for "%(hw)s"', hw=hw.info.name)
    filename = hw.info.name
    if (isinstance(filename, unicode)):
        filename = filename.encode('utf-8')

    # Pre-process the data
    # We need to display all users, even he does not submit anything!
    users = sorted(
        (u.name, u.id) for u in db.session.query(User.id, User.name)
    )
    user_scores = {}

    for rec in q:
        user_scores.setdefault(rec.user_id, 0.0)
        if (user_scores[rec.user_id] < rec.score):
            user_scores[rec.user_id] = round_score(rec.score)

    # Build data in user name ASC
    csvdata = [
        {
            'name': u[0],
            'score': user_scores.get(u[1], '-')
        }
        for u in users
    ]

    return make_csv_report(
        csvdata,
        display_headers,
        raw_headers,
        pagetitle,
        filename
    )


@bp.route('/buildcache/')
def buildcache():
    """Admin page to rebuild railgun cache."""
    io = StringIO()
    # HwCache
    task = HwCacheTask(logstream=io)
    task.execute()
    task.logflush()
    # TzCache
    io.write('-' * 70)
    io.write('\n')
    task = TzCacheTask(logstream=io)
    task.execute()
    task.logflush()

    return render_template('admin.maintain.html', task=task,
                           pagetitle=_('Build Cache'))

# Register the blue print
app.register_blueprint(bp, url_prefix='/admin')

# Register navibars
#
# We must make sure that admin navigates appear after view nagivates, so
# just import views before navigates.add
from . import views
navigates.add(
    NaviItem(
        title=lazy_gettext('Manage'),
        url=None,
        identity='admin',
        adminpage=True,
        subitems=[
            NaviItem.make_view(title=lazy_gettext('Users'),
                               endpoint='admin.users'),
            NaviItem.make_view(title=lazy_gettext('Submissions'),
                               endpoint='admin.handins'),
            NaviItem.make_view(title=lazy_gettext('Scores'),
                               endpoint='admin.scores'),
            NaviItem.make_view(title=lazy_gettext('Build Cache'),
                               endpoint='admin.buildcache'),
        ]
    )
)
