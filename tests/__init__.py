# -*- coding: UTF-8 -*-
"""
    tests
    ~~~~~

    Testing Flask-Redis

    :copyright: (c) 2013 by netzinformatik UG.
    :author: Tobias Werner <mail@tobiaswerner.net>
    :license: BSD, see LICENSE for more details.
"""
import unittest
import mock

import flask

import flask_redis


def create_app(config=dict()):
    app = flask.Flask(__name__)
    app.debug = True
    app.config['SECRET_KEY'] = 'secret'
    app.config['TESTING'] = True

    for key, value in config.items():
        app.config[key] = value

    return app


class RedisTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app(dict(REDIS_HOST='127.0.0.1', REDIS_DB=5))
        self.redis = flask_redis.Redis(self.app)

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
