# -*- coding: UTF-8 -*-
"""
Flask-Redis
~~~~~~~~~~~

Utilise Redis in your Flask application
"""
from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup

from flask_redis import __version__

setup(
    name='Flask-Redis',
    version=__version__,
    packages=['flask_redis'],
    url='https://github.com/netzinformatik/Flask-Redis',
    license='BSD',
    author='Tobias Werner',
    author_email='mail@tobiaswerner.net',
    description='Utilise Redis in your Flask application',
    long_description=__doc__,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'Flask',
        'redis',
    ],
    setup_requires=[
        'nose>=1.0',
        'mock'
    ],
    test_suite='nose.collector',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Environment :: Web Environment',
        'Framework :: Flask',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: German',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',

    ]
)
