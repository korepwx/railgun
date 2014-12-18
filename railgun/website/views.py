#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/website/views.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

import os
import uuid

from flask import (render_template, url_for, redirect, flash, request, g,
                   send_from_directory)
from flask.ext.babel import lazy_gettext, get_locale, gettext as _
from flask.ext.login import (login_user, logout_user, current_user,
                             confirm_login)
from sqlalchemy import func
from sqlalchemy.orm import contains_eager
from werkzeug.exceptions import NotFound, Forbidden

from .context import app, db
from .navibar import navigates, NaviItem, set_navibar_identity
from .forms import SignupForm, SigninForm, ProfileForm, ReAuthenticateForm
from .credential import (UserContext, login_required, fresh_login_required,
                         should_update_email, redirect_update_email)
from .userauth import authenticate, auth_providers
from .codelang import languages
from .models import User, Handin, Vote, VoteItem, UserVote
from .manual import translated_page, translated_page_source


@app.route('/')
def index():
    """The index page that displays the jumbotron to anonymous users,
    and show the scores of submitted homework to login user.

    :route: /
    :method: GET
    :template: index.html
    """
    # check user email when authenticated
    if current_user.is_authenticated():
        if should_update_email():
            return redirect_update_email()
    return render_template('index.html')


@app.route('/signup/', methods=['GET', 'POST'])
def signup():
    """The form page for anonymous user to create a new account.

    If the requested operation is successful, the user will be redirected
    to :func:`signin` view.  You may disable the registration by setting
    ``config.ALLOW_SIGNUP`` to :data:`False`, where a 403 http error will
    be responded to request users.

    :route: /signup/
    :method: GET, POST
    :template: signup.html
    :form: :class:`~railgun.website.forms.SignupForm`
    """
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
    """The form page for users to login.

    If the credential passes validation, the user will be redirected to
    :func:`index` view, unless the `next` argument is given in the query
    string, where a redirection to `next` will take place.

    :route: /signin/
    :method: GET, POST
    :template: signin.html
    :form: :class:`~railgun.website.forms.SigninForm`
    """
    form = SigninForm()
    next_url = request.args.get('next')
    if form.validate_on_submit():
        # Check whether the user exists
        user = authenticate(form.login.data, form.password.data)
        if user:
            if user.is_active:
                # Now we can login this user and redirect to index!
                login_user(UserContext(user), remember=form.remember.data)
                return redirect(next_url or url_for('index'))
            flash(_('Your account is locked by admin.'), 'warning')
        else:
            flash(_('Incorrect username or password.'), 'danger')
    return render_template('signin.html', form=form, next=next_url)


@app.route('/reauthenticate/', methods=['GET', 'POST'])
@login_required
def reauthenticate():
    """The form page to ask user enter their password to revalidate their
    stale session.

    If a user let the system remember his or her login at :func:`signup`,
    we then call it a persistent session.  This is because such session
    will not be expired within just hours of time, nor will it become
    invalid after quitting the browser.

    We call a recovered session after a relaunch of the browser or time
    expiration a stale session.  Sometimes we may want to make sure the
    user owns the permission before taking any operations. In these
    situations, the stale sessions are not enough.

    So :class:`reauthenticate` view force the user to refresh their stale
    session.  You may decorate the view by
    :func:`~railgun.website.credential.fresh_login_required` to ensure
    this.

    If the credential passes validation, the user will be redirected to
    :func:`index` view, unless the `next` argument is given in the query
    string, where a redirection to `next` will take place.

    :route: /reauthenticate/
    :method: GET, POST
    :template: reauthenticate.html
    :form: :class:`~railgun.website.forms.ReAuthenticateForm`
    """
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
    """Sign out the logged user, and redirect to :func:`index` view.

    :route: /signout/
    :method: GET
    """
    logout_user()
    return redirect(url_for('index'))


