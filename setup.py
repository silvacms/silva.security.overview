from setuptools import setup, find_packages
import os

version = '1.0dev'

setup(name='silva.security.overview',
      version=version,
      description="Security overview",
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
      url='http://infrae.com/products/silva',
      license='BSD',
      package_dir={'': 'src'},
      packages=find_packages('src', exclude=['ez_setup']),
      namespace_packages=['silva', 'silva.security'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'setuptools',
        'zope.intid',
        'zope.index',
        'zope.catalog',
        'silva.core.services'
        'silva.core.conf',
        'silva.core.interfaces',
        'silva.core.views',
        ],
      )
