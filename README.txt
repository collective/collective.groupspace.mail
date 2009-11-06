Introduction
============

Implements a mail tab for any content type implementing the ILocalGroupSpacePASRoles
interface, This interface allows managemment of dynamic roles for users and groups
in a context, and is implemented in collective.groupspace.roles. An example content 
type providing a mail tab is contained in collective.groupspace.content.

The tab looks like the standard Plone "Send this page to someone" interface, but
instead of manually filling in an email address, you can choose the recipients of
the message from a list of participants that have a role in the context of
your content type.

This package is part of the collective.groupspace suite, whose components should
be installed as needed:

* collective.groupspace.content

* collective.groupspace.roles

* collective.groupspace.mail

