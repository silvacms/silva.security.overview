# -*- coding: utf-8 -*-
# Copyright (c) 2012  Infrae. All rights reserved.
# See also LICENSE.txt
from setuptools import setup, find_packages
import os

version = '1.2dev'

tests_require = [
    'Products.Silva [test]',
    ]

setup(name='silva.security.overview',
      version=version,
      description="Extension providing a global overview of the permissions granted to users in the Silva CMS",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      classifiers=[
        "Framework :: Zope2",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='silva cms zope security',
      author='Infrae',
      author_email='info@infrae.com',
      url='https://github.com/silvacms/silva.security.overview',
      license='BSD',
      package_dir={'': 'src'},
      packages=find_packages('src', exclude=['ez_setup']),
      namespace_packages=['silva', 'silva.security'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'five.grok',
        'five.intid',
        'setuptools',
        'silva.batch',
        'silva.core.conf',
        'silva.core.interfaces',
        'silva.core.services',
        'silva.core.views',
        'silva.fanstatic',
        'zeam.form.silva',
        'zeam.utils.batch >= 1.0',
        'zope.cachedescriptors',
        'zope.catalog',
        'zope.component',
        'zope.container',
        'zope.index',
        'zope.interface',
        'zope.intid',
        'zope.lifecycleevent',
        'zope.schema',
        ],
      tests_require = tests_require,
      extras_require = {'test': tests_require},
      )
