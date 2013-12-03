# -*- coding: UTF-8 -*-
"""
    tests.redis_test
    ~~~~~

    Testing Flask-Redis

    :copyright: (c) 2013 by netzinformatik UG.
    :author: Tobias Werner <mail@tobiaswerner.net>
    :license: BSD, see LICENSE for more details.
"""
import mock

from tests import FlaskRedisTestCase


class RedisTestCase(FlaskRedisTestCase):

    def test_app(self):
        self.assertIsNotNone(self.app)

    def test_redis_connection(self):
        self.assertIsNotNone(self.redis)

    def test_redis_set(self):
        with mock.patch('redis.StrictRedis.set', return_value=True) as r_set:
            with self.app.test_request_context():
                rv = self.redis.set('foo', 'bar')

            r_set.assert_called_with('foo', 'bar')
            self.assertTrue(rv)

    def test_redis_get(self):
        with mock.patch('redis.StrictRedis.get', return_value='baz') as r_get:
            with self.app.test_request_context():
                rv = self.redis.get('foo')

            r_get.assert_called_with('foo')
            self.assertEqual('baz', rv)

    def test_redis_disconnect(self):
        with self.app.test_request_context():
            self.redis.echo('TEST')

            cp = mock.Mock(name='connection_pool')
            self.redis._connection.connection_pool = cp

            self.app.do_teardown_appcontext()
            cp.disconnect.assert_called_once_with()