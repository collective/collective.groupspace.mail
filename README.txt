Introduction
============

This is an extension for the GrufSpaces product that allows participants to send email to specific members.

groupspace.mail Installation
----------------------------

To install groupspace.mail into the global Python environment (or a workingenv),
using a traditional Zope 2 instance, you can do this:

* When you're reading this you have probably already run
  ``easy_install groupspace.mail``. Find out how to install setuptools
  (and EasyInstall) here:
  http://peak.telecommunity.com/DevCenter/EasyInstall

* Create a file called ``groupspace.mail-configure.zcml`` in the
  ``/path/to/instance/etc/package-includes`` directory.  The file
  should only contain this::

    <include package="groupspace.mail" />


Alternatively, if you are using zc.buildout and the plone.recipe.zope2instance
recipe to manage your project, you can do this:

* Add ``groupspace.mail`` to the list of eggs to install, e.g.:

    [buildout]
    ...
    eggs =
        ...
        groupspace.mail

* Tell the plone.recipe.zope2instance recipe to install a ZCML slug:

    [instance]
    recipe = plone.recipe.zope2instance
    ...
    zcml =
        groupspace.mail

* Re-run buildout, e.g. with:

    $ ./bin/buildout

You can skip the ZCML slug if you are going to explicitly include the package
from another package's configure.zcml file.
