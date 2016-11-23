==========
foundation
==========

The Problem
-----------

**Django** clearly defines the following paradigms (amongst others):

- Object-Relational Mapping (ORM) via Models
- Request Routing via URLs
- Data Binding via Forms
- Request-to-Response Mapping via Views
- Data Presentation via Templates

While this explicit control over the design and function of each component is
optimal for many use cases, one could argue that it runs afould of Django's
most desirable design principle: "Don't Repeat Yourself" (DRY).  More
to the point, while Django ships with an admin app that most new users rave
about, there is no obvious way to expose a front-end without a fair amount of
work (especially when auth or comprehension of model interrelationships is
desired) that could be simplified greatly if there was a central class through
which those interrelationships were managed.

Many approaches set out to solve this through class methods on the Models or
their Managers, but that runs counter to the spirit of segregating the Model
(intended to be a representation of the state of the DB) from logic (typically
housed in Views or Forms).  At the same time, each of those pieces is intended
to only have a comprehension of a single Model and not the interrelationships
between said Models, resulting, for instance, in an inability to have a given
implementation accomodate more than one relation that a developer may desire
to expose to the end-user.

A Solution
----------

**foundation** sets out to provide a single Backend per Django Site (website)
with Controllers specified per-model and the interrelationships between those
Controllers serving as:

- the Model (DB) access layer (via Model Manager and QuerySet)
- the View generation *and* access layer (via Class-Based Views which are, in
  their own right, Controllers)
- the Form(Set) generation layer
- the access-control layer
- the URL specification layer

This design is inspired by Django's own admin app, as well as the design
patterns of other MVC platforms.  It aims to re-use as much work from admin
out of laziness and, more importantly, a belief of mine that the admin should
be sitting atop the foundation, not the all-to-often mistake new users make of
attempting to expose a front-end from within admin.

How it works
------------

If you are not already familiar with how Django sets itself up and processes a
request, here are two links of interest:

- `Initialization Process`_
- `Processing a Request`_

.. _`Initialization Process`: https://docs.djangoproject.com/en/1.10/ref/applications/#initialization-process
.. _`Processing a Request`: https://docs.djangoproject.com/en/1.10/topics/http/urls/#how-django-processes-a-request

In addition to the above, foundation does the following during initialization:

- foundation should be installed under all project apps to ensure the Backend
  instance is in a good state prior to being referenced.  Additionally, the
  app config file is a good place to instantiate your own Backend subclass if
  you want to ensure any behaviors are baked into the backend used site-wide.
- Once applications are ready, the foundation application's ready signal will
  fire, which will autodiscover all of the controllers modules/packages in each
  installed app.  Additionally, permission creation for any new models will be
  initiated if that feature is enabled, or you can manage that in your own app
  code where appropriate (or if you implement your own permissions scheme).
- Finally, the URL configuration(s) are configured.  For many sites, this means
  you can replace the settings ROOT_URLCONF with a path to your backend's "urls"
  attribute, although you may append it to the list of urlpatterns in the
  project "urls" module to provide flexibility in adding other url specs (e.g.
  admin).  When the "urls" attribute is accessed, it will perform a single pass
  through all of the Controllers to accumulate the appropriate URL paths in
  namespaced patterns.  At this time, all of the class-based view (CBV) base
  classes will also be constructed, which will in turn be generated into
  callables just-in-time (JIT) by calling their "as_view" method (same as stock
  Django).

Since it is operating entirely within the context of a CBV at this point, the
rest of what foundation does is essentially overriding stock django CBV
methods, although there are some important behaviors to note that are possible
because of the controller interrelationships.  Most notably, the Django CBV
"dispatch" behavior has been universally extended by two components.

#. A "get_handler" method is provided which allows for a given view to handle
   a request using other than the CBV's standard HTTP-method-named methods.

#. A "handle_common" method is provided which allows for activities common to
   some or all HTTP methods (e.g. auth, QS grooming) to be performed prior to
   calling downstream methods to remove redundancy and clutter from those
   methods.

In trying to keep with some of the paradigms set forth in django-admin, this
means that for any controller- (and thus, model-) aware view, that a view "mode"
is set (e.g. add, edit, view) as well as an "edit" and "add" flag to
specifically indicate whether the view is used for editing or creation.  These
will likely move further down the stack to only be present in "html-form-aware"
views and better accommodate AJAX and RESTful views.

Additionally, handle_common is where a common layer of authentication and
access-control logic occurs.  This ensures downstream views are guaranteed to
have a common logical layer invoked prior to serving a response.  By default,
the access control ships with awareness of predefined (and overridable) "public"
and "private" named views (e.g. list and view are public while add, edit, and
delete are private).  Additionally, it provides a contextual switch so that
superusers must elect to "act" as superusers, otherwise they will be subject to
the same rules as non-superusers.