@app.route('/profile/edit/', methods=['GET', 'POST'])
@fresh_login_required
def profile_edit():
    """The form page for the user to edit their profile.

    For the accounts from third-party authentication providers, some fields
    of the form may be locked and cannot be modified.  This feature isn't
    implemented here, but in :mod:`railgun.website.userauth`.

    You may refer to :func:`railgun.website.userauth.AuthProvider.init_form`
    for more details.

    :route: /profile/edit/
    :method: GET, POST
    :template: profile_edit.html
    :form: :class:`railgun.website.forms.ProfileForm`
    """
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
    """The page to show homework detail, and to upload submissions.

    If the homework is locked, then a standard user cannot download the
    attachment, nor can he or she upload submissions.  If the homework
    is hidden, then a standard user will receive an http 404 error.
    However, admins can always view all homework and upload submissions.

    The number of pending and running submissions for a single user
    uploaded to a single homework is restricted by
    ``config.MAX_USER_PENDING_PER_HW``.  If this limit exceeds, submissions
    will be rejected.

    Submissions that have passed all deadlines are rejected as well.

    If everything is okay, then the submission will be queued into the
    runner queue.  There exists a controller in :mod:`~railgun.website`
    package to deliver submissions in different programming languages
    to their desired destination.  Such controller is implemented in
    :mod:`railgun.website.codelang`.  You may refer to
    :func:`railgun.website.codelang.CodeLanguage.handle_upload`
    for more details.

    When ``config.STORE_UPLOAD`` is set to :data:`True`, the original
    submission from user will be stored into ``config.UPLOAD_STORE_DIR``,
    where the user may download their submissions from :class:`handin_detail`
    view.

    After submitted successfully, the user will be redirected to
    :func:`~railgun.website.views.hwhandins`.

    :route: /homework/<slug>/
    :method: GET, POST
    :template: homework.html
    :form: Generated by :class:`railgun.website.codelang.CodeLanguage`
    :naviId: homework.\<slug\>

    :param slug: The url slug of the requested homework.
    :type slug: :class:`str`
    """

    # set the identity for navibar (so that current page will be activated)
    set_navibar_identity('homework.%s' % slug)
    # load requested homework instance
    hw = g.homeworks.get_by_slug(slug)
    if not hw:
        raise NotFound()
    # hidden homeworks should only be viewed by admins
    if hw.is_hidden() and not current_user.is_admin:
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
                    handid,
                    hw,
                    forms[handin_lang]
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
@login_required
def hwpack(slug, lang):
    """The attachment of a homework in given programming language.

    If the request user is not an adminstrator, and the homework is locked,
    the user will get a 403 error.  If the homework is hidden, the user
    will get a 404 error as if it does not exist.

    The attachments will not be packed into archive files automatically.
    You should execute ``manage.py build-cache`` to cache the archive
    files manually (which will be stored in ``config.HOMEWORK_PACK_DIR``).

    :route: /hwpack/<slug>/<lang>.zip
    :method: GET

    :param slug: The url slug of requested homework.
    :type slug: :class:`str`
    :param lang: The attachment programming language.
    :type lang: :class:`str`
    """
    # attachments of locked homework should not be downloaded by non-admin
    # users.  so we get the homework object, and check the privilege.
    hw = g.homeworks.get_by_slug(slug)
    if not hw:
        raise NotFound()
    if hw.is_hidden() and not current_user.is_admin:
        raise NotFound()
    if hw.is_locked() and not current_user.is_admin:
        raise Forbidden()
    # if user can download this attachment, send it.
    filename = '%(slug)s/%(lang)s.zip' % {'slug': slug, 'lang': lang}
    return send_from_directory(app.config['HOMEWORK_PACK_DIR'], filename)


@app.route('/hwstatic/<path:filename>')
def hwstatic(filename):
    """Serve the static resources of all homework descriptions.
    You may refer to :ref:`hwdesc` to see which files will be exposed, and
    how to use these resources in homework descriptions.

    The resources should be gathered into ``config.HOMEWORK_STATIC_DIR``
    manually, by executing ``manage.py build-cache``.  In addition, you may
    use a static http server, like nginx, to serve these files instead of
    a WSGI application server.

    :route: /hwstatic/<path:filename>
    :method: GET

    :param filename: The relative file path of homework static resource.
    :type filename: :class:`str`
    """
    return send_from_directory(app.config['HOMEWORK_STATIC_DIR'], filename)


