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


class FlaskRedisTestCase(unittest.TestCase):
    __config = dict(REDIS_HOST='127.0.0.1', REDIS_DB=5)

    def setUp(self):
        self.app = create_app(self.__config)
        self.redis = flask_redis.Redis(self.app)
        self._setUp()

    def _setUp(self):
        pass
