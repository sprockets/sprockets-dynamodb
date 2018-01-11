import collections
import datetime
import logging
import os
import random
import socket
import sys
import uuid
import unittest

import mock

from tornado import concurrent
from tornado import gen
from tornado import httpclient
from tornado import locks
from tornado import testing
from tornado_aws import exceptions as aws_exceptions

import sprockets_dynamodb as dynamodb
from sprockets_dynamodb import utils

LOGGER = logging.getLogger(__name__)

os.environ['ASYNC_TEST_TIMEOUT'] = '30'


class AsyncTestCase(testing.AsyncTestCase):

    def setUp(self):
        super(AsyncTestCase, self).setUp()
        self.client = self.get_client()
        self.client.set_error_callback(None)
        self.client.set_instrumentation_callback(None)

    @gen.coroutine
    def create_table(self, definition):
        response = yield self.client.create_table(definition)
        yield self.wait_on_table_creation(definition['TableName'], response)

    @gen.coroutine
    def wait_on_table_creation(self, table_name, response):
        while not self._table_is_ready(response):
            LOGGER.debug('Waiting on %s to become ready', table_name)
            yield gen.sleep(1)
            response = yield self.client.describe_table(table_name)

    @property
    def endpoint(self):
        return os.getenv('DYNAMODB_ENDPOINT')

    @staticmethod
    def generic_table_definition():
        return {
            'TableName': str(uuid.uuid4()),
            'AttributeDefinitions': [{'AttributeName': 'id',
                                      'AttributeType': 'S'}],
            'KeySchema': [{'AttributeName': 'id', 'KeyType': 'HASH'}],
            'ProvisionedThroughput': {
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        }

    def get_client(self):
        return dynamodb.Client(endpoint=self.endpoint)

    @staticmethod
    def _table_is_ready(response):
        LOGGER.debug('Is table ready? %r', response)
        if response['TableStatus'] != dynamodb.TABLE_ACTIVE:
            return False
        for index in response.get('GlobalSecondaryIndexes', {}):
            if index['IndexStatus'] != dynamodb.TABLE_ACTIVE:
                return False
        return True


class AsyncItemTestCase(AsyncTestCase):

    def setUp(self):
        self.definition = self.generic_table_definition()
        return super(AsyncItemTestCase, self).setUp()

    def tearDown(self):
        yield self.client.delete_table(self.definition['TableName'])
        super(AsyncItemTestCase, self).tearDown()

    def new_item_value(self):
        return {
            'id': str(uuid.uuid4()),
            'created_at': datetime.datetime.utcnow(),
            'value': str(uuid.uuid4())
        }

    def create_table(self, definition=None):
        return super(AsyncItemTestCase, self).create_table(
            definition or self.definition)

    def delete_item(self, item_id):
        return self.client.delete_item(self.definition['TableName'],
                                       {'id': item_id},
                                       return_consumed_capacity='TOTAL',
                                       return_item_collection_metrics='SIZE',
                                       return_values='ALL_OLD')

    def get_item(self, item_id):
        return self.client.get_item(self.definition['TableName'],
                                    {'id': item_id})

    def put_item(self, item):
        return self.client.put_item(self.definition['TableName'], item,
                                    return_consumed_capacity='TOTAL',
                                    return_item_collection_metrics='SIZE',
                                    return_values='ALL_OLD')


class AWSClientTests(AsyncTestCase):

    @testing.gen_test
    def create_table_expecting_raise(self, exception, future_exception=None):
        with mock.patch('tornado_aws.client.AsyncAWSClient.fetch') as fetch:
            future = concurrent.Future()
            future.set_exception(future_exception or exception)
            fetch.return_value = future
            with self.assertRaises(exception):
                yield self.client.create_table(self.generic_table_definition())

    def test_raises_config_not_found_exception(self):
        self.create_table_expecting_raise(
            dynamodb.ConfigNotFound,
            aws_exceptions.ConfigNotFound(path='/test'))

    def test_raises_config_parser_error(self):
        self.create_table_expecting_raise(dynamodb.ConfigParserError,
                                          aws_exceptions.ConfigParserError(
                                              path='/test'))

    def test_raises_no_credentials_error(self):
        self.create_table_expecting_raise(dynamodb.NoCredentialsError,
                                          aws_exceptions.NoCredentialsError)

    def test_raises_no_profile_error(self):
        self.create_table_expecting_raise(
            dynamodb.NoProfileError,
            aws_exceptions.NoProfileError(profile='test-1', path='/test'))

    def test_raises_request_exception(self):
        self.create_table_expecting_raise(dynamodb.RequestException,
                                          httpclient.HTTPError(500, 'uh-oh'))

    def test_raises_timeout_exception(self):
        self.create_table_expecting_raise(dynamodb.TimeoutException,
                                          httpclient.HTTPError(599))

    def test_empty_fetch_response_raises_dynamodb_exception(self):
        self.create_table_expecting_raise(dynamodb.DynamoDBException)

    def test_gaierror_raises_request_exception(self):
        self.create_table_expecting_raise(dynamodb.RequestException,
                                          socket.gaierror)

    def test_oserror_raises_request_exception(self):
        self.create_table_expecting_raise(dynamodb.RequestException,
                                          OSError)

    @unittest.skipIf(sys.version_info.major < 3,
                     'ConnectionError is Python3 only')
    def test_connection_error_request_exception(self):
        self.create_table_expecting_raise(dynamodb.RequestException,
                                          ConnectionError)

    @unittest.skipIf(sys.version_info.major < 3,
                     'ConnectionResetError is Python3 only')
    def test_connection_reset_error_request_exception(self):
        self.create_table_expecting_raise(dynamodb.RequestException,
                                          ConnectionResetError)

    @unittest.skipIf(sys.version_info.major < 3,
                     'TimeoutError is Python3 only')
    def test_connection_timeout_error_request_exception(self):
        self.create_table_expecting_raise(dynamodb.RequestException,
                                          TimeoutError)

    def test_tornado_aws_request_exception(self):
        self.create_table_expecting_raise(dynamodb.RequestException,
                                          aws_exceptions.RequestException(error=OSError))

    @testing.gen_test
    def test_retriable_exception_has_max_retries_measurements(self):
        definition = self.generic_table_definition()

        wait_for_measurements = locks.Event()

        def instrumentation_check(measurements):
            for attempt, measurement in enumerate(measurements):
                self.assertEqual(measurement.attempt, attempt + 1)
                self.assertEqual(measurement.action, 'CreateTable')
                self.assertEqual(measurement.table, definition['TableName'])
                self.assertEqual(measurement.error, 'RequestException')
            self.assertEqual(len(measurements), 3)
            wait_for_measurements.set()

        self.client.set_instrumentation_callback(instrumentation_check)
        with mock.patch('tornado_aws.client.AsyncAWSClient.fetch') as fetch:
            future = concurrent.Future()
            fetch.return_value = future
            future.set_exception(dynamodb.RequestException())
            with self.assertRaises(dynamodb.RequestException):
                yield self.client.create_table(definition)

        yield wait_for_measurements.wait()

    @testing.gen_test
    def test_internal_server_exception_has_max_retries_measurements(self):
        definition = self.generic_table_definition()

        wait_for_measurements = locks.Event()

        def instrumentation_check(measurements):
            for attempt, measurement in enumerate(measurements):
                self.assertEqual(measurement.error, 'InternalServerError')
            self.assertEqual(len(measurements), 3)
            wait_for_measurements.set()

        self.client.set_instrumentation_callback(instrumentation_check)
        with mock.patch('tornado_aws.client.AsyncAWSClient.fetch') as fetch:
            future = concurrent.Future()
            fetch.return_value = future
            future.set_exception(dynamodb.InternalServerError())
            with self.assertRaises(dynamodb.InternalServerError):
                yield self.client.create_table(definition)

        yield wait_for_measurements.wait()


class CreateTableTests(AsyncTestCase):

    @testing.gen_test
    def test_simple_table(self):
        definition = self.generic_table_definition()
        response = yield self.client.create_table(definition)
        self.assertEqual(response['TableName'], definition['TableName'])
        self.assertIn(response['TableStatus'],
                      [dynamodb.TABLE_ACTIVE,
                       dynamodb.TABLE_CREATING])

    @testing.gen_test
    def test_simple_table_measurements(self):
        definition = self.generic_table_definition()

        wait_for_measurements = locks.Event()

        def instrumentation_check(measurements):
            for attempt, measurement in enumerate(measurements):
                self.assertEqual(measurement.attempt, attempt + 1)
                self.assertEqual(measurement.action, 'CreateTable')
                self.assertEqual(measurement.table, definition['TableName'])
                self.assertEqual(measurement.error, None)
            self.assertEqual(len(measurements), 1)
            wait_for_measurements.set()

        self.client.set_instrumentation_callback(instrumentation_check)
        response = yield self.client.create_table(definition)
        self.assertEqual(response['TableName'], definition['TableName'])
        yield wait_for_measurements.wait()

    @testing.gen_test
    def test_invalid_request(self):
        definition = {
            'TableName': str(uuid.uuid4()),
            'AttributeDefinitions': [{'AttributeName': 'id'}],
            'KeySchema': [],
            'ProvisionedThroughput': {
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        }
        with self.assertRaises(dynamodb.ValidationException):
            yield self.client.create_table(definition)

    @testing.gen_test
    def test_double_create(self):
        definition = self.generic_table_definition()
        yield self.create_table(definition)
        with self.assertRaises(dynamodb.ResourceInUse):
            yield self.create_table(definition)
        yield self.client.delete_table(definition['TableName'])


class DeleteTableTests(AsyncTestCase):

    @testing.gen_test
    def test_delete_table(self):
        definition = self.generic_table_definition()
        yield self.create_table(definition)
        yield self.client.delete_table(definition['TableName'])
        with self.assertRaises(dynamodb.ResourceNotFound):
            yield self.client.describe_table(definition['TableName'])

    @testing.gen_test
    def test_table_not_found(self):
        table = str(uuid.uuid4())
        with self.assertRaises(dynamodb.ResourceNotFound):
            yield self.client.delete_table(table)


class DescribeTableTests(AsyncTestCase):

    @testing.gen_test
    def test_describe_table(self):
        # Create the table first
        definition = self.generic_table_definition()
        response = yield self.client.create_table(definition)
        self.assertEqual(response['TableName'], definition['TableName'])

        # Describe the table
        response = yield self.client.describe_table(definition['TableName'])
        self.assertEqual(response['TableName'], definition['TableName'])
        self.assertEqual(response['TableStatus'],
                         dynamodb.TABLE_ACTIVE)
        # Delete the table
        yield self.client.delete_table(definition['TableName'])

    @testing.gen_test
    def test_table_not_found(self):
        table = str(uuid.uuid4())
        with self.assertRaises(dynamodb.ResourceNotFound):
            yield self.client.describe_table(table)


class ListTableTests(AsyncTestCase):

    @testing.gen_test
    def test_list_tables(self):
        definition = self.generic_table_definition()
        response = yield self.client.create_table(definition)
        self.assertEqual(response['TableName'], definition['TableName'])

        response = yield self.client.list_tables(limit=100)
        self.assertIn(definition['TableName'], response['TableNames'])

        yield self.client.delete_table(definition['TableName'])

        response = yield self.client.list_tables(limit=100)
        self.assertNotIn(definition['TableName'], response['TableNames'])


class ItemLifecycleTests(AsyncItemTestCase):

    @testing.gen_test
    def test_item_lifecycle(self):
        yield self.create_table()

        item = self.new_item_value()

        response = yield self.put_item(item)
        self.assertIsNone(response)

        response = yield self.get_item(item['id'])
        self.assertEqual(response['Item']['id'], item['id'])

        item['update_check'] = str(uuid.uuid4())

        response = yield self.put_item(item)
        self.assertEqual(response['Attributes']['id'], item['id'])

        response = yield self.get_item(item['id'])
        self.assertEqual(response['Item']['id'], item['id'])
        self.assertEqual(response['Item']['update_check'],
                         item['update_check'])

        update_check = str(uuid.uuid4())

        response = yield self.client.update_item(
            self.definition['TableName'], {'id': item['id']},
            condition_expression='#update_check = :old_value',
            update_expression='SET #update_check = :update_check',
            expression_attribute_names={'#update_check': 'update_check'},
            expression_attribute_values={
                ':old_value': item['update_check'],
                ':update_check': update_check
            },
            return_consumed_capacity='TOTAL',
            return_item_collection_metrics='SIZE',
            return_values='ALL_OLD')
        self.assertEqual(response['Attributes']['id'], item['id'])
        self.assertEqual(response['Attributes']['update_check'],
                         item['update_check'])

        response = yield self.delete_item(item['id'])
        self.assertEqual(response['Attributes']['id'], item['id'])
        self.assertEqual(response['Attributes']['update_check'], update_check)

        response = yield self.get_item(item['id'])
        self.assertIsNone(response)


class TableQueryTests(AsyncItemTestCase):

    def setUp(self):
        super(TableQueryTests, self).setUp()
        self.common_counts = collections.Counter()
        self.common_keys = []
        for iteration in range(0, 5):
            self.common_keys.append(str(uuid.uuid4()))

    def new_item_value(self):
        offset = random.randint(0, len(self.common_keys) - 1)
        common_key = self.common_keys[offset]
        self.common_counts[common_key] += 1
        return {
            'id': str(uuid.uuid4()),
            'created_at': datetime.datetime.utcnow(),
            'value': str(uuid.uuid4()),
            'common': common_key
        }

    @staticmethod
    def generic_table_definition():
        return {
            'TableName': str(uuid.uuid4()),
            'AttributeDefinitions': [{'AttributeName': 'id',
                                      'AttributeType': 'S'},
                                     {'AttributeName': 'common',
                                      'AttributeType': 'S'}],
            'KeySchema': [{'AttributeName': 'id', 'KeyType': 'HASH'}],
            'ProvisionedThroughput': {
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            },
            'GlobalSecondaryIndexes': [
                {
                    'IndexName': 'common',
                    'KeySchema': [
                        {'AttributeName': 'common', 'KeyType': 'HASH'}
                    ],
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 1,
                        'WriteCapacityUnits': 1
                    },
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ]
        }

    @testing.gen_test()
    def test_query_on_common_key(self):
        yield self.create_table()
        for iteration in range(0, 10):
            payload = {
                'RequestItems': {
                    self.definition['TableName']: [{
                         'PutRequest': {
                             'Item': utils.marshall(self.new_item_value())
                         }
                     } for _row in range(0, 25)]
                },
                'ReturnConsumedCapacity': 'TOTAL',
                'ReturnItemCollectionMetrics': 'SIZE'
            }
            yield self.client.execute('BatchWriteItem', payload)

        for key in self.common_keys:
            items = []
            kwargs = {
                'index_name': 'common',
                'key_condition_expression': '#common = :common',
                'expression_attribute_names': {'#common': 'common'},
                'expression_attribute_values': {':common': key},
                'limit': 5
            }
            while True:
                result = yield self.client.query(self.definition['TableName'],
                                                 **kwargs)
                items += result['Items']
                if not result.get('LastEvaluatedKey'):
                    break
                kwargs['exclusive_start_key'] = result['LastEvaluatedKey']
            self.assertEqual(len(items), self.common_counts[key])


class TableScanTests(AsyncItemTestCase):

    @testing.gen_test()
    def test_query_on_common_key(self):
        yield self.create_table()
        for iteration in range(0, 10):
            payload = {
                'RequestItems': {
                    self.definition['TableName']: [{
                         'PutRequest': {
                             'Item': utils.marshall(self.new_item_value())
                         }
                     } for _row in range(0, 25)]
                },
                'ReturnConsumedCapacity': 'TOTAL',
                'ReturnItemCollectionMetrics': 'SIZE'
            }
            yield self.client.execute('BatchWriteItem', payload)

        items = []
        kwargs = {
            'limit': 5
        }
        while True:
            result = yield self.client.scan(self.definition['TableName'],
                                            **kwargs)
            items += result['Items']
            if not result.get('LastEvaluatedKey'):
                break
            kwargs['exclusive_start_key'] = result['LastEvaluatedKey']
        self.assertEqual(len(items), 250)