@app.route('/homework/<slug>/handin/')
@login_required
def hwhandins(slug):
    """The page to list all submissions to a homework assignment uploaded
    by current user.  If the homework has been deleted, send 404 http error
    to request user.

    This page supports page navigation, thus accepts `page` and `perpage`
    query string argument, where `page` defines the navigated page id
    (>= 1), and `perpage` defines the page size (default 10).

    :route: /homework/<slug>/handin/
    :method: GET
    :template: homework.handins.html
    :naviId: homework.<slug>.handin

    :param slug: The url slug of requested homework.
    :type slug: :class:`str`
    """
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
    """View the submission detailed report.
    If the submission is not owned by current user, nor is current user an
    administrator, then this view will send a 404 http error to request user.

    If the submission file was stored in ``config.UPLOAD_STORE_DIR``, a link
    will be displayed to let the user download original file.

    :route: /handin/<uuid>/
    :method: GET
    :template: handin_detail.html

    :param uuid: The submission uuid.
    :type uuid: :class:`str`
    """
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
    """Download the original submission file.
    If the submission is not owned by current user, nor is current user an
    administrator, then this view will send a 404 http error to request user.

    All the original submission files should be stored in
    ``config.UPLOAD_STORE_DIR``, if ``config.STORE_UPLOAD`` is set to
    :data:`True`.

    :route: /handin/<uuid>/download/
    :method: GET
    """

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


@app.route('/manual/userguide/')
def userguide():
    """The user's guide page in request locale.
    You may refer to :func:`~railgun.website.manual.translated_page` for more
    details about the translated manual page.

    :route: /manual/userguide/
    :method: GET
    :template: manual.html, manual/userguide/<lang>.md
    """
    return translated_page('userguide')


@app.route('/manual/userguide/source/')
def userguide_source():
    """The user's guide source code page in request locale.
    You may refer to :func:`~railgun.website.manual.translated_page_source`
    for more details about the translated manual source code page.

    :route: /manual/userguide/source/
    :method: GET
    """
    return translated_page_source('userguide')


@app.route('/manual/scores/')
def scores():
    """The scoring rules page in request locale.
    You may refer to :func:`~railgun.website.manual.translated_page` for more
    details about the translated manual page.

    :route: /manual/scores/
    :method: GET
    :template: manual.html, manual/scores/<lang>.md
    """
    return translated_page('scores')


@app.route('/manual/scores/source/')
def scores_source():
    """The scoring rules source code page in request locale.
    You may refer to :func:`~railgun.website.manual.translated_page_source`
    for more details about the translated manual source code page.

    :route: /manual/scores/source/
    :method: GET
    """
    return translated_page_source('scores')


@app.route('/manual/faq/')
def faq():
    """The faq page in request locale.
    You may refer to :func:`~railgun.website.manual.translated_page` for more
    details about the translated manual page.

    :route: /manual/faq/
    :method: GET
    :template: manual.html, manual/faq/<lang>.md
    """
    return translated_page('faq')


@app.route('/manual/faq/source/')
def faq_source():
    """The faq source code page in request locale.
    You may refer to :func:`~railgun.website.manual.translated_page_source`
    for more details about the translated manual source code page.

    :route: /manual/faq/source/
    :method: GET
    """
    return translated_page_source('faq')


@app.route('/manual/about/')
def about():
    """The about page in request locale.
    You may refer to :func:`~railgun.website.manual.translated_page` for more
    details about the translated manual page.

    :route: /manual/about/
    :method: GET
    :template: manual.html, manual/about/<lang>.md
    """
    return translated_page('about')


@app.route('/manual/about/source/')
def about_source():
    """The about source code page in request locale.
    You may refer to :func:`~railgun.website.manual.translated_page_source`
    for more details about the translated manual source code page.

    :route: /manual/about/source/
    :method: GET
    """
    return translated_page_source('about')


@app.route('/docs/')
def docs_index():
    """The index page of the documentation.

    Documentation pages should be placed at `docs/_build/html`.
    You may generate the documentation files by executing ``make html`` under
    `docs` directory.

    :route: /docs/
    :method: GET
    """
    return send_from_directory(
        os.path.join(app.config['RAILGUN_ROOT'], 'docs/_build/html'),
        'index.html'
    )


