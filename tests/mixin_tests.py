import os
import unittest

from tornado import web

from sprockets_dynamodb import exceptions, mixin


class NoCredentials429TestCase(unittest.TestCase):

    def tearDown(self):
        if 'DYANMODB_NO_CREDS_RATE_LIMIT' in os.environ:
            del os.environ['DYANMODB_NO_CREDS_RATE_LIMIT']


    def test_env_var_true(self):
        for value in {'true', 'True', 'TRUE'}:
            os.environ['DYANMODB_NO_CREDS_RATE_LIMIT'] = value
            self.assertTrue(mixin._no_creds_should_return_429())

    def test_env_var_false(self):
        for value in {'false', 'False', 'FALSE'}:
            os.environ['DYANMODB_NO_CREDS_RATE_LIMIT'] = value
            self.assertFalse(mixin._no_creds_should_return_429())

    def test_unset_env_var_false(self):
        self.assertFalse(mixin._no_creds_should_return_429())


class MixinExceptionTestCase(unittest.TestCase):

    def setUp(self):
        self.mixin = mixin.DynamoDBMixin()

    def tearDown(self):
        if 'DYANMODB_NO_CREDS_RATE_LIMIT' in os.environ:
            del os.environ['DYANMODB_NO_CREDS_RATE_LIMIT']

    def test_condition_check_exception_raises(self):
        error = exceptions.ConditionalCheckFailedException()
        try:
            self.mixin._on_dynamodb_exception(error)
        except web.HTTPError as error:
            self.assertEqual(error.status_code, 409)

    def test_no_credentials_error_raises(self):
        error = exceptions.NoCredentialsError()
        try:
            self.mixin._on_dynamodb_exception(error)
        except web.HTTPError as error:
            self.assertEqual(error.status_code, 500)

    def test_no_credentials_error_retry_raises_429(self):
        os.environ['DYANMODB_NO_CREDS_RATE_LIMIT'] = 'true'
        error = exceptions.NoCredentialsError()
        try:
            self.mixin._on_dynamodb_exception(error)
        except web.HTTPError as error:
            self.assertEqual(error.status_code, 429)
