# -*- coding: utf-8 -*-
"""
collective.groupspace.mail
"""
import os
from setuptools import setup
from setuptools import find_packages

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

version  = '1.0'

long_description = (
    read('README.txt')
    + '\n\n' +
    read('CHANGES.txt')
    )

tests_require=['zope.testing']

setup(name='collective.groupspace.mail',
    version=version ,
    description="Mail service for the GroupSpace content type",
    long_description=long_description,
    classifiers=[
      "Development Status :: 4 - Beta",
      "Environment :: Web Environment",
      "Framework :: Plone",
      "Framework :: Zope2",
      "Intended Audience :: Developers",
      "License :: OSI Approved :: GNU General Public License (GPL)",
      "Operating System :: OS Independent",
      "Programming Language :: Python",
      "Topic :: Communications :: Email",
      "Topic :: Internet :: WWW/HTTP :: Dynamic Content",        
      "Topic :: Office/Business :: Groupware",
      "Topic :: Software Development :: Libraries :: Python Modules",
        ],
    keywords='groupspace, roles, pas, borg.localrole, grufspaces',
    author='Maik Röder',
    author_email='roeder@berg.net',
    url='http://svn.plone.org/svn/collective/collective.groupspace.mail',
    license='GPL',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=['collective', 'collective.groupspace'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        # -*- Extra requirements: -*-
    ],
    tests_require=tests_require,
    extras_require=dict(tests=tests_require),
    entry_points="""
      # -*- entry_points -*-
      [z3c.autoinclude.plugin]
      target = plone
      """,
    setup_requires=["PasteScript"],
    paster_plugins = ["ZopeSkel"],
    )
