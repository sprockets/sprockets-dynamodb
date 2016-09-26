#!/usr/bin/env python
#

import os.path
import setuptools

from sprockets_dynamodb import __version__


def read_requirements(filename):
    requirements = []
    try:
        with open(os.path.join('requires', filename)) as req_file:
            for line in req_file:
                if '#' in line:
                    line = line[:line.index('#')]
                line = line.strip()
                if line.startswith('-r'):
                    requirements.extend(read_requirements(line[2:].strip()))
                elif line:
                    requirements.append(line)
    except IOError:
        pass
    return requirements


setuptools.setup(
    name='sprockets-dynamodb',
    version=__version__,
    description='DynamoDB client and mixin for Tornado applications',
    author='AWeber Communications',
    author_email='api@aweber.com',
    url='https://github.com/sprockets/sprockets-dynamodb',
    install_requires=read_requirements('installation.txt'),
    license='BSD',
    packages=['sprockets_dynamodb'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules'],
    test_suite='nose.collector',
    tests_require=read_requirements('testing.txt'),
    extras_require={
        'influxdb': ['sprockets-influxdb>=1.2.0,<2']
    },
    zip_safe=True
)
