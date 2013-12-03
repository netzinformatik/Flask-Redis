# -*- coding: UTF-8 -*-
"""
    tests.session_test
    ~~~~~~~~~~~~~~~~~~

    Testing sessions

    :copyright: (c) 2013 by netzinformatik UG.
    :author: Tobias Werner <mail@tobiaswerner.net>
    :license: BSD, see LICENSE for more details.
"""
import mock
import cPickle
from flask_redis.session import RedisSession, RedisSessionInterface
from tests import FlaskRedisTestCase


class RedisSessionTest(FlaskRedisTestCase):
    def _setUp(self):
        initial = dict(a='test1', b='test2')
        self.session_object = RedisSession(sid='test123', initial=initial)

    def test_init(self):
        self.assertIsNotNone(self.session_object)
        self.assertFalse(self.session_object.new)

    def test_modify(self):
        self.assertFalse(self.session_object.modified)
        self.session_object['foo'] = 'foo'
        self.assertTrue(self.session_object.modified)

    def test_initial_data(self):
        self.assertEqual('test1', self.session_object.get('a'))
        self.assertEqual('test2', self.session_object['b'])

    def test_set_data(self):
        self.assertNotIn('data', self.session_object)
        test_data = u'test_data'
        self.session_object['data'] = test_data
        self.assertIn('data', self.session_object)
        self.assertEqual(test_data, self.session_object.get('data'))


class RedisSessionInterfaceTest(FlaskRedisTestCase):
    def _setUp(self):
        session_object = mock.Mock(name='redis_session')
        self.session_interface = RedisSessionInterface(redis=session_object)
        self.session_object = session_object

    def test_generate_sid(self):
        sid = RedisSessionInterface.generate_sid()
        self.assertIsInstance(sid, str)
        self.assertTrue(not len(sid) < 16)
        self.assertNotEqual(sid, self.session_interface.generate_sid())

    def test_open_new_session(self):
        request = mock.Mock(name='request')
        cookies_get = mock.Mock(name='cookies.get', return_value=None)
        request.cookies.get = cookies_get

        generate_sid = mock.Mock(name='generate_sid', return_value='new__sid')
        self.session_interface.generate_sid = generate_sid

        session = self.session_interface.open_session(self.app, request)

        self.assertIsInstance(session, RedisSession)
        self.assertEqual('new__sid', session.sid)
        self.assertTrue(session.new)

    def test_open_session_with_spoofed_sid(self):
        request = mock.Mock(name='request')
        cookies_get = mock.Mock(name='cookies.get', return_value='spoofed_sid')
        request.cookies.get = cookies_get

        redis_exists = mock.Mock(name='redis.exists', return_value=False)
        self.session_object.exists = redis_exists

        generate_sid = mock.Mock(name='generate_sid',
                                 return_value='secure__sid')
        self.session_interface.generate_sid = generate_sid

        session = self.session_interface.open_session(self.app, request)

        redis_exists.assert_called_with('session:spoofed_sid:data')
        self.assertIsInstance(session, RedisSession)
        self.assertEqual('secure__sid', session.sid)

    def test_open_existing_session(self):
        request = mock.Mock(name='request')
        cookies_get = mock.Mock(name='cookies.get', return_value='known_sid')
        request.cookies.get = cookies_get

        redis_exists = mock.Mock(name='redis.exists', return_value=True)
        self.session_object.exists = redis_exists

        rv = cPickle.dumps(dict(a='test_A', b='test_B'))
        redis_get = mock.Mock(name='redis.get', return_value=rv)
        self.session_object.get = redis_get

        session = self.session_interface.open_session(self.app, request)

        cookies_get.assert_called_with(self.app.session_cookie_name)
        redis_exists.assert_called_with('session:known_sid:data')
        redis_get.assert_called_with('session:known_sid:data')

        self.assertIn('a', session)
        self.assertEqual('test_A', session['a'])
        self.assertIn('b', session)
        self.assertEqual('test_B', session['b'])
