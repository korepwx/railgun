Website Package
===============

.. module:: railgun.website

This part of the documentation describes the website package.
It includes all parts of website implementation.


Flask Context Objects
---------------------

Most of the context objects are initialized in :mod:`railgun.website.context`.
Context objects are the controllers of the website.

.. automodule:: railgun.website.context
    :members:

However, there indeed exists some context objects initialized in other modules.
All the global context objects are listed in the following table:

.. tabularcolumns:: |p{9cm}|p{6cm}|

=================================================== ========================================
Object                                              Description
=================================================== ========================================
:data:`railgun.website.context.app`                 The WSGI application that acts as
                                                    the central object of the website.
:data:`railgun.website.context.csrf`                Protect the website from CSRF attack.
:data:`railgun.website.context.db`                  Bind a database session to each reqeust.
:data:`railgun.website.admin.bp`                    The blueprint for all admin views.
:data:`railgun.website.credential.login_manager`    Support login & logout to the website.
:data:`railgun.website.i18n.babel`                  Support translations of the website.
=================================================== ========================================


Database Models
---------------

.. automodule:: railgun.website.models

.. autoclass:: railgun.website.models.User
    :members:

.. autoclass:: railgun.website.models.Handin
    :members:

.. autoclass:: railgun.website.models.FinalScore
    :members:


Jinja2 Template Filters
-----------------------

.. automodule:: railgun.website.jinja_filters
    :members:


Jinja2 Context Functions and Variables
--------------------------------------

The following table lists all the functions and variables accessible in
a jinja context, in addition to the standard Flask configutaion.

=================== ========================================================
Object Name         Description
=================== ========================================================
current_user        Reference of :data:`flask.ext.login.current_user`.
                    If :func:`current_user.is_authenticated` is :data:`True`,
                    this object should also be an instance of
                    :class:`~railgun.website.credential.UserContext`.
allow_signup        A :class:`bool` configuration value indicating whether
                    user registration is allowed.
pagelng             Store the language name for current page.  You may use
                    this value to localization html elements, for example:

                    .. code-block:: html

                        <html lang="{{ pagelng }}">
                            ...
                        </html>
navibar             A :class:`~railgun.website.navibar.NavibarProxy` object.
renderPartialScore  Reference of function
                    :func:`~railgun.website.renders.renderPartialScore`.
=================== ========================================================


Flask View Decorators
----------------------

It's a common practice to decorate a view function so that the request
is validated, pre-processed or post-processed.  For example::

    @app.route('/')
    @login_required
    def index():
        return "Hello, %(name)s" % {'name': current_user.name}

The `index` view didn't check the credential of request user.  However,
being decorated by :func:`~railgun.website.credential.login_required`,
this validation is performed automatically, where un-authorized users
will be redirected to the login page.

The following table lists all the decorators available in the website:

.. tabularcolumns:: |p{5cm}|p{10cm}|

======================================================== =======================================================
Object                                                   Description
======================================================== =======================================================
:func:`~railgun.website.admin.admin_required`            Require the user to be an administrator.
:func:`~railgun.website.credential.login_required`       Require the user to login.
:func:`~railgun.website.credential.fresh_login_required` Require the user to re-validate their credential if the
                                                         session is remembered by the browser and is stale.
:func:`~railgun.website.api.secret_api`                  Decrypt the posted data and decode the plain text as
                                                         json text, and store the loaded object as
                                                         ``request.payload``.
:data:`~railgun.website.context.csrf`:token:`.exempt()`  Skip CSRF token validation for POSTed requests.
======================================================== =======================================================


Flask-Login Integration
-----------------------

.. automodule:: railgun.website.credential
    :members:

Common Utilities
----------------

.. automodule:: railgun.website.utility
    :members:


Translation Utilities
---------------------

.. automodule:: railgun.website.i18n
    :members:


WTF Form Models
---------------

.. automodule:: railgun.website.forms
    :members:


Views for Standard Users
------------------------

Some of the views support extra arguments in the query string.  For example,
the login page support an extra `next` argument, representing what url to
redirect to after the user has successfully logged in::

    /signin/?next=http%3A//www.baidu.com

Which will redirect the logged user to `www.baidu.com`.  Other modules may
accept `page` and `perpage` arguments, to define the behaviour of page
navigation.


.. automodule:: railgun.website.views
    :members:


Views for Administrators
------------------------

.. automodule:: railgun.website.admin
    :members:


Views for WebAPI
----------------

.. automodule:: railgun.website.api
    :members:
