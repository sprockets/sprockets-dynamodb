.. :changelog:

Release History
===============

`2.0.0`_ (17 Oct 2016)
----------------------
- Breaking API change for Client.get_item to allow for return values for ConsumedCapacity
- Implement Client.delete_item, Client.update_item, Client.query, Client.scan
- Improved parameter validation

`1.1.0`_ (12 Oct 2016)
----------------------
- Remove the service tag in InfluxDB
- Remove the correlation-id field value
- Collect all of the paged query results

`1.0.2`_ (26 Sep 2016)
----------------------
- Fix a mixin InfluxDB integration issue

`1.0.1`_ (26 Sep 2016)
----------------------
- Make ``DynamoDBMixin`` available from ``sprockets_dynamodb``

`1.0.0`_ (26 Sep 2016)
----------------------
- Initial release

`Next Release`_
---------------

.. _Next Release: https://github.com/sprockets/sprockets_dynamodb/compare/2.0.0...master
.. _2.0.0: https://github.com/sprockets/sprockets-dynamodb/compare/1.1.0...2.0.0
.. _1.1.0: https://github.com/sprockets/sprockets-dynamodb/compare/1.0.2...1.1.0
.. _1.0.2: https://github.com/sprockets/sprockets-dynamodb/compare/1.0.1...1.0.2
.. _1.0.1: https://github.com/sprockets/sprockets-dynamodb/compare/1.0.0...1.0.1
.. _1.0.0: https://github.com/sprockets/sprockets-dynamodb/compare/0.0.0...1.0.0
