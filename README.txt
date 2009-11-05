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

collective.groupspace.mail Installation
---------------------------------------

To install collective.groupspace.mail into the global Python environment (or a workingenv),
using a traditional Zope 2 instance, you can do this:

* When you're reading this you have probably already run
  ``easy_install collective.groupspace.mail``. Find out how to install setuptools
  (and EasyInstall) here:
  http://peak.telecommunity.com/DevCenter/EasyInstall

* Create a file called ``collective.groupspace.mail-configure.zcml`` in the
  ``/path/to/instance/etc/package-includes`` directory.  The file
  should only contain this::

    <include package="collective.groupspace.mail" />


Alternatively, if you are using zc.buildout and the plone.recipe.zope2instance
recipe to manage your project, you can do this:

* Add ``collective.groupspace.mail`` to the list of eggs to install, e.g.:

    [buildout]
    ...
    eggs =
        ...
        collective.groupspace.mail

* Tell the plone.recipe.zope2instance recipe to install a ZCML slug:

    [instance]
    recipe = plone.recipe.zope2instance
    ...
    zcml =
        collective.groupspace.mail

* Re-run buildout, e.g. with:

    $ ./bin/buildout

You can skip the ZCML slug if you are going to explicitly include the package
from another package's configure.zcml file.