@app.route('/docs/<path:filename>')
def docs_static(filename):
    """The static resources of the documentation.

    :route: /docs/
    :method: GET
    """
    return send_from_directory(
        os.path.join(app.config['RAILGUN_ROOT'], 'docs/_build/html'),
        filename
    )


@app.route('/vote/', methods=['GET', 'POST'])
@login_required
def vote_index():
    """The page to display vote options to the user.

    :route: /vote/
    :method: GET, POST
    :template: vote_index.html
    """
    vote = Vote.query.filter().first()
    if not vote:
        raise NotFound()
    # check whether the vote has ended
    if not vote.is_open:
        flash(_('Vote is not open, you can only view the result.'), 'warning')
        return redirect(url_for('vote_result'))

    item_ids = [i.id for i in vote.items]
    user_votes = UserVote.query.filter(UserVote.user_id == current_user.id,
                                       UserVote.vote_item_id.in_(item_ids))
    has_any_logo = sum(i.logo is not None for i in vote.items) > 0
    selected_ids = [i.vote_item_id for i in user_votes]

    # if the method is POST, we check the user input
    if request.method == 'POST':
        # gather the selected ids
        selected_ids = []
        for k, v in request.form.iteritems():
            if k.startswith('vote-item-'):
                itm_id = int(k[10:])
                selected_ids.append(itm_id)
        # check whether the min & max selection exeeds
        selected_ids = set(selected_ids)
        if len(selected_ids) > vote.max_select:
            flash(_("You can only vote for at most %(max)s items.",
                    max=vote.max_select))
        elif len(selected_ids) < vote.min_select:
            flash(_("You should at least vote for %(min)s items.",
                    min=vote.min_select))
        else:
            exist_votes = set(i.vote_item_id for i in user_votes)
            # if idx already voted but not in this request, delete it
            for itm in user_votes:
                if itm.vote_item_id not in selected_ids:
                    db.session.delete(itm)
            # if idx in selected ids but not in db, add it
            for idx in selected_ids:
                if idx not in exist_votes:
                    db.session.add(
                        UserVote(vote_item_id=idx, user_id=current_user.id))
            # now submit it!
            try:
                db.session.commit()
                flash(_('You voted successfully!'), 'success')
                return redirect(url_for('vote_result'))
            except Exception:
                app.logger.exception('Error when updating user vote')
                flash(_('Internal server error, please try again.'), 'danger')

    return render_template('vote_index.html', vote=vote, user_votes=user_votes,
                           has_any_logo=has_any_logo, selected=selected_ids)


@app.route('/vote/result/')
@login_required
def vote_result():
    """The page to display vote result to the user.

    :route: /vote/result/
    :method: GET
    :template: vote_result.html
    """
    vote = Vote.query.filter().first()
    if not vote:
        raise NotFound()

    # total up the votes for each item
    q = (db.session.query(VoteItem.id, func.count(UserVote.user_id).label('C')).
         join(UserVote).
         filter(VoteItem.vote_id == vote.id).
         group_by(UserVote.vote_item_id))
    vote_count = {k: v for (k, v) in q.all()}
    print vote_count

    def C(a, b):
        t = -cmp(a[1], b[1])
        if t == 0:
            t = cmp(a[0].id, b[0].id)
        return t
    vote_items = sorted(
        ((itm, vote_count.get(itm.id, 0))
         for itm in VoteItem.query.filter(VoteItem.vote_id == vote.id).all()),
        cmp=C
    )

    # check the vote objects
    has_any_logo = sum(i[0].logo is not None for i in vote_items)
    max_count = max([0] + [i[1] for i in vote_items])
    if max_count > 0:
        percent = [float(i[1]) / max_count for i in vote_items]
    else:
        percent = [0] * len(vote_items)

    return render_template(
        'vote_result.html', items=vote_items, has_any_logo=has_any_logo,
        max_count=max_count, percent=percent)


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
                url=(app.config['ONLINE_DOC_URL'] or
                     (lambda: url_for('docs_index'))),
                identity='documentation',
            ),
            NaviItem.make_view(title=lazy_gettext('FAQ'),
                               endpoint='faq'),
            NaviItem.make_view(title=lazy_gettext('About'),
                               endpoint='about'),
        ]
    )
)
