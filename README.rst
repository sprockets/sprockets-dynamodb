Sprockets DynamoDB
==================
An asynchronous DynamoDB client and mixin for Tornado applications

|Version| |Downloads| |Status| |Coverage| |License|

Installation
------------
``sprockets-dynamodb`` is available on the Python package index and is installable via pip:

.. code:: bash

    pip install sprockets-dynamodb

Documentation
-------------
Documentation is available at `sprockets-dynamodb.readthedocs.io <https://sprockets-dynamodb.readthedocs.io>`_.

Configuration
-------------
The following table details the environment variable configuration options.

+--------------------------+--------------------------------------------------------------------+---------+
| Variable                 | Definition                                                         | Default |
+==========================+====================================================================+=========+
| ``DYNAMODB_ENDPOINT``    | Override the default DynamoDB HTTP endpoint                        |         |
+--------------------------+--------------------------------------------------------------------+---------+
| ``DYNAMODB_MAX_CLIENTS`` | Maximum number of concurrent DynamoDB clients/requests per process | ``100`` |
+--------------------------+--------------------------------------------------------------------+---------+
| ``DYNAMODB_MAX_RETRIES`` | Maximum number retries for transient errors                        | ``3``   |
+--------------------------+--------------------------------------------------------------------+---------+

Mixin Configuration
^^^^^^^^^^^^^^^^^^^
The ``sprockets_dynamodb.mixins.DynamoDBMixin`` class will automatically raise ``HTTPError``
responses for different classes of errors coming from DynamoDB. In addition it will attempt to
work with the `Sprockets InfluxDB <https://github.com/sprockets/sprockets-influxdb>`_ client
to instrument all DynamoDB requests, submitting per request measurements to InfluxDB. It will
attempt to automatically tag measurements with the application/service name if the ``SERVICE``
environment variable is set. It will also tag the measurement if the ``ENVIRONMENT`` environment
variable is set with the environment that the application is running in. Finally, if you are
using the `Sprockets Correlation Mixin <https://github.com/sprockets/sprockets.mixins.correlation>`_,
measurements will automatically be tagged with the correlation ID for a request.

Requirements
------------
-  `Tornado <https://tornadoweb.org>`_
-  `tornado-aws <https://pypi.python.org/pypi/tornado-aws>`_

Version History
---------------
Available at https://sprockets-dynamodb.readthedocs.org/en/latest/history.html

.. |Version| image:: https://img.shields.io/pypi/v/sprockets-dynamodb.svg?
   :target: http://badge.fury.io/py/sprockets-dynamodb

.. |Status| image:: https://img.shields.io/travis/sprockets/sprockets-dynamodb.svg?
   :target: https://travis-ci.org/sprockets/sprockets-dynamodb

.. |Coverage| image:: https://img.shields.io/codecov/c/github/sprockets/sprockets-dynamodb.svg?
   :target: https://codecov.io/github/sprockets/sprockets-dynamodb?branch=master

.. |Downloads| image:: https://img.shields.io/pypi/dm/sprockets-dynamodb.svg?
   :target: https://pypi.python.org/pypi/sprockets-dynamodb

.. |License| image:: https://img.shields.io/pypi/l/sprockets-dynamodb.svg?
   :target: https://sprockets-dynamodb.readthedocs.org
