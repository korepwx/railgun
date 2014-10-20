Website Package
===============

.. module:: railgun.website

This part of the documentation describes the website package.
It includes all parts of website implementation.

Database Models
---------------

.. automodule:: railgun.website.models

.. autoclass:: railgun.website.models.User
    :members:

.. autoclass:: railgun.website.models.Handin
    :members:

.. autoclass:: railgun.website.models.FinalScore
    :members:


Flask Context Objects
---------------------

.. data:: railgun.website.context.app

    A :class:`~flask.Flask` object.  It implements a WSGI application and acts
    as the central object of the website.

.. data:: railgun.website.context.csrf

    A :class:`flask_wtf.csrf.CsrfProtect` object.  It extends the
    :data:`~railgun.website.context.app` so that all post requests will be
    protected from csrf attack, unless disabled explicitly.

.. data:: railgun.website.context.db

    A :class:`flask.ext.sqlalchemy.SQLAlchemy` object.  It extends the
    :data:`~railgun.website.context.app` so that each request will bind
    a database session.

.. data:: railgun.website.admin.bp

    A :class:`~flask.Blueprint` object.  All the views for administration
    are registered to this blueprint.

.. data:: railgun.website.credential.login_manager

    A :class:`flask.ext.login.LoginManager` object.  It extends the
    :data:`~railgun.website.context.app` to support login & logout.

.. data:: railgun.website.i18n.babel

    A :class:`flask.ext.babel.Babel` object.  It extends the
    :data:`~railgun.website.context.app` to support translations for
    each request.


Jinja2 Template Filters
-----------------------

.. module::

.. function:: timedelta(delta_or_date)

    Format :class:`~datetime.datetime` or :class:`~datetime.timedelta`
    into localized string.

    If given parameter is a :class:`~datetime.datetime`, 
    it will be subtracted by :func:`railgun.common.dateutil.utcnow` to
    get the :class:`~datetime.timedelta`.

    :param delta_or_date: A :class:`~datetime.datetime` or a
        :class:`~datetime.timedelta` object.
    :return: :token:`None` if `delta_or_date` is `None`, otherwise the
        localized timedelta string.

    

Common Utility for Single Requests
----------------------------------

